"""OpenAI (via LangChain) stance classifier for FOMC monetary policy text.

Uses LangChain's ChatOpenAI with structured output (Pydantic schemas) to classify
text as hawkish/dovish across two dimensions: policy (rates) and balance sheet (QT/QE).
Falls back gracefully when API key is missing or calls fail.
"""

import logging
import os
import time

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from fomc_tracker import config as cfg
from fomc_tracker.stance_classifier import ClassificationResult

logger = logging.getLogger(__name__)

# ── Pydantic schemas for structured output ───────────────────────────────────


class KeyPhrase(BaseModel):
    phrase: str = Field(description="Exact phrase from text")
    direction: str = Field(description='"hawkish" or "dovish"')
    dimension: str = Field(description='"policy" or "balance_sheet"')
    quote: str = Field(description="1-2 sentence quote containing the phrase")


class StanceClassification(BaseModel):
    score: float = Field(description="-5.0 (very dovish) to +5.0 (very hawkish) overall")
    label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    confidence: float = Field(description="0.0 to 1.0")
    policy_score: float = Field(description="-5.0 to +5.0 (interest rate stance)")
    policy_label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    balance_sheet_score: float = Field(description="-5.0 to +5.0 (QT/QE stance)")
    balance_sheet_label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    key_phrases: list[KeyPhrase] = Field(
        description="Key phrases signaling hawkish or dovish stance with dimension"
    )


class BatchStanceClassification(BaseModel):
    score: float = Field(description="-5.0 (very dovish) to +5.0 (very hawkish) overall")
    label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    confidence: float = Field(description="0.0 to 1.0")
    policy_score: float = Field(description="-5.0 to +5.0 (interest rate stance)")
    policy_label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    balance_sheet_score: float = Field(description="-5.0 to +5.0 (QT/QE stance)")
    balance_sheet_label: str = Field(description='"Hawkish", "Dovish", or "Neutral"')
    hawkish_phrases: list[str] = Field(description="Hawkish phrases found across snippets")
    dovish_phrases: list[str] = Field(description="Dovish phrases found across snippets")


# ── Prompts ──────────────────────────────────────────────────────────────────

SINGLE_TEXT_PROMPT = """\
You are a Federal Reserve monetary policy analyst. Classify the following text \
about an FOMC participant's stance on monetary policy across TWO dimensions:

1. **Policy stance (interest rates)**: Does the participant favor raising, holding, \
or cutting interest rates?
2. **Balance sheet stance (QT/QE)**: Does the participant favor shrinking the balance \
sheet (quantitative tightening), maintaining it, or expanding it (quantitative easing / \
slowing runoff)?

Scoring scale (for each dimension and overall):
- -5.0 = very dovish (rates: strongly favors cuts / BS: strongly favors expanding or slowing QT)
- 0.0 = neutral (balanced view, no clear lean)
- +5.0 = very hawkish (rates: strongly favors hikes / BS: strongly favors shrinking or continuing QT)

Label thresholds (apply to each dimension independently):
- "Dovish" if score < {dovish_threshold}
- "Neutral" if {dovish_threshold} <= score <= {hawkish_threshold}
- "Hawkish" if score > {hawkish_threshold}

The overall score should be a weighted combination: {policy_pct}% policy + {bs_pct}% balance sheet. \
If there is no balance sheet signal, set balance_sheet_score to 0.0 (Neutral).

Extract key phrases from the text that signal hawkish or dovish stance. For each \
key phrase, provide the exact phrase, its direction ("hawkish" or "dovish"), its \
dimension ("policy" or "balance_sheet"), and a 1-2 sentence quote from the text \
containing that phrase.

Set confidence based on how clearly the text signals a monetary policy stance \
(0.0 = no policy signal, 1.0 = very clear stance).

TEXT:
{text}"""

BATCH_PROMPT = """\
You are a Federal Reserve monetary policy analyst. Below are multiple news \
snippets about a single FOMC participant. Classify their OVERALL monetary \
policy stance based on all the evidence across TWO dimensions:

1. **Policy stance (interest rates)**: Does the participant favor raising, holding, \
or cutting interest rates?
2. **Balance sheet stance (QT/QE)**: Does the participant favor shrinking the balance \
sheet (quantitative tightening), maintaining it, or expanding it (quantitative easing / \
slowing runoff)?

Scoring scale (for each dimension and overall):
- -5.0 = very dovish (rates: strongly favors cuts / BS: strongly favors expanding or slowing QT)
- 0.0 = neutral (balanced view, no clear lean)
- +5.0 = very hawkish (rates: strongly favors hikes / BS: strongly favors shrinking or continuing QT)

Label thresholds (apply to each dimension independently):
- "Dovish" if score < {dovish_threshold}
- "Neutral" if {dovish_threshold} <= score <= {hawkish_threshold}
- "Hawkish" if score > {hawkish_threshold}

The overall score should be a weighted combination: {policy_pct}% policy + {bs_pct}% balance sheet. \
If there is no balance sheet signal, set balance_sheet_score to 0.0 (Neutral).

List the most important hawkish and dovish phrases found across all snippets.

Set confidence based on how clearly the evidence signals a monetary policy stance \
(0.0 = no policy signal, 1.0 = very clear stance).

SNIPPETS:
{snippets}"""

def _prompt_kwargs() -> dict:
    """Threshold / weight values injected into LLM prompt templates."""
    pw = int(cfg.POLICY_VS_BS_WEIGHT * 100)
    return {
        "hawkish_threshold": cfg.HAWKISH_THRESHOLD,
        "dovish_threshold": cfg.DOVISH_THRESHOLD,
        "policy_pct": pw,
        "bs_pct": 100 - pw,
    }


# ── Constants ────────────────────────────────────────────────────────────────

MODEL = "gpt-4o-mini"
SINGLE_TEXT_MAX_CHARS = 8_000
BATCH_SNIPPET_MAX_CHARS = 2_000
BATCH_TOTAL_MAX_CHARS = 30_000
RATE_LIMIT_DELAY = 0.1  # seconds between API calls
MAX_RETRIES = 3

# ── Client ───────────────────────────────────────────────────────────────────

_llm_single = None
_llm_batch = None


def _get_llm_single() -> ChatOpenAI:
    """Get or create the ChatOpenAI instance for single-text classification."""
    global _llm_single
    if _llm_single is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _llm_single = ChatOpenAI(
            model=MODEL, temperature=0.1, api_key=api_key
        ).with_structured_output(StanceClassification)
    return _llm_single


def _get_llm_batch() -> ChatOpenAI:
    """Get or create the ChatOpenAI instance for batch classification."""
    global _llm_batch
    if _llm_batch is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _llm_batch = ChatOpenAI(
            model=MODEL, temperature=0.1, api_key=api_key
        ).with_structured_output(BatchStanceClassification)
    return _llm_batch


def _call_openai(llm, prompt: str):
    """Call OpenAI via LangChain with retries on rate limit errors."""
    last_err = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                backoff = 2**attempt
                logger.info(f"  OpenAI retry {attempt}/{MAX_RETRIES} after {backoff}s backoff")
                time.sleep(backoff)

            result = llm.invoke(prompt)
            time.sleep(RATE_LIMIT_DELAY)
            return result

        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "500" in err_str or "503" in err_str:
                continue
            raise

    raise last_err


def _clamp(val: float, lo: float = -5.0, hi: float = 5.0) -> float:
    return max(lo, min(hi, round(val, 3)))


# ── Adapter functions ────────────────────────────────────────────────────────


def classify_text_openai(text: str) -> ClassificationResult:
    """Classify a single text snippet using OpenAI."""
    truncated = text[:SINGLE_TEXT_MAX_CHARS]
    prompt = SINGLE_TEXT_PROMPT.format(text=truncated, **_prompt_kwargs())
    llm = _get_llm_single()
    result = _call_openai(llm, prompt)

    hawkish = [kp.phrase for kp in result.key_phrases if kp.direction == "hawkish"]
    dovish = [kp.phrase for kp in result.key_phrases if kp.direction == "dovish"]

    return ClassificationResult(
        score=_clamp(result.score),
        label=result.label,
        confidence=_clamp(result.confidence, 0.0, 1.0),
        hawkish_matches=hawkish,
        dovish_matches=dovish,
        snippet_count=1,
        policy_score=_clamp(result.policy_score),
        policy_label=result.policy_label,
        balance_sheet_score=_clamp(result.balance_sheet_score),
        balance_sheet_label=result.balance_sheet_label,
    )


def classify_text_with_evidence_openai(
    text: str,
) -> tuple[ClassificationResult, list[dict]]:
    """Classify a single text and return evidence with quotes from OpenAI."""
    truncated = text[:SINGLE_TEXT_MAX_CHARS]
    prompt = SINGLE_TEXT_PROMPT.format(text=truncated, **_prompt_kwargs())
    llm = _get_llm_single()
    result = _call_openai(llm, prompt)

    hawkish = [kp.phrase for kp in result.key_phrases if kp.direction == "hawkish"]
    dovish = [kp.phrase for kp in result.key_phrases if kp.direction == "dovish"]

    cls_result = ClassificationResult(
        score=_clamp(result.score),
        label=result.label,
        confidence=_clamp(result.confidence, 0.0, 1.0),
        hawkish_matches=hawkish,
        dovish_matches=dovish,
        snippet_count=1,
        policy_score=_clamp(result.policy_score),
        policy_label=result.policy_label,
        balance_sheet_score=_clamp(result.balance_sheet_score),
        balance_sheet_label=result.balance_sheet_label,
    )

    evidence = [
        {
            "keyword": kp.phrase,
            "direction": kp.direction,
            "dimension": kp.dimension,
            "quote": kp.quote,
        }
        for kp in result.key_phrases
    ]

    return cls_result, evidence


def classify_snippets_openai(snippets: list[str]) -> ClassificationResult:
    """Classify multiple text snippets using OpenAI batch prompt."""
    if not snippets:
        return ClassificationResult(
            score=0.0,
            label="Neutral",
            confidence=0.0,
            hawkish_matches=[],
            dovish_matches=[],
            snippet_count=0,
        )

    truncated = []
    total_chars = 0
    for s in snippets:
        chunk = s[:BATCH_SNIPPET_MAX_CHARS]
        if total_chars + len(chunk) > BATCH_TOTAL_MAX_CHARS:
            break
        truncated.append(chunk)
        total_chars += len(chunk)

    numbered = "\n\n".join(f"[{i + 1}] {s}" for i, s in enumerate(truncated))
    prompt = BATCH_PROMPT.format(snippets=numbered, **_prompt_kwargs())
    llm = _get_llm_batch()
    result = _call_openai(llm, prompt)

    return ClassificationResult(
        score=_clamp(result.score),
        label=result.label,
        confidence=_clamp(result.confidence, 0.0, 1.0),
        hawkish_matches=result.hawkish_phrases,
        dovish_matches=result.dovish_phrases,
        snippet_count=len(snippets),
        policy_score=_clamp(result.policy_score),
        policy_label=result.policy_label,
        balance_sheet_score=_clamp(result.balance_sheet_score),
        balance_sheet_label=result.balance_sheet_label,
    )

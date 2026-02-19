"""Hawkish/dovish stance classifier with Gemini API and keyword fallback.

Scores text on a scale of -5.0 (very dovish) to +5.0 (very hawkish).
Supports two dimensions: policy (rates) and balance sheet (QT/QE).

When GEMINI_API_KEY is set, uses Gemini 2.0 Flash for semantic classification.
Falls back to keyword matching when the API key is missing or on API errors.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv

from fomc_tracker import config as cfg

load_dotenv()

logger = logging.getLogger(__name__)

# ── Policy keyword dictionaries (interest rates) ─────────────────────────────

POLICY_HAWKISH_TERMS: dict[str, float] = {
    "raise rates": 1.0,
    "rate hike": 1.0,
    "rate increase": 0.9,
    "tighten": 0.8,
    "tightening": 0.8,
    "restrictive": 0.7,
    "sufficiently restrictive": 0.8,
    "more restrictive": 0.9,
    "higher for longer": 0.9,
    "too high inflation": 0.8,
    "inflation persistent": 0.7,
    "inflation expectations unanchored": 0.9,
    "price stability": 0.5,
    "overheating": 0.7,
    "hot economy": 0.6,
    "strong labor market": 0.4,
    "wage pressures": 0.6,
    "wage growth": 0.4,
    "upside risks to inflation": 0.8,
    "not yet done": 0.6,
    "more work to do": 0.6,
    "premature": 0.7,
    "premature to cut": 0.9,
    "too soon to cut": 0.9,
    "patient": 0.4,
    "no rush": 0.5,
    "no hurry": 0.5,
    "cautious": 0.3,
    "vigilant": 0.5,
    "demand too strong": 0.6,
    "above target": 0.5,
    "sticky inflation": 0.7,
    "core inflation elevated": 0.7,
    "inflation not beaten": 0.7,
    "further tightening": 0.9,
    "additional rate increases": 0.9,
    "bumpy road": 0.4,
    "not convinced": 0.5,
}

POLICY_DOVISH_TERMS: dict[str, float] = {
    "cut rates": 1.0,
    "rate cut": 1.0,
    "rate reduction": 0.9,
    "lower rates": 0.8,
    "easing": 0.8,
    "ease policy": 0.9,
    "accommodative": 0.8,
    "more accommodative": 0.9,
    "support growth": 0.6,
    "support the economy": 0.6,
    "downside risks": 0.7,
    "recession risk": 0.8,
    "recession": 0.6,
    "slowdown": 0.6,
    "economic weakness": 0.7,
    "job losses": 0.7,
    "rising unemployment": 0.8,
    "unemployment": 0.4,
    "labor market softening": 0.7,
    "labor market cooling": 0.6,
    "inflation falling": 0.6,
    "inflation declining": 0.6,
    "disinflation": 0.7,
    "progress on inflation": 0.5,
    "inflation moving down": 0.6,
    "inflation heading toward target": 0.6,
    "maximum employment": 0.5,
    "full employment": 0.4,
    "below target": 0.5,
    "not restrictive enough": 0.3,
    "gradual": 0.3,
    "appropriate to reduce": 0.8,
    "time to cut": 0.9,
    "ready to cut": 0.9,
    "case for cutting": 0.8,
    "pause tightening": 0.6,
    "stop raising": 0.7,
    "overly restrictive": 0.8,
    "too restrictive": 0.8,
    "risks becoming too restrictive": 0.7,
    "balanced risks": 0.3,
    "soft landing": 0.5,
    "achieving soft landing": 0.5,
}

# ── Balance sheet keyword dictionaries (QT/QE) ───────────────────────────────

BS_HAWKISH_TERMS: dict[str, float] = {
    "quantitative tightening": 0.9,
    "reduce balance sheet": 0.9,
    "shrink balance sheet": 0.8,
    "reducing balance sheet": 0.7,
    "balance sheet runoff": 0.7,
    "reduce holdings": 0.7,
    "treasury runoff": 0.6,
    "mbs runoff": 0.6,
    "normalize balance sheet": 0.6,
    "balance sheet normalization": 0.6,
    "too large balance sheet": 0.7,
    "unwind": 0.5,
    "wind down": 0.5,
}

BS_DOVISH_TERMS: dict[str, float] = {
    "quantitative easing": 0.9,
    "expand balance sheet": 0.9,
    "asset purchases": 0.8,
    "slow runoff": 0.8,
    "taper runoff": 0.8,
    "pause runoff": 0.9,
    "slow the pace of runoff": 0.8,
    "reinvest": 0.7,
    "reinvestment": 0.7,
    "maintain balance sheet": 0.4,
    "end qt": 0.9,
    "stop qt": 0.9,
    "ample reserves": 0.5,
    "reserve scarcity": 0.6,
    "repo pressures": 0.5,
}

# Backward-compatible unified dictionaries (union of policy + BS terms)
HAWKISH_TERMS: dict[str, float] = {**POLICY_HAWKISH_TERMS, **BS_HAWKISH_TERMS}
DOVISH_TERMS: dict[str, float] = {**POLICY_DOVISH_TERMS, **BS_DOVISH_TERMS}


@dataclass
class ClassificationResult:
    score: float  # -5.0 to +5.0 (overall combined score)
    label: str  # "Hawkish", "Dovish", "Neutral"
    confidence: float  # 0.0 to 1.0
    hawkish_matches: list[str]
    dovish_matches: list[str]
    snippet_count: int
    # Dual-dimension scores
    policy_score: float = 0.0  # -5.0 to +5.0 (interest rate stance)
    policy_label: str = "Neutral"
    balance_sheet_score: float = 0.0  # -5.0 to +5.0 (QT/QE stance)
    balance_sheet_label: str = "Neutral"


# ── Classifier backend registry ───────────────────────────────────────────────

# Type aliases for the three classifier callables.
ClassifyTextFn = Callable[[str], ClassificationResult]
ClassifyTextWithEvidenceFn = Callable[[str], tuple[ClassificationResult, list[dict]]]
ClassifySnippetsFn = Callable[[list[str]], ClassificationResult]

# Registry: list of (name, classify_text, classify_text_with_evidence, classify_snippets, enabled).
_CLASSIFIERS: list[
    tuple[str, ClassifyTextFn, ClassifyTextWithEvidenceFn, ClassifySnippetsFn, bool]
] = []


def register_classifier(
    name: str,
    classify_text_fn: ClassifyTextFn,
    classify_text_with_evidence_fn: ClassifyTextWithEvidenceFn,
    classify_snippets_fn: ClassifySnippetsFn,
    *,
    enabled: bool = True,
) -> None:
    """Register a classifier backend.

    Args:
        name: Human-readable name (used in logs).
        classify_text_fn: (text) -> ClassificationResult
        classify_text_with_evidence_fn: (text) -> (ClassificationResult, evidence_list)
        classify_snippets_fn: (snippets) -> ClassificationResult
        enabled: Set False to register but skip during classification.

    Example::

        register_classifier(
            "my_llm",
            my_classify_text,
            my_classify_with_evidence,
            my_classify_snippets,
        )
    """
    _CLASSIFIERS.append((
        name,
        classify_text_fn,
        classify_text_with_evidence_fn,
        classify_snippets_fn,
        enabled,
    ))
    logger.debug(f"Registered classifier backend: {name} (enabled={enabled})")


def classifier_backend(name: str, *, enabled: bool = True):
    """Decorator to register a class as a classifier backend.

    The decorated class must have three static/class methods:
    ``classify_text``, ``classify_text_with_evidence``, ``classify_snippets``.

    Example::

        @classifier_backend("my_llm")
        class MyClassifier:
            @staticmethod
            def classify_text(text: str) -> ClassificationResult: ...

            @staticmethod
            def classify_text_with_evidence(text: str) -> tuple[ClassificationResult, list[dict]]: ...

            @staticmethod
            def classify_snippets(snippets: list[str]) -> ClassificationResult: ...
    """
    def decorator(cls):
        register_classifier(
            name,
            cls.classify_text,
            cls.classify_text_with_evidence,
            cls.classify_snippets,
            enabled=enabled,
        )
        return cls
    return decorator


def list_classifiers() -> list[tuple[str, bool]]:
    """Return registered classifier names and their enabled status."""
    return [(name, enabled) for name, _, _, _, enabled in _CLASSIFIERS]


def enable_classifier(name: str) -> None:
    """Enable a previously registered classifier by name."""
    for i, (n, ct, ce, cs, _) in enumerate(_CLASSIFIERS):
        if n == name:
            _CLASSIFIERS[i] = (n, ct, ce, cs, True)
            return
    raise KeyError(f"No classifier named '{name}'")


def disable_classifier(name: str) -> None:
    """Disable a registered classifier by name (keeps it in the registry)."""
    for i, (n, ct, ce, cs, _) in enumerate(_CLASSIFIERS):
        if n == name:
            _CLASSIFIERS[i] = (n, ct, ce, cs, False)
            return
    raise KeyError(f"No classifier named '{name}'")


def _score_label(score: float) -> str:
    """Convert a score to a label."""
    return cfg.score_label(score)


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _score_dimension(
    normalized: str, hawkish_terms: dict[str, float], dovish_terms: dict[str, float]
) -> tuple[float, float, list[str], list[str]]:
    """Score text against a pair of hawkish/dovish term dictionaries.

    Returns (raw_score, confidence, hawkish_matches, dovish_matches).
    """
    hawkish_score = 0.0
    dovish_score = 0.0
    hawkish_matches = []
    dovish_matches = []

    for term, weight in hawkish_terms.items():
        count = normalized.count(term.lower())
        if count > 0:
            hawkish_score += weight * count
            hawkish_matches.append(term)

    for term, weight in dovish_terms.items():
        count = normalized.count(term.lower())
        if count > 0:
            dovish_score += weight * count
            dovish_matches.append(term)

    total = hawkish_score + dovish_score
    if total == 0:
        return 0.0, 0.0, [], []

    raw_score = 5.0 * (hawkish_score - dovish_score) / total
    confidence = min(total / 5.0, 1.0)
    return raw_score, confidence, hawkish_matches, dovish_matches


def classify_text_keyword(text: str) -> ClassificationResult:
    """Classify a single text snippet as hawkish, dovish, or neutral (keyword-based)."""
    normalized = _normalize(text)

    # Score policy dimension
    policy_score, policy_conf, policy_hawk, policy_dove = _score_dimension(
        normalized, POLICY_HAWKISH_TERMS, POLICY_DOVISH_TERMS
    )

    # Score balance sheet dimension
    bs_score, bs_conf, bs_hawk, bs_dove = _score_dimension(
        normalized, BS_HAWKISH_TERMS, BS_DOVISH_TERMS
    )

    # Combined overall score: policy_vs_bs_weight policy + (1-weight) balance sheet
    # If no BS keywords found, overall = policy only
    if bs_conf == 0:
        overall_score = policy_score
    else:
        overall_score = cfg.POLICY_VS_BS_WEIGHT * policy_score + (1 - cfg.POLICY_VS_BS_WEIGHT) * bs_score

    # Combined confidence
    total_conf = policy_conf + bs_conf
    if total_conf == 0:
        return ClassificationResult(
            score=0.0,
            label="Neutral",
            confidence=0.0,
            hawkish_matches=[],
            dovish_matches=[],
            snippet_count=1,
        )

    overall_conf = min((policy_conf + bs_conf) / 2.0 if bs_conf > 0 else policy_conf, 1.0)

    all_hawkish = sorted(set(policy_hawk + bs_hawk))
    all_dovish = sorted(set(policy_dove + bs_dove))

    return ClassificationResult(
        score=round(overall_score, 3),
        label=_score_label(overall_score),
        confidence=round(overall_conf, 3),
        hawkish_matches=all_hawkish,
        dovish_matches=all_dovish,
        snippet_count=1,
        policy_score=round(policy_score, 3),
        policy_label=_score_label(policy_score),
        balance_sheet_score=round(bs_score, 3),
        balance_sheet_label=_score_label(bs_score),
    )


def extract_quote(text: str, term: str, context_chars: int | None = None) -> str:
    """Extract a short quote around a matched keyword in the original text."""
    if context_chars is None:
        context_chars = cfg.QUOTE_CONTEXT_CHARS
    idx = text.lower().find(term.lower())
    if idx == -1:
        return ""
    start = max(0, idx - context_chars // 2)
    end = min(len(text), idx + len(term) + context_chars // 2)
    # Snap to word boundaries
    if start > 0:
        space = text.rfind(" ", 0, start)
        if space != -1:
            start = space + 1
    if end < len(text):
        space = text.find(" ", end)
        if space != -1:
            end = space
    quote = text[start:end].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{quote}{suffix}"


def _keyword_dimension(term: str) -> str:
    """Determine which dimension a keyword belongs to: 'policy' or 'balance_sheet'."""
    term_lower = term.lower()
    if term_lower in {t.lower() for t in BS_HAWKISH_TERMS} or term_lower in {
        t.lower() for t in BS_DOVISH_TERMS
    }:
        return "balance_sheet"
    return "policy"


def classify_text_with_evidence_keyword(text: str) -> tuple[ClassificationResult, list[dict]]:
    """Classify text and return evidence snippets for matched keywords.

    Returns (ClassificationResult, evidence_list) where each evidence item is:
        {"keyword": str, "direction": "hawkish"|"dovish", "dimension": "policy"|"balance_sheet", "quote": str}
    """
    result = classify_text_keyword(text)
    evidence = []
    for kw in result.hawkish_matches:
        quote = extract_quote(text, kw)
        if quote:
            evidence.append({
                "keyword": kw,
                "direction": "hawkish",
                "dimension": _keyword_dimension(kw),
                "quote": quote,
            })
    for kw in result.dovish_matches:
        quote = extract_quote(text, kw)
        if quote:
            evidence.append({
                "keyword": kw,
                "direction": "dovish",
                "dimension": _keyword_dimension(kw),
                "quote": quote,
            })
    return result, evidence


def classify_snippets_keyword(snippets: list[str]) -> ClassificationResult:
    """Classify multiple text snippets and return an aggregate result (keyword-based)."""
    if not snippets:
        return ClassificationResult(
            score=0.0,
            label="Neutral",
            confidence=0.0,
            hawkish_matches=[],
            dovish_matches=[],
            snippet_count=0,
        )

    results = [classify_text_keyword(s) for s in snippets]

    # Weighted average by confidence for each dimension
    total_conf = sum(r.confidence for r in results)
    if total_conf == 0:
        avg_score = 0.0
        avg_policy = 0.0
        avg_bs = 0.0
    else:
        avg_score = sum(r.score * r.confidence for r in results) / total_conf
        avg_policy = sum(r.policy_score * r.confidence for r in results) / total_conf
        avg_bs = sum(r.balance_sheet_score * r.confidence for r in results) / total_conf

    all_hawkish = []
    all_dovish = []
    for r in results:
        all_hawkish.extend(r.hawkish_matches)
        all_dovish.extend(r.dovish_matches)

    # Deduplicate
    all_hawkish = sorted(set(all_hawkish))
    all_dovish = sorted(set(all_dovish))

    avg_conf = total_conf / len(results) if results else 0.0

    return ClassificationResult(
        score=round(avg_score, 3),
        label=_score_label(avg_score),
        confidence=round(min(avg_conf, 1.0), 3),
        hawkish_matches=all_hawkish,
        dovish_matches=all_dovish,
        snippet_count=len(snippets),
        policy_score=round(avg_policy, 3),
        policy_label=_score_label(avg_policy),
        balance_sheet_score=round(avg_bs, 3),
        balance_sheet_label=_score_label(avg_bs),
    )


# ── LLM / keyword routing ────────────────────────────────────────────────────
# Priority: Registered plugins → Cerebras → Gemini → OpenAI → keyword fallback


def _cerebras_available() -> bool:
    """Check if Cerebras API is configured."""
    return bool(os.environ.get("CEREBRAS_API_KEY"))


def _gemini_available() -> bool:
    """Check if Gemini API is configured."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def _openai_available() -> bool:
    """Check if OpenAI API is configured."""
    return bool(os.environ.get("OPENAI_API_KEY"))


def classify_text(text: str) -> ClassificationResult:
    """Classify text using registered plugins, then LLM, then keyword fallback."""
    for name, ct_fn, _, _, enabled in _CLASSIFIERS:
        if not enabled:
            continue
        try:
            return ct_fn(text)
        except Exception as e:
            logger.warning(f"Classifier plugin '{name}' failed: {e}")
    if _cerebras_available():
        try:
            from fomc_tracker.cerebras_classifier import classify_text_cerebras

            return classify_text_cerebras(text)
        except Exception as e:
            logger.warning(f"Cerebras failed: {e}")
    if _gemini_available():
        try:
            from fomc_tracker.gemini_classifier import classify_text_gemini

            return classify_text_gemini(text)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
    if _openai_available():
        try:
            from fomc_tracker.openai_classifier import classify_text_openai

            return classify_text_openai(text)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
    return classify_text_keyword(text)


def classify_text_with_evidence(text: str) -> tuple[ClassificationResult, list[dict]]:
    """Classify text with evidence using registered plugins, then LLM, then keyword fallback."""
    for name, _, ce_fn, _, enabled in _CLASSIFIERS:
        if not enabled:
            continue
        try:
            return ce_fn(text)
        except Exception as e:
            logger.warning(f"Classifier plugin '{name}' failed: {e}")
    if _cerebras_available():
        try:
            from fomc_tracker.cerebras_classifier import classify_text_with_evidence_cerebras

            return classify_text_with_evidence_cerebras(text)
        except Exception as e:
            logger.warning(f"Cerebras failed: {e}")
    if _gemini_available():
        try:
            from fomc_tracker.gemini_classifier import classify_text_with_evidence_gemini

            return classify_text_with_evidence_gemini(text)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
    if _openai_available():
        try:
            from fomc_tracker.openai_classifier import classify_text_with_evidence_openai

            return classify_text_with_evidence_openai(text)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
    return classify_text_with_evidence_keyword(text)


def classify_snippets(snippets: list[str]) -> ClassificationResult:
    """Classify snippets using registered plugins, then LLM, then keyword fallback."""
    for name, _, _, cs_fn, enabled in _CLASSIFIERS:
        if not enabled:
            continue
        try:
            return cs_fn(snippets)
        except Exception as e:
            logger.warning(f"Classifier plugin '{name}' failed: {e}")
    if _cerebras_available():
        try:
            from fomc_tracker.cerebras_classifier import classify_snippets_cerebras

            return classify_snippets_cerebras(snippets)
        except Exception as e:
            logger.warning(f"Cerebras failed: {e}")
    if _gemini_available():
        try:
            from fomc_tracker.gemini_classifier import classify_snippets_gemini

            return classify_snippets_gemini(snippets)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
    if _openai_available():
        try:
            from fomc_tracker.openai_classifier import classify_snippets_openai

            return classify_snippets_openai(snippets)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
    return classify_snippets_keyword(snippets)

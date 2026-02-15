"""Keyword-based hawkish/dovish stance classifier.

Scores text on a scale of -1.0 (very dovish) to +1.0 (very hawkish).
"""

import re
from dataclasses import dataclass

# ── Keyword dictionaries with weights ──────────────────────────────────────

HAWKISH_TERMS: dict[str, float] = {
    # Strong hawkish signals
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
    "reducing balance sheet": 0.4,
    "quantitative tightening": 0.5,
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

DOVISH_TERMS: dict[str, float] = {
    # Strong dovish signals
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


@dataclass
class ClassificationResult:
    score: float  # -1.0 to +1.0
    label: str  # "Hawkish", "Dovish", "Neutral"
    confidence: float  # 0.0 to 1.0
    hawkish_matches: list[str]
    dovish_matches: list[str]
    snippet_count: int


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def classify_text(text: str) -> ClassificationResult:
    """Classify a single text snippet as hawkish, dovish, or neutral."""
    normalized = _normalize(text)

    hawkish_score = 0.0
    dovish_score = 0.0
    hawkish_matches = []
    dovish_matches = []

    for term, weight in HAWKISH_TERMS.items():
        count = normalized.count(term.lower())
        if count > 0:
            hawkish_score += weight * count
            hawkish_matches.append(term)

    for term, weight in DOVISH_TERMS.items():
        count = normalized.count(term.lower())
        if count > 0:
            dovish_score += weight * count
            dovish_matches.append(term)

    total = hawkish_score + dovish_score
    if total == 0:
        return ClassificationResult(
            score=0.0,
            label="Neutral",
            confidence=0.0,
            hawkish_matches=[],
            dovish_matches=[],
            snippet_count=1,
        )

    # Net score: positive = hawkish, negative = dovish
    raw_score = (hawkish_score - dovish_score) / total
    confidence = min(total / 5.0, 1.0)  # Scales up to 5 keyword hits

    label = "Neutral"
    if raw_score > 0.3:
        label = "Hawkish"
    elif raw_score < -0.3:
        label = "Dovish"

    return ClassificationResult(
        score=round(raw_score, 3),
        label=label,
        confidence=round(confidence, 3),
        hawkish_matches=hawkish_matches,
        dovish_matches=dovish_matches,
        snippet_count=1,
    )


def classify_snippets(snippets: list[str]) -> ClassificationResult:
    """Classify multiple text snippets and return an aggregate result."""
    if not snippets:
        return ClassificationResult(
            score=0.0,
            label="Neutral",
            confidence=0.0,
            hawkish_matches=[],
            dovish_matches=[],
            snippet_count=0,
        )

    results = [classify_text(s) for s in snippets]

    # Weighted average by confidence
    total_conf = sum(r.confidence for r in results)
    if total_conf == 0:
        avg_score = 0.0
    else:
        avg_score = sum(r.score * r.confidence for r in results) / total_conf

    all_hawkish = []
    all_dovish = []
    for r in results:
        all_hawkish.extend(r.hawkish_matches)
        all_dovish.extend(r.dovish_matches)

    # Deduplicate
    all_hawkish = sorted(set(all_hawkish))
    all_dovish = sorted(set(all_dovish))

    avg_conf = total_conf / len(results) if results else 0.0

    label = "Neutral"
    if avg_score > 0.3:
        label = "Hawkish"
    elif avg_score < -0.3:
        label = "Dovish"

    return ClassificationResult(
        score=round(avg_score, 3),
        label=label,
        confidence=round(min(avg_conf, 1.0), 3),
        hawkish_matches=all_hawkish,
        dovish_matches=all_dovish,
        snippet_count=len(snippets),
    )

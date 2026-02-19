"""Example custom classifier backend (LangChain + OpenAI).

Copy this file to ``local/classifier.py`` and uncomment the code below.
The ``@classifier_backend`` decorator automatically registers the class so it
takes priority over the built-in Cerebras/Gemini/OpenAI/keyword chain.

Requirements (add to your local environment)::

    pip install langchain-openai

Set the ``OPENAI_API_KEY`` environment variable before running ``fetch_data.py``.
"""

# from fomc_tracker import config as cfg
# from fomc_tracker.stance_classifier import ClassificationResult, classifier_backend
#
#
# # ── Lazy singleton ────────────────────────────────────────────────────────────
#
# _llm = None
#
#
# def _get_llm():
#     global _llm
#     if _llm is None:
#         from langchain_openai import ChatOpenAI
#
#         _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
#     return _llm
#
#
# # ── Prompt template ───────────────────────────────────────────────────────────
#
# _SYSTEM_PROMPT = f"""\
# You are a Federal Reserve policy analyst. Classify the monetary policy stance
# of the text on two dimensions:
#
# 1. **Policy (interest rates)**: score from -5.0 (very dovish) to +5.0 (very hawkish)
# 2. **Balance sheet (QT/QE)**: score from -5.0 (very dovish) to +5.0 (very hawkish)
#
# Labels: "Dovish" (< {cfg.DOVISH_THRESHOLD}), "Neutral" ({cfg.DOVISH_THRESHOLD} to \
# {cfg.HAWKISH_THRESHOLD}), "Hawkish" (> {cfg.HAWKISH_THRESHOLD}).
#
# Overall score = {cfg.POLICY_VS_BS_WEIGHT} * policy + \
# {round(1 - cfg.POLICY_VS_BS_WEIGHT, 2)} * balance_sheet (if balance sheet signals exist).
#
# Respond with ONLY valid JSON (no markdown fences):
# {{
#   "policy_score": <float>,
#   "balance_sheet_score": <float>,
#   "confidence": <float 0-1>,
#   "hawkish_signals": ["<phrase>", ...],
#   "dovish_signals": ["<phrase>", ...]
# }}
# """
#
#
# def _parse_response(raw: str, snippet_count: int = 1) -> ClassificationResult:
#     """Parse LLM JSON response into a ClassificationResult."""
#     import json
#
#     data = json.loads(raw)
#     ps = float(data["policy_score"])
#     bs = float(data["balance_sheet_score"])
#     conf = float(data["confidence"])
#     hawk = data.get("hawkish_signals", [])
#     dove = data.get("dovish_signals", [])
#
#     if bs == 0.0 and not any(s for s in hawk + dove if "balance" in s.lower() or "qt" in s.lower()):
#         overall = ps
#     else:
#         overall = cfg.POLICY_VS_BS_WEIGHT * ps + (1 - cfg.POLICY_VS_BS_WEIGHT) * bs
#
#     return ClassificationResult(
#         score=round(overall, 3),
#         label=cfg.score_label(overall),
#         confidence=round(min(conf, 1.0), 3),
#         hawkish_matches=hawk,
#         dovish_matches=dove,
#         snippet_count=snippet_count,
#         policy_score=round(ps, 3),
#         policy_label=cfg.score_label(ps),
#         balance_sheet_score=round(bs, 3),
#         balance_sheet_label=cfg.score_label(bs),
#     )
#
#
# @classifier_backend("langchain_openai")
# class LangChainOpenAIClassifier:
#     """LangChain + OpenAI classifier backend."""
#
#     @staticmethod
#     def classify_text(text: str) -> ClassificationResult:
#         llm = _get_llm()
#         resp = llm.invoke([
#             {"role": "system", "content": _SYSTEM_PROMPT},
#             {"role": "user", "content": text[:4000]},
#         ])
#         return _parse_response(resp.content)
#
#     @staticmethod
#     def classify_text_with_evidence(text: str) -> tuple[ClassificationResult, list[dict]]:
#         result = LangChainOpenAIClassifier.classify_text(text)
#         evidence = []
#         for kw in result.hawkish_matches:
#             evidence.append({
#                 "keyword": kw,
#                 "direction": "hawkish",
#                 "dimension": "policy",
#                 "quote": kw,
#             })
#         for kw in result.dovish_matches:
#             evidence.append({
#                 "keyword": kw,
#                 "direction": "dovish",
#                 "dimension": "policy",
#                 "quote": kw,
#             })
#         return result, evidence
#
#     @staticmethod
#     def classify_snippets(snippets: list[str]) -> ClassificationResult:
#         combined = "\n\n---\n\n".join(snippets[:20])
#         result = LangChainOpenAIClassifier.classify_text(combined)
#         return ClassificationResult(
#             score=result.score,
#             label=result.label,
#             confidence=result.confidence,
#             hawkish_matches=result.hawkish_matches,
#             dovish_matches=result.dovish_matches,
#             snippet_count=len(snippets),
#             policy_score=result.policy_score,
#             policy_label=result.policy_label,
#             balance_sheet_score=result.balance_sheet_score,
#             balance_sheet_label=result.balance_sheet_label,
#         )

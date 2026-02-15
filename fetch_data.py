#!/usr/bin/env python3
"""CLI orchestrator: fetch news, classify stances, store history."""

import argparse
import logging
import sys

from fomc_tracker.historical_data import add_stance, load_history
from fomc_tracker.news_fetcher import fetch_news_for_participant, load_cached_news
from fomc_tracker.participants import PARTICIPANTS, get_participant
from fomc_tracker.stance_classifier import classify_snippets, classify_text_with_evidence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _score_label(score: float) -> str:
    if score > 1.5:
        return "Hawkish"
    elif score < -1.5:
        return "Dovish"
    return "Neutral"


def process_participant(participant, use_cache=True):
    """Fetch news, classify stance, and store for one participant."""
    logger.info(f"Processing: {participant.name} ({participant.institution})")

    # Check cache first
    results = None
    if use_cache:
        results = load_cached_news(participant)
        if results is not None:
            logger.info(f"  Using cached data ({len(results)} items)")

    # Fetch fresh if no cache
    if results is None:
        results = fetch_news_for_participant(participant)

    if not results:
        logger.warning(f"  No news found for {participant.name}, using historical lean")
        policy_score = participant.historical_lean
        bs_score = participant.historical_balance_sheet_lean
        overall_score = 0.7 * policy_score + 0.3 * bs_score
        overall_score = max(-5.0, min(5.0, overall_score))
        label = _score_label(overall_score)
        add_stance(
            participant.name, overall_score, label, source="historical_lean",
            policy_score=policy_score, policy_label=_score_label(policy_score),
            balance_sheet_score=bs_score, balance_sheet_label=_score_label(bs_score),
        )
        return overall_score, label

    # Extract text snippets for classification
    snippets = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('body', '')}".strip()
        if text:
            snippets.append(text)

    if not snippets:
        logger.warning(f"  No text content for {participant.name}")
        policy_score = participant.historical_lean
        bs_score = participant.historical_balance_sheet_lean
        overall_score = 0.7 * policy_score + 0.3 * bs_score
        overall_score = max(-5.0, min(5.0, overall_score))
        label = _score_label(overall_score)
        add_stance(
            participant.name, overall_score, label, source="historical_lean",
            policy_score=policy_score, policy_label=_score_label(policy_score),
            balance_sheet_score=bs_score, balance_sheet_label=_score_label(bs_score),
        )
        return overall_score, label

    # Classify aggregate score
    result = classify_snippets(snippets)

    # Build evidence: classify each news item individually to get keyword quotes
    evidence = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('body', '')}".strip()
        if not text:
            continue
        cls_result, item_evidence = classify_text_with_evidence(text)
        if not item_evidence:
            continue
        # Collect top keywords found in this article
        keywords = [e["keyword"] for e in item_evidence]
        directions = [e["direction"] for e in item_evidence]
        dimensions = [e.get("dimension", "policy") for e in item_evidence]
        best_quote = item_evidence[0]["quote"]  # Use first match as representative quote
        evidence.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "source_type": r.get("source", ""),
            "keywords": keywords,
            "directions": directions,
            "dimensions": dimensions,
            "quote": best_quote,
            "score": cls_result.score,
        })

    # Keep top 8 evidence items sorted by absolute score (strongest signal first)
    evidence.sort(key=lambda e: abs(e.get("score", 0)), reverse=True)
    evidence = evidence[:8]

    # Blend each dimension independently with historical leans (70% news, 30% historical)
    blended_policy = result.policy_score * 0.7 + participant.historical_lean * 0.3
    blended_policy = max(-5.0, min(5.0, blended_policy))

    blended_bs = result.balance_sheet_score * 0.7 + participant.historical_balance_sheet_lean * 0.3
    blended_bs = max(-5.0, min(5.0, blended_bs))

    # Overall: 70% policy + 30% balance sheet
    blended_score = 0.7 * blended_policy + 0.3 * blended_bs
    blended_score = max(-5.0, min(5.0, blended_score))

    label = _score_label(blended_score)
    policy_label = _score_label(blended_policy)
    bs_label = _score_label(blended_bs)

    add_stance(
        participant.name, blended_score, label, source="live", evidence=evidence,
        policy_score=blended_policy, policy_label=policy_label,
        balance_sheet_score=blended_bs, balance_sheet_label=bs_label,
    )

    logger.info(
        f"  Overall: {blended_score:+.3f} ({label}) | "
        f"Policy: {blended_policy:+.3f} ({policy_label}) | "
        f"Balance Sheet: {blended_bs:+.3f} ({bs_label}) "
        f"[{len(result.hawkish_matches)} hawkish, {len(result.dovish_matches)} dovish keywords] "
        f"[{len(evidence)} evidence items]"
    )
    return blended_score, label


def main():
    parser = argparse.ArgumentParser(description="FOMC Stance Tracker - Data Fetcher")
    parser.add_argument("--name", type=str, help="Fetch data for a single participant")
    parser.add_argument(
        "--participants-only",
        action="store_true",
        help="Just list participants, don't fetch",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force re-fetch even if cached data exists",
    )
    args = parser.parse_args()

    if args.participants_only:
        print("\n  FOMC Participants (2026)")
        print("  " + "=" * 60)
        for p in PARTICIPANTS:
            voter = "VOTER" if p.is_voter_2026 else "alt  "
            print(f"  [{voter}] {p.name:<28s} {p.institution}")
        print()
        return

    if args.name:
        p = get_participant(args.name)
        if not p:
            print(f"Error: No participant matching '{args.name}'")
            sys.exit(1)
        process_participant(p, use_cache=not args.no_cache)
    else:
        print("\n  Fetching data for all 19 FOMC participants...")
        print("  " + "=" * 60)
        results = []
        for p in PARTICIPANTS:
            score, label = process_participant(p, use_cache=not args.no_cache)
            results.append((p, score, label))

        # Summary
        print("\n  " + "=" * 60)
        print("  STANCE SUMMARY")
        print("  " + "=" * 60)
        hawks = sum(1 for _, _, l in results if l == "Hawkish")
        doves = sum(1 for _, _, l in results if l == "Dovish")
        neutrals = sum(1 for _, _, l in results if l == "Neutral")
        print(f"  Hawkish: {hawks}  |  Neutral: {neutrals}  |  Dovish: {doves}")
        print()

        for p, score, label in sorted(results, key=lambda x: -x[1]):
            voter = "*" if p.is_voter_2026 else " "
            bar_len = int(abs(score) * 4)
            if score >= 0:
                bar = " " * 20 + "|" + "#" * bar_len
            else:
                bar = " " * (20 - bar_len) + "#" * bar_len + "|"
            print(f"  {voter} {p.name:<28s} {score:+.3f}  {bar}  {label}")
        print("\n  * = 2026 voter\n")


if __name__ == "__main__":
    main()

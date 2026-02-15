#!/usr/bin/env python3
"""CLI orchestrator: fetch news, classify stances, store history."""

import argparse
import logging
import sys

from fomc_tracker.historical_data import add_stance, load_history
from fomc_tracker.news_fetcher import fetch_news_for_participant, load_cached_news
from fomc_tracker.participants import PARTICIPANTS, get_participant
from fomc_tracker.stance_classifier import classify_snippets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


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
        score = participant.historical_lean
        label = "Neutral"
        if score > 0.3:
            label = "Hawkish"
        elif score < -0.3:
            label = "Dovish"
        add_stance(participant.name, score, label, source="historical_lean")
        return score, label

    # Extract text snippets for classification
    snippets = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('body', '')}".strip()
        if text:
            snippets.append(text)

    if not snippets:
        logger.warning(f"  No text content for {participant.name}")
        score = participant.historical_lean
        label = "Neutral"
        if score > 0.3:
            label = "Hawkish"
        elif score < -0.3:
            label = "Dovish"
        add_stance(participant.name, score, label, source="historical_lean")
        return score, label

    # Classify
    result = classify_snippets(snippets)

    # Blend with historical lean (70% news, 30% historical baseline)
    blended_score = result.score * 0.7 + participant.historical_lean * 0.3
    blended_score = max(-1.0, min(1.0, blended_score))

    label = "Neutral"
    if blended_score > 0.3:
        label = "Hawkish"
    elif blended_score < -0.3:
        label = "Dovish"

    add_stance(participant.name, blended_score, label, source="live")

    logger.info(
        f"  Score: {blended_score:+.3f} ({label}) "
        f"[{len(result.hawkish_matches)} hawkish, {len(result.dovish_matches)} dovish keywords]"
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
            bar_len = int(abs(score) * 20)
            if score >= 0:
                bar = " " * 20 + "|" + "#" * bar_len
            else:
                bar = " " * (20 - bar_len) + "#" * bar_len + "|"
            print(f"  {voter} {p.name:<28s} {score:+.3f}  {bar}  {label}")
        print("\n  * = 2026 voter\n")


if __name__ == "__main__":
    main()

"""Tests for the BOE MPC Stance Tracker."""

import json
import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Participants
# ============================================================================

class TestParticipants:
    def test_roster_count(self):
        from boe_tracker.participants import PARTICIPANTS
        assert len(PARTICIPANTS) == 9

    def test_all_are_voters(self):
        from boe_tracker.participants import PARTICIPANTS
        assert all(p.is_voter for p in PARTICIPANTS)

    def test_governor_exists(self):
        from boe_tracker.participants import PARTICIPANTS
        governors = [p for p in PARTICIPANTS if p.role_type == "Governor"]
        assert len(governors) == 1
        assert governors[0].name == "Andrew Bailey"

    def test_deputy_governors(self):
        from boe_tracker.participants import PARTICIPANTS
        dgs = [p for p in PARTICIPANTS if p.role_type == "Deputy Governor"]
        assert len(dgs) == 3

    def test_external_members(self):
        from boe_tracker.participants import PARTICIPANTS, get_externals
        externals = get_externals()
        assert len(externals) == 4
        ext_names = {p.name for p in externals}
        assert "Swati Dhingra" in ext_names
        assert "Catherine L Mann" in ext_names

    def test_chief_economist(self):
        from boe_tracker.participants import PARTICIPANTS
        ce = [p for p in PARTICIPANTS if p.role_type == "Chief Economist"]
        assert len(ce) == 1
        assert ce[0].name == "Huw Pill"

    def test_get_participant_by_name(self):
        from boe_tracker.participants import get_participant
        p = get_participant("Bailey")
        assert p is not None
        assert p.name == "Andrew Bailey"

    def test_get_participant_not_found(self):
        from boe_tracker.participants import get_participant
        assert get_participant("Nonexistent Person") is None

    def test_get_internals(self):
        from boe_tracker.participants import get_internals
        internals = get_internals()
        # Governor + 3 DGs + Chief Economist = 5
        assert len(internals) == 5

    def test_historical_leans(self):
        from boe_tracker.participants import PARTICIPANTS
        for p in PARTICIPANTS:
            assert -5.0 <= p.historical_lean <= 5.0
            assert -5.0 <= p.historical_balance_sheet_lean <= 5.0


# ============================================================================
# Config
# ============================================================================

class TestConfig:
    def test_score_label_hawkish(self):
        from boe_tracker.config import score_label
        assert score_label(2.0) == "Hawkish"

    def test_score_label_dovish(self):
        from boe_tracker.config import score_label
        assert score_label(-2.0) == "Dovish"

    def test_score_label_neutral(self):
        from boe_tracker.config import score_label
        assert score_label(0.0) == "Neutral"
        assert score_label(1.4) == "Neutral"
        assert score_label(-1.4) == "Neutral"

    def test_score_color(self):
        from boe_tracker.config import score_color
        assert "#f87171" in score_color(2.0)  # hawk
        assert "#60a5fa" in score_color(-2.0)  # dove
        assert "#64748b" in score_color(0.0)  # neutral

    def test_defaults_loaded(self):
        from boe_tracker import config as cfg
        assert cfg.HAWKISH_THRESHOLD == 1.5
        assert cfg.DOVISH_THRESHOLD == -1.5
        assert cfg.SCORE_MIN == -5.0
        assert cfg.SCORE_MAX == 5.0

    def test_role_weights(self):
        from boe_tracker import config as cfg
        assert cfg.ROLE_WEIGHTS["Governor"] == 3.0
        assert cfg.ROLE_WEIGHTS["External Member"] == 1.0

    def test_boe_keywords(self):
        from boe_tracker import config as cfg
        assert "bank rate increase" in cfg.BOE_HAWKISH_TERMS
        assert "bank rate cut" in cfg.BOE_DOVISH_TERMS


# ============================================================================
# Meeting Calendar
# ============================================================================

class TestMeetingCalendar:
    def test_meeting_count(self):
        from boe_tracker.meeting_calendar import MEETINGS
        assert len(MEETINGS) >= 16  # 8 per year for 2025-2026

    def test_get_next_meeting(self):
        from boe_tracker.meeting_calendar import get_next_meeting
        m = get_next_meeting(date(2026, 2, 15))
        assert m is not None
        assert m.date >= date(2026, 2, 15)

    def test_get_previous_meeting(self):
        from boe_tracker.meeting_calendar import get_previous_meeting
        m = get_previous_meeting(date(2026, 2, 15))
        assert m is not None
        assert m.date < date(2026, 2, 15)
        assert m.decision is not None

    def test_get_current_rate(self):
        from boe_tracker.meeting_calendar import get_current_rate
        rate = get_current_rate(date(2026, 2, 15))
        assert rate is not None
        assert isinstance(rate, float)
        assert rate > 0

    def test_days_until_next_meeting(self):
        from boe_tracker.meeting_calendar import days_until_next_meeting
        days = days_until_next_meeting(date(2026, 2, 15))
        assert days is not None
        assert days >= 0

    def test_past_meetings(self):
        from boe_tracker.meeting_calendar import get_past_meetings
        past = get_past_meetings(n=4, ref=date(2026, 2, 15))
        assert len(past) >= 4
        for m in past:
            assert m.decision is not None

    def test_feb_2026_decision(self):
        from boe_tracker.meeting_calendar import get_previous_meeting
        m = get_previous_meeting(date(2026, 2, 15))
        assert m.decision == "-25"
        assert m.bank_rate == 3.50
        assert m.vote_split == "7-2"


# ============================================================================
# Historical Data
# ============================================================================

class TestHistoricalData:
    def test_seed_data_loaded(self):
        from boe_tracker.historical_data import SEED_DATA
        assert len(SEED_DATA) == 9
        assert "Andrew Bailey" in SEED_DATA
        assert "Swati Dhingra" in SEED_DATA

    def test_load_history(self):
        from boe_tracker.historical_data import load_history
        history = load_history()
        assert isinstance(history, dict)
        assert "Andrew Bailey" in history
        assert len(history["Andrew Bailey"]) >= 5

    def test_get_latest_stance(self):
        from boe_tracker.historical_data import get_latest_stance
        stance = get_latest_stance("Andrew Bailey")
        assert stance is not None
        assert "score" in stance
        assert "policy_score" in stance
        assert "balance_sheet_score" in stance

    def test_seed_data_has_dual_dimensions(self):
        from boe_tracker.historical_data import SEED_DATA
        for name, entries in SEED_DATA.items():
            for entry in entries:
                assert "policy_score" in entry, f"Missing policy_score for {name}"
                assert "balance_sheet_score" in entry, f"Missing balance_sheet_score for {name}"

    def test_dhingra_is_dovish(self):
        from boe_tracker.historical_data import get_latest_stance
        stance = get_latest_stance("Swati Dhingra")
        assert stance is not None
        assert stance["score"] < -1.5

    def test_mann_shift(self):
        """Mann shifted from hawkish to dovish in Dec 2025."""
        from boe_tracker.historical_data import SEED_DATA
        entries = SEED_DATA["Catherine L Mann"]
        # Early entries should be hawkish
        assert entries[0]["score"] > 1.5
        # Dec 2025 entry should be dovish (surprise 50bp cut vote)
        dec_entry = next(e for e in entries if e["date"] == "2025-12-15")
        assert dec_entry["score"] < -1.5


# ============================================================================
# Policy Signal
# ============================================================================

class TestPolicySignal:
    def test_compute_weighted_signal(self):
        from boe_tracker.policy_signal import compute_weighted_signal
        signal = compute_weighted_signal()
        assert "weighted_score" in signal
        assert "simple_average" in signal
        assert "internal_average" in signal
        assert "participant_contributions" in signal
        assert len(signal["participant_contributions"]) == 9

    def test_implied_rate_action_hold(self):
        from boe_tracker.policy_signal import implied_rate_action
        action = implied_rate_action(0.0)
        assert action["action"] == "Hold"
        assert action["direction"] == "neutral"
        assert action["magnitude_bp"] == 0

    def test_implied_rate_action_cut(self):
        from boe_tracker.policy_signal import implied_rate_action
        action = implied_rate_action(-2.5)
        assert action["direction"] == "easing"
        assert action["magnitude_bp"] > 0

    def test_implied_rate_action_hike(self):
        from boe_tracker.policy_signal import implied_rate_action
        action = implied_rate_action(2.5)
        assert action["direction"] == "tightening"
        assert action["magnitude_bp"] > 0

    def test_projected_rate(self):
        from boe_tracker.policy_signal import implied_rate_action
        action = implied_rate_action(-2.5)
        assert action["projected_rate"] is not None

    def test_meeting_drift(self):
        from boe_tracker.policy_signal import compute_meeting_drift
        drift = compute_meeting_drift()
        # Might be None if no previous meeting data
        if drift is not None:
            assert "drift" in drift
            assert "drift_direction" in drift


# ============================================================================
# Classification Integration (reuses FOMC classifier)
# ============================================================================

class TestClassification:
    def test_classify_boe_hawkish_text(self):
        from fomc_tracker.stance_classifier import classify_text_keyword
        result = classify_text_keyword(
            "The Bank of England should raise rates further. "
            "Inflation is too high and tightening monetary policy is needed."
        )
        assert result.score > 0

    def test_classify_boe_dovish_text(self):
        from fomc_tracker.stance_classifier import classify_text_keyword
        result = classify_text_keyword(
            "The economy is weakening and rate cuts are needed. "
            "Unemployment is rising and inflation is falling."
        )
        assert result.score < 0

    def test_classify_neutral_text(self):
        from fomc_tracker.stance_classifier import classify_text_keyword
        result = classify_text_keyword(
            "The weather in London was pleasant today."
        )
        assert result.score == 0.0

    def test_classify_snippets_aggregate(self):
        from fomc_tracker.stance_classifier import classify_snippets_keyword
        result = classify_snippets_keyword([
            "Interest rates should be raised to combat inflation",
            "The economy needs rate cuts to support growth",
        ])
        # Should be somewhere in the middle
        assert -5.0 <= result.score <= 5.0
        assert result.snippet_count == 2


# ============================================================================
# News Fetcher Registry
# ============================================================================

class TestNewsFetcherRegistry:
    def test_sources_registered(self):
        from boe_tracker.news_fetcher import list_sources
        sources = list_sources()
        names = [name for name, _ in sources]
        assert "duckduckgo" in names
        assert "boe_speeches" in names
        assert "boe_news_rss" in names
        assert "mpc_minutes" in names
        assert "treasury_committee" in names

    def test_register_custom_source(self):
        from boe_tracker.news_fetcher import register_source, list_sources

        def dummy_source(participant, **kwargs):
            return []

        initial_count = len(list_sources())
        register_source("test_source", dummy_source)
        assert len(list_sources()) == initial_count + 1

    def test_disable_enable_source(self):
        from boe_tracker.news_fetcher import (
            register_source, enable_source, disable_source, list_sources
        )

        def dummy(p, **kw):
            return []

        register_source("toggle_test", dummy, enabled=True)
        sources = dict(list_sources())
        assert sources["toggle_test"] is True

        disable_source("toggle_test")
        sources = dict(list_sources())
        assert sources["toggle_test"] is False

        enable_source("toggle_test")
        sources = dict(list_sources())
        assert sources["toggle_test"] is True


# ============================================================================
# MPC Minutes
# ============================================================================

class TestMPCMinutes:
    def test_parse_vote_record_hold(self):
        from boe_tracker.mpc_minutes import parse_vote_record
        text = "7 members voted to maintain Bank Rate at 4.50%"
        votes = parse_vote_record(text)
        assert votes is not None
        assert votes["hold"] == 7

    def test_parse_vote_record_cut(self):
        from boe_tracker.mpc_minutes import parse_vote_record
        text = (
            "7 members voted to maintain Bank Rate at 4.50%. "
            "2 members preferred to reduce Bank Rate by 0.25 percentage points."
        )
        votes = parse_vote_record(text)
        assert votes is not None
        assert votes["hold"] == 7
        assert votes["cut"] == 2

    def test_parse_vote_record_no_votes(self):
        from boe_tracker.mpc_minutes import parse_vote_record
        text = "No monetary policy discussion in this document."
        assert parse_vote_record(text) is None


# ============================================================================
# BOE Stats
# ============================================================================

class TestBOEStats:
    def test_is_available(self):
        from boe_tracker.boe_stats import is_available
        assert is_available() is True

    def test_generate_context_summary_empty(self):
        from boe_tracker.boe_stats import generate_context_summary
        assert generate_context_summary({}) == "Economic data unavailable"

    def test_generate_context_summary(self):
        from boe_tracker.boe_stats import generate_context_summary
        indicators = {
            "IUDBEDR": {"short_name": "Bank Rate", "latest": 3.50, "unit": "%"},
            "D7BT": {"short_name": "CPI", "latest": 2.8, "unit": "% YoY"},
        }
        summary = generate_context_summary(indicators)
        assert "Bank Rate" in summary
        assert "CPI" in summary

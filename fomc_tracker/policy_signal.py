"""Vote-weighted policy signal with implied rate action mapping."""

from datetime import date

from fomc_tracker.participants import PARTICIPANTS, Participant
from fomc_tracker.historical_data import load_history, get_latest_stance
from fomc_tracker.meeting_calendar import (
    get_next_meeting,
    get_previous_meeting,
    get_past_meetings,
    get_current_rate,
)


# ── Influence Weights ─────────────────────────────────────────────────────
# Reflects actual FOMC dynamics: the Chair has outsized influence (agenda
# setting, proposal framing, press conference), Vice Chair carries weight,
# voters decide, alternates influence through discussion but don't vote.

ROLE_WEIGHTS = {
    "Chair": 3.0,
    "Vice Chair": 1.5,
    "Vice Chair for Supervision": 1.25,
    "Governor": 1.0,        # Voting governors
    "President_voter": 1.0,  # Voting bank presidents
    "President_alt": 0.25,   # Non-voting alternates (participate but don't vote)
}


def _participant_weight(p: Participant) -> float:
    """Assign influence weight based on role and voting status."""
    if p.title == "Chair":
        return ROLE_WEIGHTS["Chair"]
    if p.title == "Vice Chair":
        return ROLE_WEIGHTS["Vice Chair"]
    if p.title == "Vice Chair for Supervision":
        return ROLE_WEIGHTS["Vice Chair for Supervision"]
    if p.is_governor:
        return ROLE_WEIGHTS["Governor"]
    if p.is_voter_2026:
        return ROLE_WEIGHTS["President_voter"]
    return ROLE_WEIGHTS["President_alt"]


def compute_weighted_signal(
    score_key: str = "score",
    ref_date: date | None = None,
) -> dict:
    """Compute the vote-weighted committee policy signal.

    Returns dict with:
        weighted_score: float (-5 to +5)
        simple_average: float
        voter_average: float
        participant_contributions: list of dicts
        total_weight: float
    """
    contributions = []
    total_weight = 0.0
    weighted_sum = 0.0
    voter_sum = 0.0
    voter_count = 0
    simple_sum = 0.0
    count = 0

    for p in PARTICIPANTS:
        latest = get_latest_stance(p.name)
        if latest is None:
            score = p.historical_lean if score_key == "score" else (
                p.historical_lean if score_key == "policy_score"
                else p.historical_balance_sheet_lean
            )
        else:
            score = latest.get(score_key, latest.get("score", 0))

        w = _participant_weight(p)
        weighted_sum += score * w
        total_weight += w
        simple_sum += score
        count += 1

        if p.is_voter_2026:
            voter_sum += score
            voter_count += 1

        contributions.append({
            "name": p.name,
            "score": score,
            "weight": w,
            "weighted_contribution": score * w,
            "voter": p.is_voter_2026,
            "role": p.title,
        })

    weighted_score = weighted_sum / total_weight if total_weight else 0.0
    simple_average = simple_sum / count if count else 0.0
    voter_average = voter_sum / voter_count if voter_count else 0.0

    return {
        "weighted_score": round(weighted_score, 3),
        "simple_average": round(simple_average, 3),
        "voter_average": round(voter_average, 3),
        "participant_contributions": sorted(
            contributions, key=lambda c: c["weighted_contribution"], reverse=True
        ),
        "total_weight": total_weight,
    }


# ── Implied Rate Action ──────────────────────────────────────────────────
# Maps the weighted stance score to an expected policy action.
# The FOMC is known for incrementalism — even a fairly hawkish committee
# typically moves in 25bp steps unless conditions are extreme.

_ACTION_THRESHOLDS = [
    # (min_score, max_score, action_label, direction, magnitude_bp)
    (-5.0, -3.5, "Cut 50bp",   "easing",     50),
    (-3.5, -2.0, "Cut 25bp",   "easing",     25),
    (-2.0, -0.5, "Lean Cut",   "easing",     25),
    (-0.5,  0.5, "Hold",       "neutral",     0),
    ( 0.5,  2.0, "Lean Hike",  "tightening", 25),
    ( 2.0,  3.5, "Hike 25bp",  "tightening", 25),
    ( 3.5,  5.0, "Hike 50bp",  "tightening", 50),
]


def implied_rate_action(weighted_score: float) -> dict:
    """Map a weighted stance score to an implied policy action.

    Returns dict with:
        action: str (e.g. "Hold", "Lean Cut", "Cut 25bp")
        direction: str ("easing", "neutral", "tightening")
        magnitude_bp: int
        confidence: str ("high", "moderate", "low")
        projected_rate: tuple | None (new target range if action taken)
    """
    action_label = "Hold"
    direction = "neutral"
    magnitude_bp = 0

    for min_s, max_s, label, dirn, mag in _ACTION_THRESHOLDS:
        if min_s <= weighted_score < max_s:
            action_label = label
            direction = dirn
            magnitude_bp = mag
            break
    else:
        # Score >= 5.0 edge case
        if weighted_score >= 3.5:
            action_label, direction, magnitude_bp = "Hike 50bp", "tightening", 50

    # Confidence based on distance from threshold boundaries
    abs_score = abs(weighted_score)
    if abs_score < 0.5:
        confidence = "high"  # Clearly in hold territory
    elif abs_score < 1.0:
        confidence = "moderate"  # Near the lean threshold
    elif abs_score < 2.0:
        confidence = "moderate"  # Leaning but not decisive
    else:
        confidence = "high"  # Strong directional signal

    # Project new rate range if action is taken
    current_rate = get_current_rate()
    projected_rate = None
    if current_rate and magnitude_bp > 0:
        delta = magnitude_bp / 100.0
        if direction == "easing":
            projected_rate = (
                round(current_rate[0] - delta, 2),
                round(current_rate[1] - delta, 2),
            )
        else:
            projected_rate = (
                round(current_rate[0] + delta, 2),
                round(current_rate[1] + delta, 2),
            )

    return {
        "action": action_label,
        "direction": direction,
        "magnitude_bp": magnitude_bp,
        "confidence": confidence,
        "projected_rate": projected_rate,
    }


# ── Meeting-to-Meeting Drift ─────────────────────────────────────────────

def compute_meeting_drift(score_key: str = "score") -> dict | None:
    """Compute how the committee signal has shifted since the last meeting.

    Returns dict with:
        previous_meeting_date: str
        previous_signal: float (weighted score as of that meeting)
        current_signal: float
        drift: float (current - previous)
        drift_direction: str ("hawkish shift", "dovish shift", "stable")
    """
    prev = get_previous_meeting()
    if prev is None:
        return None

    history = load_history()
    prev_date_str = prev.end_date.isoformat()

    # Compute weighted signal using stances closest to previous meeting date
    prev_weighted_sum = 0.0
    prev_total_weight = 0.0

    for p in PARTICIPANTS:
        entries = history.get(p.name, [])
        w = _participant_weight(p)

        # Find the entry closest to (and not after) the previous meeting
        closest = None
        for e in entries:
            if e["date"] <= prev_date_str:
                closest = e
            else:
                break

        if closest:
            score = closest.get(score_key, closest.get("score", 0))
        else:
            # Fall back to historical lean
            score = p.historical_lean if score_key in ("score", "policy_score") else p.historical_balance_sheet_lean

        prev_weighted_sum += score * w
        prev_total_weight += w

    prev_signal = prev_weighted_sum / prev_total_weight if prev_total_weight else 0.0

    current = compute_weighted_signal(score_key)
    current_signal = current["weighted_score"]
    drift = current_signal - prev_signal

    if drift > 0.3:
        drift_direction = "hawkish shift"
    elif drift < -0.3:
        drift_direction = "dovish shift"
    else:
        drift_direction = "stable"

    return {
        "previous_meeting_date": prev.end_date.isoformat(),
        "previous_decision": prev.decision,
        "previous_signal": round(prev_signal, 3),
        "current_signal": round(current_signal, 3),
        "drift": round(drift, 3),
        "drift_direction": drift_direction,
    }


def signal_vs_decisions(score_key: str = "score", n_meetings: int = 6) -> list[dict]:
    """Compare historical weighted signals against actual FOMC decisions.

    For each past meeting, reconstructs the weighted signal from stance data
    available at that time and compares to the actual decision.

    Returns list of dicts with:
        meeting_date: str
        decision: str
        signal_score: float
        implied_action: str
        match: bool (did signal predict the decision direction?)
    """
    history = load_history()
    past = get_past_meetings(n_meetings)
    results = []

    for meeting in past:
        meeting_date_str = meeting.end_date.isoformat()

        # Reconstruct weighted signal as of meeting date
        weighted_sum = 0.0
        total_weight = 0.0

        for p in PARTICIPANTS:
            entries = history.get(p.name, [])
            w = _participant_weight(p)

            closest = None
            for e in entries:
                if e["date"] <= meeting_date_str:
                    closest = e
                else:
                    break

            if closest:
                score = closest.get(score_key, closest.get("score", 0))
            else:
                score = p.historical_lean if score_key in ("score", "policy_score") else p.historical_balance_sheet_lean

            weighted_sum += score * w
            total_weight += w

        signal_score = weighted_sum / total_weight if total_weight else 0.0
        action = implied_rate_action(signal_score)

        # Check if signal direction matched actual decision
        actual = meeting.decision or "hold"
        actual_dir = "easing" if "-" in actual else ("tightening" if "+" in actual else "neutral")
        match = action["direction"] == actual_dir

        results.append({
            "meeting_date": meeting.end_date.isoformat(),
            "decision": meeting.decision,
            "rate_range": f"{meeting.rate_lower:.2f}%-{meeting.rate_upper:.2f}%" if meeting.rate_upper else "N/A",
            "signal_score": round(signal_score, 3),
            "implied_action": action["action"],
            "implied_direction": action["direction"],
            "match": match,
            "statement_note": meeting.statement_note,
        })

    return results

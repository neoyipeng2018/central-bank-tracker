"""Vote-weighted MPC policy signal with implied rate action mapping."""

from datetime import date

from boe_tracker import config as cfg
from boe_tracker.participants import PARTICIPANTS, Participant
from boe_tracker.historical_data import load_history, get_latest_stance
from boe_tracker.meeting_calendar import (
    get_next_meeting,
    get_previous_meeting,
    get_past_meetings,
    get_current_rate,
)


ROLE_WEIGHTS = cfg.ROLE_WEIGHTS


def _participant_weight(p: Participant) -> float:
    """Assign influence weight based on role."""
    return ROLE_WEIGHTS.get(p.role_type, 1.0)


def compute_weighted_signal(
    score_key: str = "score",
    ref_date: date | None = None,
) -> dict:
    """Compute the vote-weighted MPC policy signal.

    Returns dict with:
        weighted_score: float (-5 to +5)
        simple_average: float
        internal_average: float (internal members only)
        participant_contributions: list of dicts
        total_weight: float
    """
    contributions = []
    total_weight = 0.0
    weighted_sum = 0.0
    internal_sum = 0.0
    internal_count = 0
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

        if p.role_type != "External Member":
            internal_sum += score
            internal_count += 1

        contributions.append({
            "name": p.name,
            "score": score,
            "weight": w,
            "weighted_contribution": score * w,
            "role": p.role_type,
            "title": p.title,
        })

    weighted_score = weighted_sum / total_weight if total_weight else 0.0
    simple_average = simple_sum / count if count else 0.0
    internal_average = internal_sum / internal_count if internal_count else 0.0

    return {
        "weighted_score": round(weighted_score, 3),
        "simple_average": round(simple_average, 3),
        "internal_average": round(internal_average, 3),
        "participant_contributions": sorted(
            contributions, key=lambda c: c["weighted_contribution"], reverse=True
        ),
        "total_weight": total_weight,
    }


# -- Implied Rate Action ---------------------------------------------------

_ACTION_THRESHOLDS = cfg.ACTION_THRESHOLDS


def implied_rate_action(weighted_score: float) -> dict:
    """Map a weighted stance score to an implied policy action.

    Returns dict with:
        action: str (e.g. "Hold", "Lean Cut", "Cut 25bp")
        direction: str ("easing", "neutral", "tightening")
        magnitude_bp: int
        confidence: str ("high", "moderate", "low")
        projected_rate: float | None (new Bank Rate if action taken)
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
        if weighted_score >= 3.5:
            action_label, direction, magnitude_bp = "Hike 50bp", "tightening", 50

    # Confidence based on distance from threshold boundaries
    abs_score = abs(weighted_score)
    if abs_score < 0.5:
        confidence = "high"
    elif abs_score < 1.0:
        confidence = "moderate"
    elif abs_score < 2.0:
        confidence = "moderate"
    else:
        confidence = "high"

    # Project new rate if action is taken
    current_rate = get_current_rate()
    projected_rate = None
    if current_rate is not None and magnitude_bp > 0:
        delta = magnitude_bp / 100.0
        if direction == "easing":
            projected_rate = round(current_rate - delta, 2)
        else:
            projected_rate = round(current_rate + delta, 2)

    return {
        "action": action_label,
        "direction": direction,
        "magnitude_bp": magnitude_bp,
        "confidence": confidence,
        "projected_rate": projected_rate,
    }


# -- Meeting-to-Meeting Drift -----------------------------------------------

def compute_meeting_drift(score_key: str = "score") -> dict | None:
    """Compute how the MPC signal has shifted since the last meeting."""
    prev = get_previous_meeting()
    if prev is None:
        return None

    history = load_history()
    prev_date_str = prev.date.isoformat()

    prev_weighted_sum = 0.0
    prev_total_weight = 0.0

    for p in PARTICIPANTS:
        entries = history.get(p.name, [])
        w = _participant_weight(p)

        closest = None
        for e in entries:
            if e["date"] <= prev_date_str:
                closest = e
            else:
                break

        if closest:
            score = closest.get(score_key, closest.get("score", 0))
        else:
            score = p.historical_lean if score_key in ("score", "policy_score") else p.historical_balance_sheet_lean

        prev_weighted_sum += score * w
        prev_total_weight += w

    prev_signal = prev_weighted_sum / prev_total_weight if prev_total_weight else 0.0

    current = compute_weighted_signal(score_key)
    current_signal = current["weighted_score"]
    drift = current_signal - prev_signal

    if drift > cfg.HAWKISH_DRIFT_THRESHOLD:
        drift_direction = "hawkish shift"
    elif drift < cfg.DOVISH_DRIFT_THRESHOLD:
        drift_direction = "dovish shift"
    else:
        drift_direction = "stable"

    return {
        "previous_meeting_date": prev.date.isoformat(),
        "previous_decision": prev.decision,
        "previous_signal": round(prev_signal, 3),
        "current_signal": round(current_signal, 3),
        "drift": round(drift, 3),
        "drift_direction": drift_direction,
    }


def signal_vs_decisions(score_key: str = "score", n_meetings: int = 6) -> list[dict]:
    """Compare historical weighted signals against actual MPC decisions."""
    history = load_history()
    past = get_past_meetings(n_meetings)
    results = []

    for meeting in past:
        meeting_date_str = meeting.date.isoformat()

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

        actual = meeting.decision or "hold"
        actual_dir = "easing" if "-" in actual else ("tightening" if "+" in actual else "neutral")
        match = action["direction"] == actual_dir

        results.append({
            "meeting_date": meeting.date.isoformat(),
            "decision": meeting.decision,
            "bank_rate": f"{meeting.bank_rate:.2f}%" if meeting.bank_rate else "N/A",
            "vote_split": meeting.vote_split,
            "signal_score": round(signal_score, 3),
            "implied_action": action["action"],
            "implied_direction": action["direction"],
            "match": match,
            "statement_note": meeting.statement_note,
        })

    return results

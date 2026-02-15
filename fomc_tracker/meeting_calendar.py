"""FOMC meeting calendar with rate decisions and cycle awareness."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass
class FOMCMeeting:
    """Represents a single FOMC meeting."""
    start_date: date  # First day of two-day meeting
    end_date: date    # Decision announcement day
    # Actual decision: "hold", "+25", "+50", "-25", "-50", or None if future
    decision: str | None = None
    # Fed funds rate target range after decision (upper bound in %)
    rate_upper: float | None = None
    rate_lower: float | None = None
    # Optional statement summary
    statement_note: str = ""


# FOMC meetings: 8 scheduled per year
# Blackout period starts the second Saturday before the meeting
MEETINGS: list[FOMCMeeting] = [
    # ── 2025 ──────────────────────────────────────────────
    FOMCMeeting(
        start_date=date(2025, 1, 28), end_date=date(2025, 1, 29),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Held steady; noted inflation progress slowing",
    ),
    FOMCMeeting(
        start_date=date(2025, 3, 18), end_date=date(2025, 3, 19),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Maintained rates; watching tariff uncertainty",
    ),
    FOMCMeeting(
        start_date=date(2025, 5, 6), end_date=date(2025, 5, 7),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Held rates; labor market remains solid",
    ),
    FOMCMeeting(
        start_date=date(2025, 6, 17), end_date=date(2025, 6, 18),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="No change; data-dependent approach emphasized",
    ),
    FOMCMeeting(
        start_date=date(2025, 7, 29), end_date=date(2025, 7, 30),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Held steady; inflation still above 2% target",
    ),
    FOMCMeeting(
        start_date=date(2025, 9, 16), end_date=date(2025, 9, 17),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Maintained rates; watching incoming data",
    ),
    FOMCMeeting(
        start_date=date(2025, 10, 28), end_date=date(2025, 10, 29),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="No change; risks roughly balanced",
    ),
    FOMCMeeting(
        start_date=date(2025, 12, 16), end_date=date(2025, 12, 17),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Held rates; SEP unchanged from September",
    ),
    # ── 2026 ──────────────────────────────────────────────
    FOMCMeeting(
        start_date=date(2026, 1, 27), end_date=date(2026, 1, 28),
        decision="hold", rate_upper=4.50, rate_lower=4.25,
        statement_note="Maintained rates; watching policy uncertainty",
    ),
    FOMCMeeting(
        start_date=date(2026, 3, 17), end_date=date(2026, 3, 18),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 5, 5), end_date=date(2026, 5, 6),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 6, 16), end_date=date(2026, 6, 17),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 7, 28), end_date=date(2026, 7, 29),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 9, 15), end_date=date(2026, 9, 16),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 10, 27), end_date=date(2026, 10, 28),
        decision=None, rate_upper=None, rate_lower=None,
    ),
    FOMCMeeting(
        start_date=date(2026, 12, 15), end_date=date(2026, 12, 16),
        decision=None, rate_upper=None, rate_lower=None,
    ),
]


def _blackout_start(meeting: FOMCMeeting) -> date:
    """Blackout begins the second Saturday before the meeting start date."""
    days_to_saturday = (meeting.start_date.weekday() - 5) % 7
    first_saturday_before = meeting.start_date - timedelta(days=days_to_saturday or 7)
    return first_saturday_before - timedelta(days=7)


def get_next_meeting(ref: date | None = None) -> FOMCMeeting | None:
    """Get the next upcoming FOMC meeting (whose end_date hasn't passed)."""
    ref = ref or date.today()
    for m in MEETINGS:
        if m.end_date >= ref:
            return m
    return None


def get_previous_meeting(ref: date | None = None) -> FOMCMeeting | None:
    """Get the most recent completed FOMC meeting."""
    ref = ref or date.today()
    prev = None
    for m in MEETINGS:
        if m.end_date < ref:
            prev = m
        else:
            break
    return prev


def days_until_next_meeting(ref: date | None = None) -> int | None:
    """Days until the next FOMC decision date."""
    nxt = get_next_meeting(ref)
    if nxt is None:
        return None
    ref = ref or date.today()
    return (nxt.end_date - ref).days


def is_blackout_period(ref: date | None = None) -> bool:
    """Check if the reference date falls in the FOMC communications blackout."""
    ref = ref or date.today()
    nxt = get_next_meeting(ref)
    if nxt is None:
        return False
    bo_start = _blackout_start(nxt)
    return bo_start <= ref <= nxt.end_date


def get_meetings_in_range(start: date, end: date) -> list[FOMCMeeting]:
    """Return meetings whose decision dates fall within [start, end]."""
    return [m for m in MEETINGS if start <= m.end_date <= end]


def get_past_meetings(n: int = 8, ref: date | None = None) -> list[FOMCMeeting]:
    """Get the last N completed meetings with decisions."""
    ref = ref or date.today()
    past = [m for m in MEETINGS if m.end_date < ref and m.decision is not None]
    return past[-n:]


def get_current_rate(ref: date | None = None) -> tuple[float, float] | None:
    """Get the current fed funds target range based on the last decision."""
    prev = get_previous_meeting(ref)
    if prev and prev.rate_upper is not None:
        return (prev.rate_lower, prev.rate_upper)
    return None

"""MPC meeting calendar with rate decisions and cycle awareness."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class MPCMeeting:
    """Represents a single MPC meeting."""
    date: date  # Decision announcement day (MPC meets over multiple days, decision on Thursday)
    decision: str | None = None  # "hold", "+25", "+50", "-25", "-50", or None if future
    bank_rate: float | None = None  # Bank Rate after decision (%)
    vote_split: str = ""  # e.g. "7-2" or "5-4"
    statement_note: str = ""


# MPC meetings: 8 per year, decisions announced on Thursdays
MEETINGS: list[MPCMeeting] = [
    # -- 2025 --
    MPCMeeting(
        date=date(2025, 2, 6),
        decision="-25", bank_rate=4.50, vote_split="7-2",
        statement_note="Cut to 4.50%; Dhingra and Taylor voted for 50bp cut",
    ),
    MPCMeeting(
        date=date(2025, 3, 20),
        decision="hold", bank_rate=4.50, vote_split="8-1",
        statement_note="Held at 4.50%; Dhingra voted for cut",
    ),
    MPCMeeting(
        date=date(2025, 5, 8),
        decision="-25", bank_rate=4.25, vote_split="5-4",
        statement_note="Cut to 4.25%; Mann surprised with 50bp cut vote",
    ),
    MPCMeeting(
        date=date(2025, 6, 19),
        decision="hold", bank_rate=4.25, vote_split="7-2",
        statement_note="Held at 4.25%; watching services inflation",
    ),
    MPCMeeting(
        date=date(2025, 8, 7),
        decision="-25", bank_rate=4.00, vote_split="6-3",
        statement_note="Cut to 4.00%; gradual easing path",
    ),
    MPCMeeting(
        date=date(2025, 9, 18),
        decision="hold", bank_rate=4.00, vote_split="7-2",
        statement_note="Held at 4.00%; cautious approach",
    ),
    MPCMeeting(
        date=date(2025, 11, 6),
        decision="-25", bank_rate=3.75, vote_split="6-3",
        statement_note="Cut to 3.75%; inflation progress continues",
    ),
    MPCMeeting(
        date=date(2025, 12, 18),
        decision="hold", bank_rate=3.75, vote_split="7-2",
        statement_note="Held at 3.75%; assessing inflation outlook",
    ),
    # -- 2026 --
    MPCMeeting(
        date=date(2026, 2, 6),
        decision="-25", bank_rate=3.50, vote_split="7-2",
        statement_note="Cut to 3.50%; gradual easing continues",
    ),
    MPCMeeting(
        date=date(2026, 3, 20),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 5, 7),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 6, 19),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 8, 6),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 9, 17),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 11, 5),
        decision=None, bank_rate=None,
    ),
    MPCMeeting(
        date=date(2026, 12, 17),
        decision=None, bank_rate=None,
    ),
]


def _load_extra_meetings() -> None:
    """Append extra meetings from ``local/boe_meetings.py`` if present."""
    try:
        from local.boe_meetings import EXTRA_MEETINGS  # type: ignore[import-not-found]
        existing = {m.date for m in MEETINGS}
        for m in EXTRA_MEETINGS:
            if m.date not in existing:
                MEETINGS.append(m)
        MEETINGS.sort(key=lambda m: m.date)
    except ImportError:
        pass


_load_extra_meetings()


def _blackout_start(meeting: MPCMeeting) -> date:
    """Blackout begins the second Saturday before the meeting date.

    BOE pre-MPC quiet period is similar to FOMC -- approximately two weeks
    before the decision announcement.
    """
    days_to_saturday = (meeting.date.weekday() - 5) % 7
    first_saturday_before = meeting.date - timedelta(days=days_to_saturday or 7)
    return first_saturday_before - timedelta(days=7)


def get_next_meeting(ref: date | None = None) -> MPCMeeting | None:
    """Get the next upcoming MPC meeting."""
    ref = ref or date.today()
    for m in MEETINGS:
        if m.date >= ref:
            return m
    return None


def get_previous_meeting(ref: date | None = None) -> MPCMeeting | None:
    """Get the most recent completed MPC meeting."""
    ref = ref or date.today()
    prev = None
    for m in MEETINGS:
        if m.date < ref:
            prev = m
        else:
            break
    return prev


def days_until_next_meeting(ref: date | None = None) -> int | None:
    """Days until the next MPC decision date."""
    nxt = get_next_meeting(ref)
    if nxt is None:
        return None
    ref = ref or date.today()
    return (nxt.date - ref).days


def is_blackout_period(ref: date | None = None) -> bool:
    """Check if the reference date falls in the MPC communications quiet period."""
    ref = ref or date.today()
    nxt = get_next_meeting(ref)
    if nxt is None:
        return False
    bo_start = _blackout_start(nxt)
    return bo_start <= ref <= nxt.date


def get_meetings_in_range(start: date, end: date) -> list[MPCMeeting]:
    """Return meetings whose decision dates fall within [start, end]."""
    return [m for m in MEETINGS if start <= m.date <= end]


def get_past_meetings(n: int = 8, ref: date | None = None) -> list[MPCMeeting]:
    """Get the last N completed meetings with decisions."""
    ref = ref or date.today()
    past = [m for m in MEETINGS if m.date < ref and m.decision is not None]
    return past[-n:]


def get_current_rate(ref: date | None = None) -> float | None:
    """Get the current Bank Rate based on the last decision."""
    prev = get_previous_meeting(ref)
    if prev and prev.bank_rate is not None:
        return prev.bank_rate
    return None

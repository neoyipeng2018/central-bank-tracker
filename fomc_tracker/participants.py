"""FOMC participant roster and metadata."""

from dataclasses import dataclass


@dataclass
class Participant:
    name: str
    title: str
    institution: str
    is_voter_2026: bool
    is_governor: bool
    # Baseline lean from historical record: -5 (dovish) to +5 (hawkish)
    historical_lean: float  # policy (rates) lean
    historical_balance_sheet_lean: float = 0.0  # balance sheet (QT/QE) lean


# Full FOMC roster for 2026 + notable incoming officials
PARTICIPANTS: list[Participant] = [
    # ── Incoming Chair (nominated, not yet serving) ────────────────
    Participant(
        name="Kevin M. Warsh",
        title="Nominated Fed Chair",
        institution="Incoming",
        is_voter_2026=False,
        is_governor=False,
        # Warsh served as Fed Governor 2006-2011; known as a hawk who
        # dissented against QE and favors rules-based monetary policy
        historical_lean=2.75,
        historical_balance_sheet_lean=2.50,  # strongly opposed QE
    ),
    # ── Board of Governors (all vote) ──────────────────────────────
    Participant(
        name="Jerome H. Powell",
        title="Chair",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=0.25,
        historical_balance_sheet_lean=0.25,  # pragmatic, follows committee consensus
    ),
    Participant(
        name="Philip N. Jefferson",
        title="Vice Chair",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=-0.50,
        historical_balance_sheet_lean=-0.25,
    ),
    Participant(
        name="Michael S. Barr",
        title="Vice Chair for Supervision",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=-1.00,
        historical_balance_sheet_lean=-0.50,
    ),
    Participant(
        name="Michelle W. Bowman",
        title="Governor",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=2.75,
        historical_balance_sheet_lean=1.75,  # supports QT
    ),
    Participant(
        name="Christopher J. Waller",
        title="Governor",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=2.25,
        historical_balance_sheet_lean=1.50,  # supports continued QT
    ),
    Participant(
        name="Lisa D. Cook",
        title="Governor",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=-1.25,
        historical_balance_sheet_lean=-0.75,
    ),
    Participant(
        name="Adriana D. Kugler",
        title="Governor",
        institution="Board of Governors",
        is_voter_2026=True,
        is_governor=True,
        historical_lean=-0.75,
        historical_balance_sheet_lean=-0.25,
    ),
    # ── Federal Reserve Bank Presidents ────────────────────────────
    # NY Fed president always votes
    Participant(
        name="John C. Williams",
        title="President",
        institution="FRB New York",
        is_voter_2026=True,
        is_governor=False,
        historical_lean=-0.25,
        historical_balance_sheet_lean=0.50,  # NY Fed manages operations; slightly hawkish on BS
    ),
    # 2026 rotating voters
    Participant(
        name="Patrick T. Harker",
        title="President",
        institution="FRB Philadelphia",
        is_voter_2026=True,
        is_governor=False,
        historical_lean=0.50,
        historical_balance_sheet_lean=0.25,
    ),
    Participant(
        name="Thomas I. Barkin",
        title="President",
        institution="FRB Richmond",
        is_voter_2026=True,
        is_governor=False,
        historical_lean=0.75,
        historical_balance_sheet_lean=0.50,
    ),
    Participant(
        name="Raphael W. Bostic",
        title="President",
        institution="FRB Atlanta",
        is_voter_2026=True,
        is_governor=False,
        historical_lean=-0.50,
        historical_balance_sheet_lean=-0.25,
    ),
    Participant(
        name="Mary C. Daly",
        title="President",
        institution="FRB San Francisco",
        is_voter_2026=True,
        is_governor=False,
        historical_lean=-0.75,
        historical_balance_sheet_lean=-0.50,
    ),
    # 2026 non-voting (alternate) participants
    Participant(
        name="Susan M. Collins",
        title="President",
        institution="FRB Boston",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=0.25,
        historical_balance_sheet_lean=0.00,
    ),
    Participant(
        name="Beth M. Hammack",
        title="President",
        institution="FRB Cleveland",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=1.00,
        historical_balance_sheet_lean=0.75,
    ),
    Participant(
        name="Austan D. Goolsbee",
        title="President",
        institution="FRB Chicago",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=-1.75,
        historical_balance_sheet_lean=-1.00,  # more dovish on BS too
    ),
    Participant(
        name="Alberto G. Musalem",
        title="President",
        institution="FRB St. Louis",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=1.25,
        historical_balance_sheet_lean=0.75,
    ),
    Participant(
        name="Jeffrey R. Schmid",
        title="President",
        institution="FRB Kansas City",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=1.75,
        historical_balance_sheet_lean=1.25,
    ),
    Participant(
        name="Lorie K. Logan",
        title="President",
        institution="FRB Dallas",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=2.00,
        historical_balance_sheet_lean=-1.00,  # hawkish on rates, dovish on BS (advocates slowing QT)
    ),
    Participant(
        name="Neel Kashkari",
        title="President",
        institution="FRB Minneapolis",
        is_voter_2026=False,
        is_governor=False,
        historical_lean=-1.50,
        historical_balance_sheet_lean=-1.00,
    ),
]


def get_participant(name: str) -> Participant | None:
    """Find a participant by partial name match (case-insensitive)."""
    name_lower = name.lower()
    for p in PARTICIPANTS:
        if name_lower in p.name.lower():
            return p
    return None


def get_voters() -> list[Participant]:
    return [p for p in PARTICIPANTS if p.is_voter_2026]


def get_alternates() -> list[Participant]:
    return [p for p in PARTICIPANTS if not p.is_voter_2026]

"""MPC participant roster and metadata."""

from dataclasses import dataclass


@dataclass
class Participant:
    name: str
    title: str
    institution: str  # Always "Bank of England" for MPC
    is_voter: bool  # All 9 MPC members vote
    role_type: str  # "Governor", "Deputy Governor", "Chief Economist", "External Member"
    # Baseline lean from historical record: -5 (dovish) to +5 (hawkish)
    historical_lean: float
    historical_balance_sheet_lean: float = 0.0


# Current MPC members (9 total)
PARTICIPANTS: list[Participant] = [
    Participant(
        name="Andrew Bailey",
        title="Governor",
        institution="Bank of England",
        is_voter=True,
        role_type="Governor",
        historical_lean=0.25,
        historical_balance_sheet_lean=0.25,
    ),
    Participant(
        name="Sarah Breeden",
        title="Deputy Governor, Financial Stability",
        institution="Bank of England",
        is_voter=True,
        role_type="Deputy Governor",
        historical_lean=-0.25,
        historical_balance_sheet_lean=0.00,
    ),
    Participant(
        name="Clare Lombardelli",
        title="Deputy Governor, Monetary Policy",
        institution="Bank of England",
        is_voter=True,
        role_type="Deputy Governor",
        historical_lean=-0.25,
        historical_balance_sheet_lean=0.00,
    ),
    Participant(
        name="Dave Ramsden",
        title="Deputy Governor, Markets & Banking",
        institution="Bank of England",
        is_voter=True,
        role_type="Deputy Governor",
        historical_lean=-0.75,
        historical_balance_sheet_lean=-0.25,
    ),
    Participant(
        name="Huw Pill",
        title="Chief Economist",
        institution="Bank of England",
        is_voter=True,
        role_type="Chief Economist",
        historical_lean=1.00,
        historical_balance_sheet_lean=0.50,
    ),
    Participant(
        name="Megan Greene",
        title="External Member",
        institution="Bank of England",
        is_voter=True,
        role_type="External Member",
        historical_lean=1.25,
        historical_balance_sheet_lean=0.50,
    ),
    Participant(
        name="Catherine L Mann",
        title="External Member",
        institution="Bank of England",
        is_voter=True,
        role_type="External Member",
        historical_lean=2.00,
        historical_balance_sheet_lean=1.00,
    ),
    Participant(
        name="Swati Dhingra",
        title="External Member",
        institution="Bank of England",
        is_voter=True,
        role_type="External Member",
        historical_lean=-2.50,
        historical_balance_sheet_lean=-1.00,
    ),
    Participant(
        name="Alan Taylor",
        title="External Member",
        institution="Bank of England",
        is_voter=True,
        role_type="External Member",
        historical_lean=-1.00,
        historical_balance_sheet_lean=-0.50,
    ),
]


def _load_extra_participants() -> None:
    """Append extra participants from ``local/boe_participants.py`` if present."""
    try:
        from local.boe_participants import EXTRA_PARTICIPANTS  # type: ignore[import-not-found]
        existing_names = {p.name for p in PARTICIPANTS}
        for p in EXTRA_PARTICIPANTS:
            if p.name not in existing_names:
                PARTICIPANTS.append(p)
    except ImportError:
        pass


_load_extra_participants()


def get_participant(name: str) -> Participant | None:
    """Find a participant by partial name match (case-insensitive)."""
    name_lower = name.lower()
    for p in PARTICIPANTS:
        if name_lower in p.name.lower():
            return p
    return None


def get_internals() -> list[Participant]:
    """Return internal MPC members (Governor, Deputies, Chief Economist)."""
    return [p for p in PARTICIPANTS if p.role_type != "External Member"]


def get_externals() -> list[Participant]:
    """Return external MPC members."""
    return [p for p in PARTICIPANTS if p.role_type == "External Member"]

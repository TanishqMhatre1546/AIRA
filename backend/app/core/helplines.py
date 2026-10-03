"""Indian national emergency and healthcare helplines registry.

Note: Helpline numbers and operational state availability must be verified
by local administrators before production deployment.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Helpline:
    """Helpline contact information."""

    number: str
    name: str
    description: str
    verified_on: str | None = None


# National Emergency Number (Police, Fire, Ambulance)
HELPLINE_NATIONAL_EMERGENCY = Helpline(
    number="112",
    name="National Emergency Number",
    description=(
        "All-in-one emergency helpline across India for police, fire, and ambulance services."
    ),
    verified_on=None,  # State availability must be verified
)

# Emergency Medical Ambulance Service
HELPLINE_AMBULANCE = Helpline(
    number="108",
    name="Emergency Ambulance",
    description="Emergency medical transport and ambulance dispatch in participating states.",
    verified_on=None,  # State availability must be verified
)

# Maternal and Child Healthcare Ambulance Service
HELPLINE_MATERNAL_CHILD = Helpline(
    number="102",
    name="Maternal and Child Ambulance",
    description=(
        "Free transport service for pregnant women and sick infants under national health schemes."
    ),
    verified_on=None,  # State availability must be verified
)

# National Health Information and Medical Advice Helpline
HELPLINE_HEALTH_INFO = Helpline(
    number="104",
    name="Health Information Helpline",
    description=(
        "Non-emergency health advice, information on government medical schemes, "
        "and blood bank availability."
    ),
    verified_on=None,  # State availability must be verified
)

# Tele-MANAS National Mental Health Crisis Helpline
HELPLINE_TELE_MANAS = Helpline(
    number="14416",
    name="Tele-MANAS",
    description=(
        "National Tele Mental Health Programme 24/7 toll-free mental health counseling "
        "and crisis support."
    ),
    verified_on=None,  # State availability must be verified
)


def get_emergency_helplines() -> list[Helpline]:
    """Return default emergency helplines for acute medical emergencies."""
    return [HELPLINE_NATIONAL_EMERGENCY, HELPLINE_AMBULANCE]


def get_crisis_helplines() -> list[Helpline]:
    """Return specialized crisis helplines for self-harm or mental health emergencies."""
    return [HELPLINE_TELE_MANAS, HELPLINE_NATIONAL_EMERGENCY]


def get_all_helplines() -> list[Helpline]:
    """Return all registered Indian national helplines."""
    return [
        HELPLINE_NATIONAL_EMERGENCY,
        HELPLINE_AMBULANCE,
        HELPLINE_MATERNAL_CHILD,
        HELPLINE_HEALTH_INFO,
        HELPLINE_TELE_MANAS,
    ]

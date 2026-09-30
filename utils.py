"""
utils.py – Shared utility functions for TestIQ.

Provides formatting helpers, colour mappings, and other small
functions used across the Streamlit UI and backend modules.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Colour / badge helpers (used by Streamlit UI)
# ---------------------------------------------------------------------------

_SEVERITY_COLOURS = {
    "Critical": "#dc2626",   # red-600
    "Major":    "#ea580c",   # orange-600
    "Minor":    "#ca8a04",   # yellow-600
    "Trivial":  "#16a34a",   # green-600
}

_STATUS_COLOURS = {
    "PASS":        "#16a34a",
    "FAIL":        "#dc2626",
    "BLOCKED":     "#ca8a04",
    "Not Run":     "#6b7280",
    "Open":        "#dc2626",
    "In Progress": "#ea580c",
    "Resolved":    "#2563eb",
    "Closed":      "#16a34a",
}

_PRIORITY_COLOURS = {
    "Critical": "#7c3aed",
    "High":     "#dc2626",
    "Medium":   "#ca8a04",
    "Low":      "#16a34a",
}


def get_severity_colour(severity: str) -> str:
    return _SEVERITY_COLOURS.get(severity, "#6b7280")


def get_status_colour(status: str) -> str:
    return _STATUS_COLOURS.get(status, "#6b7280")


def get_priority_colour(priority: str) -> str:
    return _PRIORITY_COLOURS.get(priority, "#6b7280")


def coloured_badge(label: str, colour: str) -> str:
    """Return an inline HTML badge (for use with st.markdown unsafe_allow_html)."""
    return (
        f'<span style="background:{colour};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.78rem;font-weight:600;">{label}</span>'
    )


def status_badge(status: str) -> str:
    return coloured_badge(status, get_status_colour(status))


def severity_badge(severity: str) -> str:
    return coloured_badge(severity, get_severity_colour(severity))


def priority_badge(priority: str) -> str:
    return coloured_badge(priority, get_priority_colour(priority))


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_datetime(iso_str: Optional[str]) -> str:
    """Convert an ISO datetime string to a human-readable format."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %Y, %H:%M")
    except ValueError:
        return iso_str


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text to max_len characters with an ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def pluralise(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Return 'N word' with correct singular/plural form."""
    word = singular if count == 1 else (plural or singular + "s")
    return f"{count} {word}"


# ---------------------------------------------------------------------------
# List / dict helpers
# ---------------------------------------------------------------------------

def safe_get(d: Dict[str, Any], key: str, default: Any = "") -> Any:
    """Return d[key] or default if missing / None."""
    val = d.get(key)
    return val if val is not None else default


def deduplicate(items: List[Any]) -> List[Any]:
    """Remove duplicates while preserving order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Pass-rate helpers
# ---------------------------------------------------------------------------

def calculate_pass_rate(passed: int, total: int) -> float:
    """Return pass rate as a percentage rounded to 1 decimal place."""
    if total <= 0:
        return 0.0
    return round(passed / total * 100, 1)


def quality_label(pass_rate: float) -> str:
    """Return a qualitative quality label based on pass rate."""
    if pass_rate >= 90:
        return "Excellent"
    if pass_rate >= 75:
        return "Good"
    if pass_rate >= 50:
        return "Fair"
    return "Poor"


# ---------------------------------------------------------------------------
# Sample data loader
# ---------------------------------------------------------------------------

SAMPLE_REQUIREMENT = {
    "title": "User Registration",
    "description": (
        "Users should be able to register with a valid name, email address "
        "and password. The system must validate all fields before creating "
        "the user account."
    ),
    "module": "Registration",
    "acceptance": (
        "- Name is required and must be at least 2 characters\n"
        "- Email must contain a valid format (user@domain.tld)\n"
        "- Password must contain at least 8 characters\n"
        "- Empty fields must be rejected with clear error messages\n"
        "- Duplicate email addresses must not be accepted"
    ),
}

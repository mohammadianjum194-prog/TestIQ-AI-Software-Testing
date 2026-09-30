"""
bug_analyzer.py – Defect detection and classification engine for TestIQ.

Whenever a test case execution results in FAIL, this module:
    1. Creates a structured defect record.
    2. Classifies the defect by Severity and Priority using rule-based logic.
    3. Returns the defect dict ready for database insertion.
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Defect ID generator (stateless, derived from test_id + timestamp)
# ---------------------------------------------------------------------------

def _generate_defect_id(test_id: str) -> str:
    """Generate a unique defect ID based on test_id and current timestamp."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_id = re.sub(r"[^A-Z0-9]", "", test_id.upper())[:10]
    return f"DEF-{safe_id}-{ts}"


# ---------------------------------------------------------------------------
# Classification engine
# ---------------------------------------------------------------------------

# Keyword rules for severity classification.
# Each tuple: (pattern_in_actual_result, pattern_in_expected_result, severity, priority)
_CLASSIFICATION_RULES = [
    # Security / authentication issues – Critical
    (r"password.*(short|length|bypass)",  None,            "Critical", "Critical"),
    (r"invalid.*accepted",                r"rejected|error","Critical", "Critical"),
    (r"sql.*inject|injection",            None,             "Critical", "Critical"),
    (r"authentication.*bypass",           None,             "Critical", "Critical"),

    # Required field not validated – Major
    (r"required.*empty|empty.*required|unexpectedly passed", r"required|error", "Major", "High"),
    (r"email.*(invalid|format|accepted)", r"rejected|error","Major",    "High"),
    (r"boundary.*(off|wrong|incorrect)",  None,             "Major",    "High"),
    (r"not submitted|form.*submit",       r"submit|success","Major",    "High"),

    # Validation logic failures – Minor
    (r"validation.*failed|error message", r"valid|accept",  "Minor",    "Medium"),
    (r"too (short|long).*unexpect",       None,             "Minor",    "Medium"),

    # Blocked / inconclusive – Trivial
    (r"blocked|not verifiable|no data",   None,             "Trivial",  "Low"),
]


def classify_defect(
    actual_result: str,
    expected_result: str,
    test_type: str = "",
) -> Dict[str, str]:
    """
    Classify a failed test's defect severity and priority.

    Returns a dict with keys: severity, priority.
    """
    actual_lower   = actual_result.lower()
    expected_lower = expected_result.lower()

    for actual_pat, expected_pat, severity, priority in _CLASSIFICATION_RULES:
        if re.search(actual_pat, actual_lower):
            if expected_pat is None or re.search(expected_pat, expected_lower):
                return {"severity": severity, "priority": priority}

    # Fallback based on test type
    type_defaults = {
        "negative":   ("Major",  "High"),
        "boundary":   ("Major",  "High"),
        "validation": ("Minor",  "Medium"),
        "positive":   ("Critical","Critical"),
    }
    sev, pri = type_defaults.get(test_type.lower(), ("Minor", "Medium"))
    return {"severity": sev, "priority": pri}


# ---------------------------------------------------------------------------
# Defect creator
# ---------------------------------------------------------------------------

def create_defect(test_result: Dict[str, Any], test_case: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Create a defect record from a failed test result.

    Returns None if the test did not fail.
    """
    if test_result.get("status") not in ("FAIL", "BLOCKED"):
        return None

    test_id        = test_result["test_id"]
    actual_result  = test_result.get("actual_result", "No details available.")
    expected_result= test_result.get("expected_result", "")
    test_type      = test_case.get("test_type", "") if test_case else ""

    classification = classify_defect(actual_result, expected_result, test_type)

    # Build defect title from the scenario or a generic label
    scenario = test_case.get("scenario", "") if test_case else ""
    if scenario:
        title = _derive_defect_title(scenario, actual_result, test_type)
    else:
        title = f"Defect found in {test_id}: unexpected outcome."

    description = (
        f"Test case '{test_id}' produced an unexpected result during execution.\n"
        f"Test Type: {test_type or 'Unknown'}\n"
        f"Scenario: {scenario or 'N/A'}\n\n"
        f"Root cause analysis required."
    )

    defect = {
        "defect_id":       _generate_defect_id(test_id),
        "test_id":         test_id,
        "title":           title,
        "description":     description,
        "expected_result": expected_result,
        "actual_result":   actual_result,
        "severity":        classification["severity"],
        "priority":        classification["priority"],
        "status":          "Open",
    }

    logger.info(
        "Defect created: %s | Severity: %s | Test: %s",
        defect["defect_id"], defect["severity"], test_id,
    )
    return defect


# ---------------------------------------------------------------------------
# Title derivation
# ---------------------------------------------------------------------------

def _derive_defect_title(scenario: str, actual_result: str, test_type: str) -> str:
    """
    Generate a concise defect title from the failing scenario.

    Trims the scenario to a readable title and prepends a defect type prefix.
    """
    # Trim scenario to 80 chars
    short_scenario = scenario[:80].rstrip()
    if len(scenario) > 80:
        short_scenario += "…"

    prefix_map = {
        "negative":   "[NEG]",
        "boundary":   "[BVA]",
        "validation": "[VAL]",
        "positive":   "[POS]",
    }
    prefix = prefix_map.get(test_type.lower(), "[DEFECT]")

    return f"{prefix} {short_scenario}"


# ---------------------------------------------------------------------------
# Defect summary statistics (used by dashboard)
# ---------------------------------------------------------------------------

def summarise_defects(defects: list) -> Dict[str, int]:
    """Return a dict of severity counts from a list of defect dicts."""
    summary = {"Critical": 0, "Major": 0, "Minor": 0, "Trivial": 0}
    for d in defects:
        sev = d.get("severity", "Minor")
        summary[sev] = summary.get(sev, 0) + 1
    return summary

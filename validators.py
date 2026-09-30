"""
validators.py – Reusable input validation functions for TestIQ.

Each validator returns a dict:
    {"valid": bool, "message": str}

These are called by test_executor.py to determine PASS/FAIL at runtime.
"""

import re
from typing import Any, Dict

from config import (
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)

# Pre-compiled email regex (RFC 5322 simplified, practical subset).
# Local part must not contain consecutive dots and must not start/end with a dot.
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9_%+\-]+([.][a-zA-Z0-9_%+\-]+)*@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


# ---------------------------------------------------------------------------
# Core validators
# ---------------------------------------------------------------------------

def validate_required(value: Any) -> Dict[str, Any]:
    """Fail if value is None, empty string, or whitespace-only."""
    if value is None or str(value).strip() == "":
        return {"valid": False, "message": "Field is required and cannot be empty."}
    return {"valid": True, "message": "Field is present."}


def validate_email(email: str) -> Dict[str, Any]:
    """Validate email format and length."""
    if not email or str(email).strip() == "":
        return {"valid": False, "message": "Email address is required."}
    email = str(email).strip()
    if len(email) > EMAIL_MAX_LENGTH:
        return {
            "valid": False,
            "message": f"Email must not exceed {EMAIL_MAX_LENGTH} characters.",
        }
    if not _EMAIL_RE.match(email):
        return {
            "valid": False,
            "message": "Email format is invalid. Expected: user@domain.tld",
        }
    return {"valid": True, "message": "Email format is valid."}


def validate_password(password: str) -> Dict[str, Any]:
    """Validate password meets minimum/maximum length requirements."""
    if not password:
        return {"valid": False, "message": "Password is required."}
    length = len(str(password))
    if length < PASSWORD_MIN_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Password is too short. Minimum length is "
                f"{PASSWORD_MIN_LENGTH} characters (got {length})."
            ),
        }
    if length > PASSWORD_MAX_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Password is too long. Maximum length is "
                f"{PASSWORD_MAX_LENGTH} characters (got {length})."
            ),
        }
    return {"valid": True, "message": "Password meets length requirements."}


def validate_name(name: str) -> Dict[str, Any]:
    """Validate that a name is non-empty and within allowed length range."""
    if not name or str(name).strip() == "":
        return {"valid": False, "message": "Name is required."}
    name = str(name).strip()
    if len(name) < NAME_MIN_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Name is too short. Minimum length is "
                f"{NAME_MIN_LENGTH} characters (got {len(name)})."
            ),
        }
    if len(name) > NAME_MAX_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Name is too long. Maximum length is "
                f"{NAME_MAX_LENGTH} characters (got {len(name)})."
            ),
        }
    return {"valid": True, "message": "Name is valid."}


def validate_numeric(value: Any) -> Dict[str, Any]:
    """Check that value can be interpreted as a number."""
    try:
        float(str(value))
        return {"valid": True, "message": "Value is numeric."}
    except (ValueError, TypeError):
        return {"valid": False, "message": f"Value '{value}' is not a valid number."}


def validate_range(value: Any, min_val: float, max_val: float) -> Dict[str, Any]:
    """Check that a numeric value falls within [min_val, max_val]."""
    result = validate_numeric(value)
    if not result["valid"]:
        return result
    num = float(str(value))
    if num < min_val or num > max_val:
        return {
            "valid": False,
            "message": (
                f"Value {num} is out of range. "
                f"Expected between {min_val} and {max_val}."
            ),
        }
    return {"valid": True, "message": f"Value {num} is within the valid range."}


def validate_string_length(value: str, min_len: int = 0,
                            max_len: int = 255) -> Dict[str, Any]:
    """Validate string length falls within [min_len, max_len]."""
    length = len(str(value))
    if length < min_len:
        return {
            "valid": False,
            "message": (
                f"Input is too short. Minimum {min_len} characters required "
                f"(got {length})."
            ),
        }
    if length > max_len:
        return {
            "valid": False,
            "message": (
                f"Input is too long. Maximum {max_len} characters allowed "
                f"(got {length})."
            ),
        }
    return {"valid": True, "message": "String length is valid."}


def validate_not_null(value: Any) -> Dict[str, Any]:
    """Fail only for None (not for empty string)."""
    if value is None:
        return {"valid": False, "message": "Value must not be null/None."}
    return {"valid": True, "message": "Value is not null."}


# ---------------------------------------------------------------------------
# Composite validator dispatcher
# ---------------------------------------------------------------------------

# Maps a rule keyword to the validator function + any extra kwargs.
_RULE_MAP = {
    "required":     (validate_required, {}),
    "email":        (validate_email, {}),
    "password":     (validate_password, {}),
    "name":         (validate_name, {}),
    "numeric":      (validate_numeric, {}),
    "not_null":     (validate_not_null, {}),
}


def run_validation(rule: str, value: Any, **kwargs) -> Dict[str, Any]:
    """
    Dispatch to the correct validator based on *rule* keyword.

    Extra keyword arguments (e.g. min_len, max_len, min_val, max_val)
    are forwarded to validators that accept them.
    """
    rule_lower = rule.lower().strip()

    if rule_lower == "range":
        min_val = float(kwargs.get("min_val", 0))
        max_val = float(kwargs.get("max_val", 100))
        return validate_range(value, min_val, max_val)

    if rule_lower == "string_length":
        min_len = int(kwargs.get("min_len", 0))
        max_len = int(kwargs.get("max_len", 255))
        return validate_string_length(str(value), min_len, max_len)

    if rule_lower in _RULE_MAP:
        fn, defaults = _RULE_MAP[rule_lower]
        return fn(value)

    # Unknown rule – treat as always passing to avoid false failures
    return {
        "valid": True,
        "message": f"No validator defined for rule '{rule}'. Skipped.",
    }

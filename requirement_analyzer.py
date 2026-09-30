"""
requirement_analyzer.py – Rule-based requirement analysis engine.

Parses a natural-language requirement description and extracts:
    - Detected input fields
    - Validation rules per field
    - Expected behaviours
    - Edge cases / boundary conditions
    - Possible defect areas

This module is the foundation that feeds test_generator.py.
"""

import re
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Keyword dictionaries
# ---------------------------------------------------------------------------

# Maps common field keywords to canonical field names
_FIELD_KEYWORDS: Dict[str, str] = {
    "name":         "name",
    "full name":    "name",
    "username":     "username",
    "user name":    "username",
    "email":        "email",
    "email address":"email",
    "mail":         "email",
    "password":     "password",
    "passphrase":   "password",
    "pin":          "pin",
    "phone":        "phone",
    "mobile":       "phone",
    "phone number": "phone",
    "age":          "age",
    "date":         "date",
    "date of birth":"date_of_birth",
    "dob":          "date_of_birth",
    "address":      "address",
    "city":         "city",
    "country":      "country",
    "zip":          "zip_code",
    "zip code":     "zip_code",
    "postal code":  "zip_code",
    "price":        "price",
    "amount":       "amount",
    "quantity":     "quantity",
    "description":  "description",
    "title":        "title",
    "message":      "message",
    "url":          "url",
    "website":      "url",
    "id":           "id",
    "user id":      "user_id",
}

# Validation rules implied by a given field name
_FIELD_RULES: Dict[str, List[str]] = {
    "name":          ["required", "name", "string_length:2:100"],
    "username":      ["required", "string_length:3:50"],
    "email":         ["required", "email"],
    "password":      ["required", "password"],
    "pin":           ["required", "numeric", "string_length:4:6"],
    "phone":         ["required", "numeric", "string_length:7:15"],
    "age":           ["required", "numeric", "range:0:150"],
    "date":          ["required"],
    "date_of_birth": ["required"],
    "address":       ["required", "string_length:5:200"],
    "city":          ["required", "string_length:2:100"],
    "country":       ["required", "string_length:2:60"],
    "zip_code":      ["required", "string_length:3:10"],
    "price":         ["required", "numeric", "range:0:1000000"],
    "amount":        ["required", "numeric"],
    "quantity":      ["required", "numeric", "range:1:9999"],
    "description":   ["string_length:0:1000"],
    "title":         ["required", "string_length:1:200"],
    "message":       ["required", "string_length:1:2000"],
    "url":           ["required"],
    "id":            ["required", "numeric"],
    "user_id":       ["required", "numeric"],
}

# Keywords that suggest a mandatory / required field
_REQUIRED_KEYWORDS = [
    "must", "required", "mandatory", "should", "need", "have to",
    "cannot be empty", "not empty", "needs", "compulsory",
]

# Keywords that suggest a boundary condition
_BOUNDARY_KEYWORDS = [
    "minimum", "maximum", "min", "max", "at least", "at most",
    "less than", "greater than", "between", "length", "characters",
    "limit", "range",
]

# Keywords that suggest a negative / invalid scenario
_NEGATIVE_KEYWORDS = [
    "invalid", "incorrect", "wrong", "not valid", "fail", "error",
    "should not", "must not", "cannot", "reject", "deny", "block",
]

# Module-type heuristics
_MODULE_KEYWORDS = {
    "registration": ["register", "sign up", "signup", "create account"],
    "login":        ["login", "sign in", "signin", "authenticate", "log in"],
    "profile":      ["profile", "update user", "edit user"],
    "payment":      ["pay", "payment", "checkout", "purchase", "transaction"],
    "search":       ["search", "find", "filter", "query"],
    "upload":       ["upload", "file", "attach", "document"],
    "reset":        ["reset", "forgot", "recover", "password reset"],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_requirement(
    title: str,
    description: str,
    module: str = "",
    acceptance: str = "",
) -> Dict[str, Any]:
    """
    Perform rule-based analysis of a software requirement.

    Returns a structured dict consumed by test_generator.py.
    """
    text = f"{title} {description} {acceptance}".lower()

    detected_fields = _detect_fields(text)
    validation_rules = _build_validation_rules(detected_fields, text, acceptance)
    expected_behaviours = _derive_expected_behaviours(description, detected_fields)
    edge_cases = _derive_edge_cases(detected_fields, text)
    boundary_conditions = _derive_boundary_conditions(text, detected_fields)
    potential_defects = _derive_potential_defects(detected_fields, text)
    module_type = _detect_module_type(text) or module or "General"

    return {
        "title": title,
        "description": description,
        "module": module_type,
        "acceptance_criteria": acceptance,
        "detected_fields": detected_fields,
        "validation_rules": validation_rules,
        "expected_behaviours": expected_behaviours,
        "edge_cases": edge_cases,
        "boundary_conditions": boundary_conditions,
        "potential_defects": potential_defects,
        "test_scope": _determine_test_scope(text),
        "risk_level": _assess_risk(detected_fields, text),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_fields(text: str) -> List[str]:
    """Return canonical field names found in the requirement text."""
    found = []
    for keyword, canonical in _FIELD_KEYWORDS.items():
        if keyword in text and canonical not in found:
            found.append(canonical)
    # Guarantee at least one field so generators always produce output
    if not found:
        found.append("input")
    return found


def _build_validation_rules(
    fields: List[str],
    text: str,
    acceptance: str,
) -> Dict[str, List[str]]:
    """Map each detected field to its validation rules."""
    rules: Dict[str, List[str]] = {}

    for field in fields:
        base_rules = list(_FIELD_RULES.get(field, ["required"]))

        # Augment from acceptance criteria text
        acc_lower = acceptance.lower()
        if field == "password":
            # Look for explicit minimum-length mentions
            match = re.search(r"(\d+)\s*characters?", acc_lower)
            if match:
                min_len = int(match.group(1))
                # Replace the generic password rule with a specific one
                base_rules = [
                    r for r in base_rules
                    if not r.startswith("string_length")
                ]
                base_rules.append(f"string_length:{min_len}:128")

        rules[field] = base_rules

    return rules


def _derive_expected_behaviours(description: str, fields: List[str]) -> List[str]:
    """Produce a human-readable list of expected system behaviours."""
    behaviours = [
        f"System accepts valid input for all required fields: "
        f"{', '.join(fields)}.",
        "System displays a meaningful error message for each validation failure.",
        "System prevents form submission when required fields are empty.",
    ]

    desc_lower = description.lower()

    if "register" in desc_lower or "sign up" in desc_lower:
        behaviours.append("User is successfully registered when all inputs are valid.")
        behaviours.append("Duplicate email/username is rejected with a clear message.")

    if "login" in desc_lower or "sign in" in desc_lower:
        behaviours.append("User is authenticated when credentials are correct.")
        behaviours.append("Authentication fails with incorrect credentials.")

    if "email" in fields:
        behaviours.append("Email format is validated before submission.")

    if "password" in fields:
        behaviours.append(
            "Password length is enforced (minimum / maximum constraints)."
        )

    return behaviours


def _derive_edge_cases(fields: List[str], text: str) -> List[str]:
    """Generate edge-case scenarios based on field types."""
    cases = [
        "All fields left empty at once.",
        "Only whitespace entered in required text fields.",
        "Extremely long strings injected into text fields.",
    ]

    if "email" in fields:
        cases += [
            "Email with no @ symbol.",
            "Email with no domain (user@).",
            "Email with no TLD (user@domain).",
            "Email with consecutive dots (user..name@domain.com).",
            "SQL injection attempt in email field.",
        ]

    if "password" in fields:
        cases += [
            "Password exactly at the minimum boundary length.",
            "Password one character below the minimum length.",
            "Password with only spaces.",
            "Password at maximum allowed length.",
        ]

    if "name" in fields:
        cases += [
            "Name with only a single character.",
            "Name with special characters or numbers.",
            "Name with leading/trailing spaces.",
        ]

    if "phone" in fields:
        cases += [
            "Phone number with non-numeric characters.",
            "Phone number with too few digits.",
        ]

    return cases


def _derive_boundary_conditions(text: str, fields: List[str]) -> List[str]:
    """Identify boundary values based on detected fields and rules."""
    conditions = []

    if "password" in fields:
        conditions += [
            "Password length = minimum boundary (e.g. 8 characters) → PASS",
            "Password length = minimum − 1 (e.g. 7 characters) → FAIL",
            "Password length = maximum boundary → PASS",
            "Password length = maximum + 1 → FAIL",
        ]

    if "name" in fields:
        conditions += [
            "Name length = minimum boundary (2 characters) → PASS",
            "Name length = minimum − 1 (1 character) → FAIL",
            "Name length = maximum boundary (100 characters) → PASS",
        ]

    if "age" in fields:
        conditions += [
            "Age = 0 → PASS (boundary minimum)",
            "Age = 150 → PASS (boundary maximum)",
            "Age = −1 → FAIL",
            "Age = 151 → FAIL",
        ]

    if "quantity" in fields:
        conditions += [
            "Quantity = 1 → PASS (minimum)",
            "Quantity = 0 → FAIL",
            "Quantity = 9999 → PASS (maximum)",
            "Quantity = 10000 → FAIL",
        ]

    if not conditions:
        conditions.append("No specific numeric boundary conditions detected.")

    return conditions


def _derive_potential_defects(fields: List[str], text: str) -> List[str]:
    """List likely defect areas based on the requirement."""
    defects = [
        "Missing required-field validation on empty submission.",
        "Inadequate or missing error messages for invalid inputs.",
    ]

    if "email" in fields:
        defects.append("Invalid email formats incorrectly accepted.")

    if "password" in fields:
        defects += [
            "Passwords shorter than minimum length accepted.",
            "Password length boundary off-by-one error.",
        ]

    if "name" in fields:
        defects.append("Empty or whitespace-only names accepted.")

    if "phone" in fields:
        defects.append("Non-numeric phone numbers accepted.")

    defects += [
        "SQL injection not sanitised in input fields.",
        "Duplicate records allowed due to missing uniqueness check.",
    ]

    return defects


def _detect_module_type(text: str) -> str:
    """Infer the functional module from the requirement text."""
    for module_name, keywords in _MODULE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return module_name.title()
    return ""


def _determine_test_scope(text: str) -> List[str]:
    """Return the types of testing recommended for this requirement."""
    scope = ["Functional Testing", "Boundary Value Analysis", "Negative Testing"]
    if any(kw in text for kw in ["ui", "interface", "display", "screen", "button"]):
        scope.append("UI / Usability Testing")
    if any(kw in text for kw in ["performance", "load", "speed", "concurrent"]):
        scope.append("Performance Testing")
    if any(kw in text for kw in ["security", "auth", "password", "token", "session"]):
        scope.append("Security Testing")
    return scope


def _assess_risk(fields: List[str], text: str) -> str:
    """Return a qualitative risk level for the requirement."""
    high_risk_fields = {"password", "email", "payment", "amount", "price"}
    if any(f in high_risk_fields for f in fields):
        return "High"
    if len(fields) > 4:
        return "Medium"
    return "Low"

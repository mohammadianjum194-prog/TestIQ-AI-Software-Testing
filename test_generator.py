"""
test_generator.py – Structured test-case generator for TestIQ.

Converts a requirement-analysis dict (from ai_engine / requirement_analyzer)
into a list of test-case dicts ready to be stored in SQLite and executed.

Each test case covers one of four test types:
    Positive   – valid, happy-path input
    Negative   – invalid input that should be rejected
    Boundary   – values at the exact edge of allowed ranges
    Validation – field-level format / constraint checks
"""

from typing import Any, Dict, List

from config import PRIORITY_LEVELS


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_test_cases(
    analysis: Dict[str, Any],
    requirement_id: int,
) -> List[Dict[str, Any]]:
    """
    Generate a complete test-case suite from a requirement analysis.

    Parameters
    ----------
    analysis       : dict returned by ai_engine.ai_analyze_requirement()
    requirement_id : SQLite row id of the parent requirement

    Returns
    -------
    List of test-case dicts (not yet persisted to the database).
    """
    test_cases: List[Dict[str, Any]] = []
    counter = _get_counter(requirement_id)

    fields: List[str] = analysis.get("detected_fields", ["input"])
    validation_rules: Dict[str, List[str]] = analysis.get("validation_rules", {})

    # --- Positive tests -------------------------------------------------
    test_cases.extend(
        _generate_positive_tests(fields, validation_rules, requirement_id, counter)
    )
    counter[0] += len(test_cases)

    # --- Negative tests -------------------------------------------------
    neg = _generate_negative_tests(
        fields, validation_rules, requirement_id, counter
    )
    test_cases.extend(neg)
    counter[0] += len(neg)

    # --- Boundary tests -------------------------------------------------
    bnd = _generate_boundary_tests(fields, validation_rules, requirement_id, counter)
    test_cases.extend(bnd)
    counter[0] += len(bnd)

    # --- Validation tests -----------------------------------------------
    val = _generate_validation_tests(fields, validation_rules, requirement_id, counter)
    test_cases.extend(val)

    return test_cases


# ---------------------------------------------------------------------------
# Test type generators
# ---------------------------------------------------------------------------

def _generate_positive_tests(
    fields: List[str],
    rules: Dict[str, List[str]],
    req_id: int,
    counter: List[int],
) -> List[Dict[str, Any]]:
    tests = []

    # One master "all-valid-inputs" positive test
    sample_data = _build_valid_sample(fields)
    tests.append(
        _make_tc(
            counter,
            req_id,
            scenario=f"Submit form with all valid inputs for: {', '.join(fields)}",
            preconditions="Application is running and the form is accessible.",
            test_data=sample_data,
            expected="Form submission succeeds; system accepts valid data and "
                     "completes the operation successfully.",
            test_type="Positive",
            priority="Critical",
        )
    )

    # One positive test per field
    for field in fields:
        tests.append(
            _make_tc(
                counter,
                req_id,
                scenario=f"Provide valid value for field '{field}'",
                preconditions="Form is accessible.",
                test_data=f"{field}: {_valid_value(field)}",
                expected=f"'{field}' field accepts the valid value without error.",
                test_type="Positive",
                priority="High",
            )
        )

    return tests


def _generate_negative_tests(
    fields: List[str],
    rules: Dict[str, List[str]],
    req_id: int,
    counter: List[int],
) -> List[Dict[str, Any]]:
    tests = []

    for field in fields:
        field_rules = rules.get(field, [])

        # Empty / missing field
        tests.append(
            _make_tc(
                counter,
                req_id,
                scenario=f"Submit form with '{field}' field left empty",
                preconditions="Form is accessible.",
                test_data=f"{field}: ''  (empty string)",
                expected=f"Validation error: '{field}' is required.",
                test_type="Negative",
                priority="High",
            )
        )

        # Field-specific negative cases
        if "email" in field_rules or field == "email":
            tests.append(
                _make_tc(
                    counter,
                    req_id,
                    scenario="Submit form with an improperly formatted email address",
                    preconditions="Form is accessible.",
                    test_data=f"{field}: 'notanemail'",
                    expected="Validation error: email format is invalid.",
                    test_type="Negative",
                    priority="High",
                )
            )
            tests.append(
                _make_tc(
                    counter,
                    req_id,
                    scenario="Submit form with email missing the domain part",
                    preconditions="Form is accessible.",
                    test_data=f"{field}: 'user@'",
                    expected="Validation error: email format is invalid.",
                    test_type="Negative",
                    priority="Medium",
                )
            )

        if "password" in field_rules or field == "password":
            tests.append(
                _make_tc(
                    counter,
                    req_id,
                    scenario="Submit form with password that is too short",
                    preconditions="Form is accessible.",
                    test_data=f"{field}: 'abc'  (3 characters)",
                    expected="Validation error: password does not meet minimum "
                             "length requirement.",
                    test_type="Negative",
                    priority="Critical",
                )
            )

        if "name" in field_rules or field == "name":
            tests.append(
                _make_tc(
                    counter,
                    req_id,
                    scenario="Submit form with name consisting only of whitespace",
                    preconditions="Form is accessible.",
                    test_data=f"{field}: '   '  (spaces only)",
                    expected="Validation error: name cannot be empty or whitespace.",
                    test_type="Negative",
                    priority="High",
                )
            )

    # All-empty submission
    tests.append(
        _make_tc(
            counter,
            req_id,
            scenario="Submit the form with all fields left completely empty",
            preconditions="Form is accessible.",
            test_data="All fields: '' (empty)",
            expected="Multiple validation errors displayed; form not submitted.",
            test_type="Negative",
            priority="Critical",
        )
    )

    return tests


def _generate_boundary_tests(
    fields: List[str],
    rules: Dict[str, List[str]],
    req_id: int,
    counter: List[int],
) -> List[Dict[str, Any]]:
    tests = []

    if "password" in fields:
        tests += [
            _make_tc(
                counter, req_id,
                scenario="Submit password at exactly the minimum allowed length (8 chars)",
                preconditions="Form is accessible.",
                test_data="password: 'Abcde123'  (8 characters)",
                expected="Password accepted; no validation error.",
                test_type="Boundary",
                priority="Critical",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit password one character below the minimum length (7 chars)",
                preconditions="Form is accessible.",
                test_data="password: 'Abcde12'  (7 characters)",
                expected="Validation error: password too short.",
                test_type="Boundary",
                priority="Critical",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit password at exactly the maximum allowed length (128 chars)",
                preconditions="Form is accessible.",
                test_data="password: 'A' * 128",
                expected="Password accepted; no validation error.",
                test_type="Boundary",
                priority="High",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit password one character above the maximum length (129 chars)",
                preconditions="Form is accessible.",
                test_data="password: 'A' * 129",
                expected="Validation error: password too long.",
                test_type="Boundary",
                priority="High",
            ),
        ]

    if "name" in fields:
        tests += [
            _make_tc(
                counter, req_id,
                scenario="Submit name at exactly the minimum length (2 characters)",
                preconditions="Form is accessible.",
                test_data="name: 'Jo'  (2 characters)",
                expected="Name accepted.",
                test_type="Boundary",
                priority="Medium",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit name with only 1 character (below minimum)",
                preconditions="Form is accessible.",
                test_data="name: 'J'  (1 character)",
                expected="Validation error: name is too short.",
                test_type="Boundary",
                priority="Medium",
            ),
        ]

    if "age" in fields:
        tests += [
            _make_tc(
                counter, req_id,
                scenario="Submit age = 0 (minimum boundary)",
                preconditions="Form is accessible.",
                test_data="age: 0",
                expected="Age accepted.",
                test_type="Boundary",
                priority="Medium",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit age = 150 (maximum boundary)",
                preconditions="Form is accessible.",
                test_data="age: 150",
                expected="Age accepted.",
                test_type="Boundary",
                priority="Medium",
            ),
            _make_tc(
                counter, req_id,
                scenario="Submit age = -1 (below minimum boundary)",
                preconditions="Form is accessible.",
                test_data="age: -1",
                expected="Validation error: age is out of valid range.",
                test_type="Boundary",
                priority="Medium",
            ),
        ]

    if not tests:
        # Generic boundary test when no numeric fields detected
        tests.append(
            _make_tc(
                counter, req_id,
                scenario="Submit input at the boundary of maximum allowed length",
                preconditions="Form is accessible.",
                test_data="input: string of 255 characters",
                expected="System handles maximum-length input without crashing.",
                test_type="Boundary",
                priority="Medium",
            )
        )

    return tests


def _generate_validation_tests(
    fields: List[str],
    rules: Dict[str, List[str]],
    req_id: int,
    counter: List[int],
) -> List[Dict[str, Any]]:
    tests = []

    if "email" in fields:
        for invalid_email, note in [
            ("plainaddress",          "missing @ and domain"),
            ("@nodomain.com",         "missing local part"),
            ("user@.com",             "domain starts with dot"),
            ("user@domain",           "missing TLD"),
            ("user @domain.com",      "space in local part"),
        ]:
            tests.append(
                _make_tc(
                    counter, req_id,
                    scenario=f"Email validation: '{invalid_email}' ({note})",
                    preconditions="Email field is visible.",
                    test_data=f"email: '{invalid_email}'",
                    expected="Validation error displayed; email rejected.",
                    test_type="Validation",
                    priority="High",
                )
            )

    if "password" in fields:
        tests.append(
            _make_tc(
                counter, req_id,
                scenario="Password validation: only whitespace characters",
                preconditions="Password field is visible.",
                test_data="password: '        '  (8 spaces)",
                expected="Validation error: password cannot be only whitespace.",
                test_type="Validation",
                priority="High",
            )
        )

    # Required-field validation for each field
    for field in fields:
        tests.append(
            _make_tc(
                counter, req_id,
                scenario=f"Required field check: '{field}' must not be null or empty",
                preconditions="Form is accessible.",
                test_data=f"{field}: None / null",
                expected=f"Validation error: '{field}' is required.",
                test_type="Validation",
                priority="High",
            )
        )

    return tests


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_counter(requirement_id: int) -> List[int]:
    """Return a mutable counter list seeded from the requirement id."""
    return [1]


def _make_tc(
    counter: List[int],
    req_id: int,
    scenario: str,
    preconditions: str,
    test_data: str,
    expected: str,
    test_type: str,
    priority: str,
) -> Dict[str, Any]:
    """Construct a single test-case dict and increment the counter."""
    tc = {
        "requirement_id": req_id,
        "test_id":         f"TC-{req_id:03d}-{counter[0]:03d}",
        "scenario":        scenario,
        "preconditions":   preconditions,
        "test_data":       test_data,
        "expected_result": expected,
        "test_type":       test_type,
        "priority":        priority,
        "status":          "Not Run",
    }
    counter[0] += 1
    return tc


def _valid_value(field: str) -> str:
    """Return a representative valid sample value for a given field name."""
    defaults = {
        "name":          "Jane Smith",
        "username":      "jane_smith",
        "email":         "jane.smith@example.com",
        "password":      "SecurePass1!",
        "phone":         "9876543210",
        "age":           "25",
        "date":          "2024-01-15",
        "date_of_birth": "1998-06-20",
        "address":       "123 Main Street, Springfield",
        "city":          "Springfield",
        "country":       "United States",
        "zip_code":      "12345",
        "price":         "99.99",
        "amount":        "500",
        "quantity":      "3",
        "description":   "Sample description text.",
        "title":         "Sample Title",
        "message":       "Hello, this is a test message.",
        "url":           "https://example.com",
        "id":            "1001",
        "user_id":       "42",
        "input":         "ValidInput123",
    }
    return defaults.get(field, f"valid_{field}_value")


def _build_valid_sample(fields: List[str]) -> str:
    """Build a comma-separated test-data string with valid values for all fields."""
    parts = [f"{f}: {_valid_value(f)}" for f in fields]
    return ";  ".join(parts)

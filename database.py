"""
database.py – SQLite persistence layer for TestIQ.

Handles schema creation and all CRUD operations.
Uses parameterised queries throughout to prevent SQL injection.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import DB_PATH

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

@contextmanager
def get_connection():
    """Yield a SQLite connection with row_factory set to Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS requirements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL,
                module      TEXT    DEFAULT '',
                acceptance  TEXT    DEFAULT '',
                status      TEXT    DEFAULT 'Active',
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_cases (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id  INTEGER NOT NULL REFERENCES requirements(id),
                test_id         TEXT    NOT NULL UNIQUE,
                scenario        TEXT    NOT NULL,
                preconditions   TEXT    DEFAULT '',
                test_data       TEXT    DEFAULT '',
                expected_result TEXT    NOT NULL,
                test_type       TEXT    NOT NULL,
                priority        TEXT    NOT NULL,
                status          TEXT    DEFAULT 'Not Run',
                created_at      TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id    INTEGER NOT NULL REFERENCES test_cases(id),
                test_id         TEXT    NOT NULL,
                input_data      TEXT    DEFAULT '',
                expected_result TEXT    NOT NULL,
                actual_result   TEXT    NOT NULL,
                status          TEXT    NOT NULL,
                execution_time  REAL    DEFAULT 0.0,
                executed_at     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS defects (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_id       TEXT    NOT NULL UNIQUE,
                test_id         TEXT    NOT NULL,
                title           TEXT    NOT NULL,
                description     TEXT    NOT NULL,
                expected_result TEXT    NOT NULL,
                actual_result   TEXT    NOT NULL,
                severity        TEXT    NOT NULL,
                priority        TEXT    NOT NULL,
                status          TEXT    DEFAULT 'Open',
                created_at      TEXT    NOT NULL
            );
        """)
    logger.info("Database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------

def insert_requirement(title: str, description: str, module: str = "",
                        acceptance: str = "") -> int:
    """Insert a new requirement and return its row id."""
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO requirements (title, description, module, acceptance, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, description, module, acceptance, now),
        )
        return cur.lastrowid


def get_all_requirements() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM requirements ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_requirement_by_id(req_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM requirements WHERE id = ?", (req_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_requirement(req_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM requirements WHERE id = ?", (req_id,))


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def insert_test_case(tc: Dict[str, Any]) -> int:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO test_cases
               (requirement_id, test_id, scenario, preconditions, test_data,
                expected_result, test_type, priority, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tc["requirement_id"], tc["test_id"], tc["scenario"],
                tc.get("preconditions", ""), tc.get("test_data", ""),
                tc["expected_result"], tc["test_type"], tc["priority"],
                tc.get("status", "Not Run"), now,
            ),
        )
        return cur.lastrowid


def get_test_cases_by_requirement(req_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_cases WHERE requirement_id = ? ORDER BY test_id",
            (req_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_test_cases() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_cases ORDER BY test_id"
        ).fetchall()
    return [dict(r) for r in rows]


def update_test_case_status(test_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE test_cases SET status = ? WHERE test_id = ?",
            (status, test_id),
        )


def delete_test_case(test_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM test_cases WHERE test_id = ?", (test_id,))


# ---------------------------------------------------------------------------
# Test results
# ---------------------------------------------------------------------------

def insert_test_result(result: Dict[str, Any]) -> int:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO test_results
               (test_case_id, test_id, input_data, expected_result,
                actual_result, status, execution_time, executed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.get("test_case_id", 0),
                result["test_id"],
                result.get("input_data", ""),
                result["expected_result"],
                result["actual_result"],
                result["status"],
                result.get("execution_time", 0.0),
                now,
            ),
        )
        return cur.lastrowid


def get_all_test_results() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_results ORDER BY executed_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_test_results_by_test_id(test_id: str) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_results WHERE test_id = ? ORDER BY executed_at DESC",
            (test_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Defects
# ---------------------------------------------------------------------------

def insert_defect(defect: Dict[str, Any]) -> int:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO defects
               (defect_id, test_id, title, description, expected_result,
                actual_result, severity, priority, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                defect["defect_id"], defect["test_id"], defect["title"],
                defect["description"], defect["expected_result"],
                defect["actual_result"], defect["severity"],
                defect["priority"], defect.get("status", "Open"), now,
            ),
        )
        return cur.lastrowid


def get_all_defects() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM defects ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_defect_status(defect_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE defects SET status = ? WHERE defect_id = ?",
            (status, defect_id),
        )


# ---------------------------------------------------------------------------
# Dashboard aggregates
# ---------------------------------------------------------------------------

def get_dashboard_metrics() -> Dict[str, Any]:
    """Return a single dict of all KPIs used on the dashboard."""
    with get_connection() as conn:
        total_req = conn.execute(
            "SELECT COUNT(*) FROM requirements"
        ).fetchone()[0]
        total_tc = conn.execute(
            "SELECT COUNT(*) FROM test_cases"
        ).fetchone()[0]
        passed = conn.execute(
            "SELECT COUNT(*) FROM test_results WHERE status='PASS'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM test_results WHERE status='FAIL'"
        ).fetchone()[0]
        blocked = conn.execute(
            "SELECT COUNT(*) FROM test_results WHERE status='BLOCKED'"
        ).fetchone()[0]
        total_exec = passed + failed + blocked
        pass_rate = round(passed / total_exec * 100, 1) if total_exec > 0 else 0.0

        defects = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM defects GROUP BY severity"
        ).fetchall()
        sev_map = {row["severity"]: row["cnt"] for row in defects}

    return {
        "total_requirements": total_req,
        "total_test_cases": total_tc,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "total_executed": total_exec,
        "pass_rate": pass_rate,
        "total_defects": sum(sev_map.values()),
        "critical_defects": sev_map.get("Critical", 0),
        "major_defects": sev_map.get("Major", 0),
        "minor_defects": sev_map.get("Minor", 0),
        "trivial_defects": sev_map.get("Trivial", 0),
    }

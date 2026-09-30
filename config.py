"""
config.py – Central configuration for TestIQ.

Loads settings from environment variables (via .env) with sensible defaults
so the application runs fully offline without any API key.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists (silently ignored if absent)
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "testiq.db"

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME = "TestIQ"
APP_SUBTITLE = "AI-Powered Software Testing & Intelligent Automation Platform"
APP_VERSION = "1.0.0"
APP_AUTHOR = "TestIQ"

# ---------------------------------------------------------------------------
# AI / LLM settings
# ---------------------------------------------------------------------------
# Set OPENAI_API_KEY (or GEMINI_API_KEY) in your .env to enable AI features.
# Leave blank to use the deterministic rule-based engine (default).
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
AI_MODEL: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")  # openai | gemini | none

# Derived flag – True only when a key is actually present
AI_ENABLED: bool = bool(OPENAI_API_KEY or GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Validation thresholds
# ---------------------------------------------------------------------------
PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_MAX_LENGTH: int = int(os.getenv("PASSWORD_MAX_LENGTH", "128"))
NAME_MIN_LENGTH: int = int(os.getenv("NAME_MIN_LENGTH", "2"))
NAME_MAX_LENGTH: int = int(os.getenv("NAME_MAX_LENGTH", "100"))
EMAIL_MAX_LENGTH: int = int(os.getenv("EMAIL_MAX_LENGTH", "254"))

# ---------------------------------------------------------------------------
# Test execution settings
# ---------------------------------------------------------------------------
MAX_TEST_CASES_PER_REQUIREMENT: int = 20
DEFAULT_TEST_PRIORITY = "Medium"
DEFAULT_TEST_STATUS = "Not Run"

# ---------------------------------------------------------------------------
# Severity / priority mappings (used by defect classifier)
# ---------------------------------------------------------------------------
SEVERITY_LEVELS = ["Critical", "Major", "Minor", "Trivial"]
PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"]
TEST_TYPES = ["Positive", "Negative", "Boundary", "Validation"]
DEFECT_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
TEST_STATUSES = ["Not Run", "PASS", "FAIL", "BLOCKED"]

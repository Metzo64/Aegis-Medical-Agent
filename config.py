"""
Configuration settings and constants for the Hospital RL Access Control project.
Loads environment variables safely and defines system-wide constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Server Settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# RL Model Storage Paths
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = BASE_DIR / os.getenv("MODEL_PATH", "models/q_table.json")
METADATA_PATH = MODEL_DIR / "agent_metadata.json"
TRAINING_METRICS_PATH = MODEL_DIR / "training_metrics.json"

# Ensure models directory exists
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Supabase Table Names specified by the project requirements
REQUIRED_TABLES = [
    "users",
    "patients",
    "medical_records",
    "departments",
    "access_requests",
    "rl_decisions",
    "audit_logs"
]

# Action Space (Tabular Q-Learning)
# Requirement 9: ALLOW, DENY, CHALLENGE, RESTRICT
ACTIONS = ["ALLOW", "DENY", "CHALLENGE", "RESTRICT"]
ACTION_ALLOW = 0
ACTION_DENY = 1
ACTION_CHALLENGE = 2
ACTION_RESTRICT = 3

ACTION_NAMES = {
    ACTION_ALLOW: "ALLOW",
    ACTION_DENY: "DENY",
    ACTION_CHALLENGE: "CHALLENGE",
    ACTION_RESTRICT: "RESTRICT"
}

ACTION_DESCRIPTIONS = {
    "ALLOW": "Grant immediate full access to requested patient record.",
    "DENY": "Block request immediately to preserve security and confidentiality.",
    "CHALLENGE": "Step-up verification (e.g. 2FA / Biometric / Supervisor OTP).",
    "RESTRICT": "Grant limited/masked view (e.g. vital signs only, anonymized PII)."
}

# Observation Feature Encoding Dictionaries for State Discretization
ROLES = ["DOCTOR", "NURSE", "STAFF", "RESEARCHER"]
ROLE_MAP = {role: idx for idx, role in enumerate(ROLES)}

SENSITIVITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL_VIP"]
SENSITIVITY_MAP = {s: idx for idx, s in enumerate(SENSITIVITIES)}

LOCATIONS = ["INTERNAL_HOSPITAL", "VPN_OFFSITE", "EXTERNAL_UNKNOWN"]
LOCATION_MAP = {loc: idx for idx, loc in enumerate(LOCATIONS)}

FREQUENCIES = ["NORMAL", "ELEVATED", "BURST_HIGH"]  # <=5 req/min, 6-20 req/min, >20 req/min
FREQUENCY_MAP = {freq: idx for idx, freq in enumerate(FREQUENCIES)}

REQUEST_TIMES = ["NORMAL_HOURS", "OFF_HOURS"]
TIME_MAP = {t: idx for idx, t in enumerate(REQUEST_TIMES)}

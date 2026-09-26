"""
Application Configuration and Constants.
"""
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_FILE = BASE_DIR / "misa_profile.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Initial seed data specified by the trial contract
INITIAL_PROFILE = {
    "displayName": "Nova",
    "bio": "Music, late nights, and things I make.",
    "link": {
        "label": "My website",
        "url": "https://example.com"
    }
}

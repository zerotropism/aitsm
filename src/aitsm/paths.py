"""Filesystem locations, resolved from the installed package rather than the current directory."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ENV_FILE = PROJECT_ROOT / ".env"
DATABASE_FILE = PROJECT_ROOT / "aitsm.db"

"""Run the seeding scripts in order, each in its own process.

Separate processes matter: seed_system_user writes MCP_SYSTEM_USER_ID into .env, and the
scripts that follow must read it back. A single process would keep the settings it loaded
at import time.
"""

import subprocess
import sys

STEPS = (
    ("aitsm.scripts.init_db", "Database init"),
    ("aitsm.scripts.seed_admin", "Admin user"),
    ("aitsm.scripts.seed_system_user", "System user"),
    ("aitsm.scripts.seed_data", "Sample data"),
)


def run(module: str, label: str) -> None:
    print(f"\n── {label} ──")
    result = subprocess.run([sys.executable, "-m", module], check=False)
    if result.returncode != 0:
        print(f"ERROR: {module} failed (exit {result.returncode})")
        sys.exit(result.returncode)


def main() -> None:
    from aitsm.paths import ENV_FILE

    if not ENV_FILE.exists():
        print(f"No {ENV_FILE} found. Copy .env.example and set SECRET_KEY (32 characters minimum).")
        sys.exit(1)

    for module, label in STEPS:
        run(module, label)

    print("\n✓ Bootstrap complete.")
    print("  → API :  uv run aitsm-api")
    print("  → MCP :  uv run aitsm-mcp")


if __name__ == "__main__":
    main()

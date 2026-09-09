import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {**os.environ, "PYTHONPATH": ROOT}


def run(script: str, label: str):
    print(f"\n── {label} ──")
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", script)],
        env=env,
    )
    if result.returncode != 0:
        print(f"ERROR: {script} failed (exit {result.returncode})")
        sys.exit(result.returncode)


run("init_db.py", "Database init")
run("seed_admin.py", "Admin user")
run("seed_system_user.py", "System user")
run("seed_data.py", "Sample data")

print("\n✓ Bootstrap complete.")
print("  → API :  uv run uvicorn main:app --reload")
print("  → MCP :  PYTHONPATH=. uv run fastmcp dev mcp/server.py")

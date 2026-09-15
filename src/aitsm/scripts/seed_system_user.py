import re

from aitsm.core.database import SessionLocal
from aitsm.core.security import hash_password
from aitsm.models.user import User
from aitsm.paths import ENV_FILE

db = SessionLocal()

existing = db.query(User).filter(User.email == "system@aitsm.local").first()
if existing:
    user_id = existing.id
    print(f"System user already exists: {user_id}")
else:
    u = User(
        email="system@aitsm.local",
        hashed_password=hash_password("not-used"),
        full_name="System",
        role="agent",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    user_id = u.id
    print(f"Created system user: {user_id}")

# Auto-update .env with system user ID for use in MCP actions
if ENV_FILE.exists():
    content = ENV_FILE.read_text()
    if re.search(r"^MCP_SYSTEM_USER_ID=", content, re.MULTILINE):
        content = re.sub(
            r"^MCP_SYSTEM_USER_ID=.*$",
            f"MCP_SYSTEM_USER_ID={user_id}",
            content,
            flags=re.MULTILINE,
        )
    else:
        content += f"\nMCP_SYSTEM_USER_ID={user_id}"
    ENV_FILE.write_text(content)
    print(f".env updated: MCP_SYSTEM_USER_ID={user_id}")
else:
    print(f"WARNING: .env not found — add manually: MCP_SYSTEM_USER_ID={user_id}")

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.security import hash_password
from models import (
    user,
    ticket,
    kb_article,
    service_catalog,
    change,
    ticket_comment,
    kb_feedback,
)  # noqa
from models.user import User

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
env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        content = f.read()
    if re.search(r"^MCP_SYSTEM_USER_ID=", content, re.MULTILINE):
        content = re.sub(
            r"^MCP_SYSTEM_USER_ID=.*$",
            f"MCP_SYSTEM_USER_ID={user_id}",
            content,
            flags=re.MULTILINE,
        )
    else:
        content += f"\nMCP_SYSTEM_USER_ID={user_id}"
    with open(env_path, "w") as f:
        f.write(content)
    print(f".env updated: MCP_SYSTEM_USER_ID={user_id}")
else:
    print(f"WARNING: .env not found — add manually: MCP_SYSTEM_USER_ID={user_id}")

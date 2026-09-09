import secrets
import sys

from core.database import SessionLocal
from core.security import hash_password
from models.user import User

db = SessionLocal()
email = sys.argv[1] if len(sys.argv) > 1 else "admin@aitsm.local"
password = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(16)

existing = db.query(User).filter(User.email == email).first()
if existing:
    existing.role = "admin"
    db.commit()
    print(f"Promoted {email} to admin")
else:
    user = User(email=email, hashed_password=hash_password(password), role="admin")
    db.add(user)
    db.commit()
    print(f"Created admin: {email}")
    if len(sys.argv) <= 2:
        print(f"Generated password (shown once): {password}")
import os
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
from models.ticket import Ticket
from models.kb_article import KBArticle
from models.service_catalog import ServiceCatalogItem
from models.change import Change
from models.ticket_comment import TicketComment
from vector.chroma_client import index_article
import json
import yaml


# Set users
db = SessionLocal()
agent = db.query(User).filter(User.email == "agent@aitsm.local").first()
if not agent:
    agent = User(
        email="agent@aitsm.local",
        hashed_password=hash_password("changeme"),
        full_name="Agent Support",
        role="agent",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    print(f"Created agent: {agent.id}")
else:
    print(f"Agent already exists: {agent.id}")

admin = db.query(User).filter(User.email == "admin@aitsm.local").first()
if not admin:
    print("WARNING: admin@aitsm.local not found — run seed_admin.py first")
    sys.exit(1)

# Load sample data from customizable data/sample_data.yml
DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample_data.yml",
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

kb_items = data["kb_articles"]
catalog_items = data["service_catalog"]
tickets_data = data["tickets"]
changes_data = data["changes"]

# Add loaded items to the database, checking for duplicates by title/name
created_articles = []
for item in kb_items:
    existing = db.query(KBArticle).filter(KBArticle.title == item["title"]).first()
    if existing:
        print(f"KB already exists: {item['title']}")
        created_articles.append(existing)
        continue
    article = KBArticle(
        title=item["title"],
        content=item["content"],
        tags=json.dumps(item["tags"]),
        status="published",
        author_id=admin.id,
        chroma_id=None,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    index_article(article.id, article.title, article.content, item["tags"])
    article.chroma_id = article.id
    db.commit()
    created_articles.append(article)
    print(f"Created & indexed KB: {article.title}")


for item in catalog_items:
    existing = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.name == item["name"])
        .first()
    )
    if existing:
        print(f"Catalog already exists: {item['name']}")
        continue
    entry = ServiceCatalogItem(
        name=item["name"],
        description=item["description"],
        category=item["category"],
        default_priority=item["default_priority"],
        form_schema=json.dumps(item["form_schema"]),
    )
    db.add(entry)
    db.commit()
    print(f"Created catalog: {item['name']}")


created_tickets = []
for item in tickets_data:
    existing = db.query(Ticket).filter(Ticket.title == item["title"]).first()
    if existing:
        print(f"Ticket already exists: {item['title']}")
        created_tickets.append(existing)
        continue
    t = Ticket(
        title=item["title"],
        description=item["description"],
        priority=item["priority"],
        status=item["status"],
        source="portal",
        requester_id=agent.id,
        assignee_id=admin.id if item["status"] == "in_progress" else None,
        resolution=item.get("resolution"),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    created_tickets.append(t)
    print(f"Created ticket: {t.title}")

if created_tickets:
    t = created_tickets[0]
    existing = db.query(TicketComment).filter(TicketComment.ticket_id == t.id).first()
    if not existing:
        db.add(
            TicketComment(
                ticket_id=t.id,
                author_id=agent.id,
                content="Problème reproduit sur un autre Mac également.",
                is_internal=True,
            )
        )
        db.add(
            TicketComment(
                ticket_id=t.id,
                author_id=admin.id,
                content="Nous avons bien reçu votre demande, notre équipe traite le problème.",
                is_internal=False,
            )
        )
        db.commit()
        print(f"Created comments on ticket: {t.title}")

created_changes = []
for item in changes_data:
    existing_change = db.query(Change).filter(Change.title == item["title"]).first()
    if existing_change:
        print(f"Change already exists: {item['title']}")
        created_changes.append(existing_change)
        continue
    c = Change(
        title=item["title"],
        description=item["description"],
        risk=item["risk"],
        status=item["status"],
        submitter_id=agent.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    created_changes.append(c)
    print(f"Created change: {c.title}")

print("\n✓ Seed data complete.")
print("\n── Summary ────────────────────────────────────────────────────────────")
for t in created_tickets:
    print(f"  Ticket  [{t.id}]  {t.title}")
for a in created_articles:
    print(f"  KB      [{a.id}]  {a.title}")
for c in created_changes:
    print(f"  Change  [{c.id}]  {c.title}")
print("─────────────────────────────────────────────────────────────────────────")

from sqlalchemy.orm import Session
from models.change import Change
from models.user import User
from schemas.change import ChangeCreate, ChangeUpdate

TRANSITIONS = {
    "draft": {"review"},
    "review": {"approved", "rejected"},
    "approved": {"done"},
    "rejected": set(),
    "done": set(),
}

ADMIN_ONLY_TRANSITIONS = {"approved", "rejected", "done"}


def create_change(db: Session, payload: ChangeCreate, submitter_id: str) -> Change:
    change = Change(**payload.model_dump(), submitter_id=submitter_id)
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


def get_change(db: Session, change_id: str) -> Change | None:
    return db.get(Change, change_id)


def list_changes(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> tuple[list[Change], int]:
    query = db.query(Change)
    if status:
        query = query.filter(Change.status == status)
    total = query.count()
    items = query.order_by(Change.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_change(db: Session, change_id: str, payload: ChangeUpdate) -> Change | None:
    change = db.get(Change, change_id)
    if not change:
        return None
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(change, field, value)
    db.commit()
    db.refresh(change)
    return change


def transition(db: Session, change_id: str, new_status: str, user: User) -> Change:
    change = db.get(Change, change_id)
    if not change:
        raise ValueError(f"Change {change_id} not found")

    allowed = TRANSITIONS.get(change.status, set())
    if new_status not in allowed:
        raise PermissionError(
            f"Cannot transition from '{change.status}' to '{new_status}'"
        )

    if new_status in ADMIN_ONLY_TRANSITIONS and user.role != "admin":
        raise PermissionError("Admin only")

    change.status = new_status
    if new_status == "approved":
        change.approver_id = user.id

    db.commit()
    db.refresh(change)
    return change

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.change import ChangeCreate, ChangeOut, ChangeUpdate
from services.change_service import (
    create_change,
    get_change,
    list_changes,
    transition,
    update_change,
)

router = APIRouter()


@router.post("", response_model=ChangeOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: ChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_change(db, payload, submitter_id=current_user.id)


@router.get("", response_model=list[ChangeOut])
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, _ = list_changes(db, skip=skip, limit=limit, status=status)
    return items


@router.get("/{change_id}", response_model=ChangeOut)
def get_one(
    change_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change = get_change(db, change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    return change


@router.patch("/{change_id}", response_model=ChangeOut)
def update(
    change_id: str,
    payload: ChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change = update_change(db, change_id, payload)
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    return change


def _transition_endpoint(new_status: str):
    def endpoint(
        change_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        try:
            return transition(db, change_id, new_status, current_user)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    endpoint.__name__ = f"transition_{new_status}"
    return endpoint


router.add_api_route(
    "/{change_id}/submit",
    _transition_endpoint("review"),
    methods=["POST"],
    response_model=ChangeOut,
)
router.add_api_route(
    "/{change_id}/approve",
    _transition_endpoint("approved"),
    methods=["POST"],
    response_model=ChangeOut,
)
router.add_api_route(
    "/{change_id}/reject",
    _transition_endpoint("rejected"),
    methods=["POST"],
    response_model=ChangeOut,
)
router.add_api_route(
    "/{change_id}/done",
    _transition_endpoint("done"),
    methods=["POST"],
    response_model=ChangeOut,
)

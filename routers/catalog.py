from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.service_catalog import (
    ServiceCatalogCreate,
    ServiceCatalogOut,
    ServiceRequestCreate,
)
from schemas.ticket import TicketOut
from services.catalog_service import (
    create_service,
    get_service,
    list_services,
    submit_request,
)

router = APIRouter()


@router.post("", response_model=ServiceCatalogOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: ServiceCatalogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return create_service(db, payload)


@router.get("", response_model=list[ServiceCatalogOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_services(db, active_only=True)


@router.get("/{service_id}", response_model=ServiceCatalogOut)
def get_one(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post(
    "/{service_id}/request",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
)
def request_service(
    service_id: str,
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return submit_request(db, service_id, payload, requester_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

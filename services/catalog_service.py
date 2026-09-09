import json

from sqlalchemy.orm import Session

from models.service_catalog import ServiceCatalogItem
from models.ticket import Ticket
from schemas.service_catalog import ServiceCatalogCreate, ServiceRequestCreate


def create_service(db: Session, payload: ServiceCatalogCreate) -> ServiceCatalogItem:
    item = ServiceCatalogItem(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        default_priority=payload.default_priority,
        form_schema=json.dumps(payload.form_schema),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_services(db: Session, active_only: bool = True) -> list[ServiceCatalogItem]:
    query = db.query(ServiceCatalogItem)
    if active_only:
        query = query.filter(ServiceCatalogItem.is_active)
    return query.order_by(ServiceCatalogItem.name).all()


def get_service(db: Session, service_id: str) -> ServiceCatalogItem | None:
    return db.get(ServiceCatalogItem, service_id)


def submit_request(
    db: Session, service_id: str, payload: ServiceRequestCreate, requester_id: str
) -> Ticket:
    service = db.get(ServiceCatalogItem, service_id)
    if not service:
        raise ValueError(f"Service {service_id} not found")

    description = (
        f"Demande de service : {service.name}\n\n"
        + "\n".join(f"**{k}** : {v}" for k, v in payload.form_data.items())
        if payload.form_data
        else service.description
    )

    ticket = Ticket(
        title=service.name,
        description=description,
        category=service.category,
        priority=service.default_priority,
        source="portal",
        requester_id=requester_id,
        service_id=service.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

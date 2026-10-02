from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.auth.dependencies import get_current_admin


router = APIRouter(
    prefix="/services",
    tags=["Servicios"]
)


# =========================================================
# SCHEMAS
# =========================================================

class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    base_price: float
    duration: str | None = None


class ServiceUpdate(BaseModel):
    name: str
    description: str | None = None
    base_price: float
    duration: str | None = None


class ServiceStatusUpdate(BaseModel):
    is_active: bool


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    base_price: float
    duration: str | None
    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# OBTENER TODOS LOS SERVICIOS
# =========================================================

@router.get(
    "/",
    response_model=list[ServiceResponse]
)
def get_services(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    services = (
        db.query(Service)
        .order_by(Service.id.desc())
        .all()
    )

    return services


# =========================================================
# OBTENER UN SERVICIO
# =========================================================

@router.get(
    "/{service_id}",
    response_model=ServiceResponse
)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    return service


# =========================================================
# CREAR SERVICIO
# =========================================================

@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=201
)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    existing_service = (
        db.query(Service)
        .filter(Service.name == service_data.name)
        .first()
    )

    if existing_service:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un servicio con ese nombre"
        )

    if service_data.base_price < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio no puede ser negativo"
        )

    service = Service(
        name=service_data.name,
        description=service_data.description,
        base_price=service_data.base_price,
        duration=service_data.duration,
        is_active=True
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


# =========================================================
# EDITAR SERVICIO
# =========================================================

@router.put(
    "/{service_id}",
    response_model=ServiceResponse
)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    existing_service = (
        db.query(Service)
        .filter(
            Service.name == service_data.name,
            Service.id != service_id
        )
        .first()
    )

    if existing_service:
        raise HTTPException(
            status_code=400,
            detail="Ese nombre ya pertenece a otro servicio"
        )

    if service_data.base_price < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio no puede ser negativo"
        )

    service.name = service_data.name
    service.description = service_data.description
    service.base_price = service_data.base_price
    service.duration = service_data.duration

    db.commit()
    db.refresh(service)

    return service


# =========================================================
# ACTIVAR / DESACTIVAR SERVICIO
# =========================================================

@router.patch(
    "/{service_id}/status",
    response_model=ServiceResponse
)
def update_service_status(
    service_id: int,
    status_data: ServiceStatusUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    service.is_active = status_data.is_active

    db.commit()
    db.refresh(service)

    return service
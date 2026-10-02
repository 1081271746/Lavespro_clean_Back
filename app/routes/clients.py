from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.auth.dependencies import get_current_admin


router = APIRouter(
    prefix="/clients",
    tags=["Clientes"]
)


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str | None = None
    city: str | None = "Pasto"


class ClientUpdate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str | None = None
    city: str | None = "Pasto"


class ClientStatusUpdate(BaseModel):
    is_active: bool


class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: str | None
    city: str | None
    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# OBTENER TODOS LOS CLIENTES
# =========================================================

@router.get(
    "/",
    response_model=list[ClientResponse]
)
def get_clients(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    clients = (
        db.query(Client)
        .order_by(Client.id.desc())
        .all()
    )

    return clients


# =========================================================
# OBTENER UN CLIENTE
# =========================================================

@router.get(
    "/{client_id}",
    response_model=ClientResponse
)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return client


# =========================================================
# CREAR CLIENTE
# =========================================================

@router.post(
    "/",
    response_model=ClientResponse,
    status_code=201
)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    existing_client = (
        db.query(Client)
        .filter(Client.email == client_data.email)
        .first()
    )

    if existing_client:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un cliente con este correo"
        )

    client = Client(
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        address=client_data.address,
        city=client_data.city,
        is_active=True
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


# =========================================================
# EDITAR CLIENTE
# =========================================================

@router.put(
    "/{client_id}",
    response_model=ClientResponse
)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Verificar que el correo no pertenezca a otro cliente
    existing_client = (
        db.query(Client)
        .filter(
            Client.email == client_data.email,
            Client.id != client_id
        )
        .first()
    )

    if existing_client:
        raise HTTPException(
            status_code=400,
            detail="Ese correo ya pertenece a otro cliente"
        )

    client.name = client_data.name
    client.email = client_data.email
    client.phone = client_data.phone
    client.address = client_data.address
    client.city = client_data.city

    db.commit()
    db.refresh(client)

    return client


# =========================================================
# ACTIVAR / DESACTIVAR CLIENTE
# =========================================================

@router.patch(
    "/{client_id}/status",
    response_model=ClientResponse
)
def update_client_status(
    client_id: int,
    status_data: ClientStatusUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    client.is_active = status_data.is_active

    db.commit()
    db.refresh(client)

    return client
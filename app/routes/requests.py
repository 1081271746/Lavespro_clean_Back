import os
import uuid

from pathlib import Path

from fastapi import UploadFile, File

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.request_photo import RequestPhoto
from app.database import get_db, SessionLocal
from app.models.request import ServiceRequest
from app.models.client import Client
from app.models.service import Service
from app.auth.dependencies import get_current_admin
from app.models.work import Work


router = APIRouter(
    prefix="/service-requests",
    tags=["Solicitudes"]
)


# =========================================================
# SCHEMAS
# =========================================================

class RequestCreate(BaseModel):
    client_id: int
    service_id: int
    requested_date: datetime | None = None
    address: str
    notes: str | None = None

class PublicRequestCreate(BaseModel):
    name: str
    email: str
    phone: str
    service_id: int
    requested_date: datetime | None = None
    address: str
    city: str = "Pasto"
    notes: str | None = None


class RequestUpdate(BaseModel):
    client_id: int
    service_id: int
    requested_date: datetime | None = None
    address: str
    notes: str | None = None


class RequestStatusUpdate(BaseModel):
    status: str


class RequestResponse(BaseModel):
    id: int
    client_id: int
    service_id: int
    requested_date: datetime | None
    address: str
    notes: str | None
    status: str
    estimated_price: float
    is_active: bool

    photos: list[dict] = []

    class Config:
        from_attributes = True


# =========================================================
# VALIDAR ESTADO
# =========================================================

VALID_STATUSES = {
    "Pendiente",
    "Confirmada",
    "Cancelada"
}


# =========================================================
# OBTENER TODAS LAS SOLICITUDES
# =========================================================

# =========================================================
# CREAR SOLICITUD DESDE EL SITIO WEB PÚBLICO
# =========================================================

@router.post(
    "/public",
    response_model=RequestResponse,
    status_code=201
)
def create_public_request(
    request_data: PublicRequestCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------
    # VALIDAR SERVICIO
    # -----------------------------------------

    service = (
        db.query(Service)
        .filter(Service.id == request_data.service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="El servicio seleccionado no existe"
        )

    if not service.is_active:
        raise HTTPException(
            status_code=400,
            detail="El servicio seleccionado no está disponible"
        )

    # -----------------------------------------
    # VALIDAR DATOS DEL CLIENTE
    # -----------------------------------------

    if not request_data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="El nombre es obligatorio"
        )

    if not request_data.phone.strip():
        raise HTTPException(
            status_code=400,
            detail="El teléfono es obligatorio"
        )

    if not request_data.address.strip():
        raise HTTPException(
            status_code=400,
            detail="La dirección es obligatoria"
        )

    # -----------------------------------------
    # BUSCAR CLIENTE EXISTENTE
    # -----------------------------------------

    client = (
        db.query(Client)
        .filter(Client.email == request_data.email)
        .first()
    )

    # -----------------------------------------
    # CREAR O ACTUALIZAR CLIENTE
    # -----------------------------------------

    if client:

        client.name = request_data.name.strip()
        client.phone = request_data.phone.strip()
        client.address = request_data.address.strip()
        client.city = request_data.city.strip()
        client.is_active = True

    else:

        client = Client(
            name=request_data.name.strip(),
            email=request_data.email.strip(),
            phone=request_data.phone.strip(),
            address=request_data.address.strip(),
            city=request_data.city.strip(),
            is_active=True
        )

        db.add(client)
        db.flush()

    # -----------------------------------------
    # CREAR SOLICITUD
    # -----------------------------------------

    service_request = ServiceRequest(
        client_id=client.id,
        service_id=service.id,
        requested_date=request_data.requested_date,
        address=request_data.address.strip(),
        notes=request_data.notes,
        status="Pendiente",
        estimated_price=service.base_price,
        is_active=True
    )

    db.add(service_request)
    db.commit()
    db.refresh(service_request)

    return service_request

# =========================================================
# OBTENER TODAS LAS SOLICITUDES
# =========================================================

@router.get(
    "/",
    response_model=list[RequestResponse]
)
def get_requests(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    requests = (
        db.query(ServiceRequest)
        .order_by(ServiceRequest.id.desc())
        .all()
    )

    result = []

    for request in requests:

        photos = (
            db.query(RequestPhoto)
            .filter(
                RequestPhoto.request_id == request.id
            )
            .all()
        )

        photo_list = [
            {
                "file_name": photo.file_name,
                "url": (
                    f"/uploads/requests/"
                    f"{request.id}/"
                    f"{Path(photo.file_path).name}"
                )
            }
            for photo in photos
        ]

        result.append({
            "id": request.id,
            "client_id": request.client_id,
            "service_id": request.service_id,
            "requested_date": request.requested_date,
            "address": request.address,
            "notes": request.notes,
            "status": request.status,
            "estimated_price": request.estimated_price,
            "is_active": request.is_active,
            "photos": photo_list
        })

    return result


# =========================================================
# OBTENER UNA SOLICITUD
# =========================================================

@router.get(
    "/{request_id}",
    response_model=RequestResponse
)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )

    photos = (
        db.query(RequestPhoto)
        .filter(
            RequestPhoto.request_id == request_id
        )
        .all()
    )

    photo_list = [
        {
            "file_name": photo.file_name,
            "url": (
                f"/uploads/requests/"
                f"{request_id}/"
                f"{Path(photo.file_path).name}"
            )
        }
        for photo in photos
    ]

    return {
        "id": request.id,
        "client_id": request.client_id,
        "service_id": request.service_id,
        "requested_date": request.requested_date,
        "address": request.address,
        "notes": request.notes,
        "status": request.status,
        "estimated_price": request.estimated_price,
        "is_active": request.is_active,
        "photos": photo_list
    }

# =========================================================
# CREAR SOLICITUD
# =========================================================

@router.post(
    "/",
    response_model=RequestResponse,
    status_code=201
)
def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    # -----------------------------------------
    # VALIDAR CLIENTE
    # -----------------------------------------

    client = (
        db.query(Client)
        .filter(Client.id == request_data.client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=400,
            detail="El cliente está inactivo"
        )

    # -----------------------------------------
    # VALIDAR SERVICIO
    # -----------------------------------------

    service = (
        db.query(Service)
        .filter(Service.id == request_data.service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    if not service.is_active:
        raise HTTPException(
            status_code=400,
            detail="El servicio está inactivo"
        )

    # -----------------------------------------
    # VALIDAR DIRECCIÓN
    # -----------------------------------------

    if not request_data.address.strip():
        raise HTTPException(
            status_code=400,
            detail="La dirección es obligatoria"
        )

    # -----------------------------------------
    # CREAR SOLICITUD
    # -----------------------------------------

    service_request = ServiceRequest(
        client_id=request_data.client_id,
        service_id=request_data.service_id,
        requested_date=request_data.requested_date,
        address=request_data.address.strip(),
        notes=request_data.notes,
        status="Pendiente",
        estimated_price=service.base_price,
        is_active=True
    )

    db.add(service_request)
    db.commit()
    db.refresh(service_request)

    return service_request


# =========================================================
# EDITAR SOLICITUD
# =========================================================

@router.put(
    "/{request_id}",
    response_model=RequestResponse
)
def update_request(
    request_id: int,
    request_data: RequestUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    service_request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if not service_request:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )

    # -----------------------------------------
    # VALIDAR CLIENTE
    # -----------------------------------------

    client = (
        db.query(Client)
        .filter(Client.id == request_data.client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=400,
            detail="El cliente está inactivo"
        )

    # -----------------------------------------
    # VALIDAR SERVICIO
    # -----------------------------------------

    service = (
        db.query(Service)
        .filter(Service.id == request_data.service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    if not service.is_active:
        raise HTTPException(
            status_code=400,
            detail="El servicio está inactivo"
        )

    # -----------------------------------------
    # ACTUALIZAR
    # -----------------------------------------

    service_request.client_id = request_data.client_id
    service_request.service_id = request_data.service_id
    service_request.requested_date = request_data.requested_date
    service_request.address = request_data.address.strip()
    service_request.notes = request_data.notes
    service_request.estimated_price = service.base_price

    db.commit()
    db.refresh(service_request)

    return service_request


# =========================================================
# CAMBIAR ESTADO
# =========================================================

# =========================================================
# CAMBIAR ESTADO DE SOLICITUD
# =========================================================

@router.patch(
    "/{request_id}/status",
    response_model=RequestResponse
)
def update_request_status(
    request_id: int,
    status_data: RequestStatusUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    service_request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if not service_request:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )

    # -----------------------------------------
    # VALIDAR ESTADO
    # -----------------------------------------

    if status_data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Estado inválido. Estados permitidos: "
                "Pendiente, Confirmada, Cancelada"
            )
        )

    # -----------------------------------------
    # ACTUALIZAR ESTADO DE SOLICITUD
    # -----------------------------------------

    service_request.status = status_data.status

    # -----------------------------------------
    # SI SE CONFIRMA LA SOLICITUD,
    # CREAR TRABAJO AUTOMÁTICAMENTE
    # -----------------------------------------

    if status_data.status == "Confirmada":

        existing_work = (
            db.query(Work)
            .filter(
                Work.request_id == service_request.id,
                Work.is_active == True
            )
            .first()
        )

        # Evitar crear trabajos duplicados
        if not existing_work:

            work = Work(
                request_id=service_request.id,
                scheduled_date=service_request.requested_date,
                assigned_to=None,
                status="Programado",
                price=service_request.estimated_price,
                notes=service_request.notes,
                is_active=True
            )

            db.add(work)

    db.commit()
    db.refresh(service_request)

    return service_request

# =========================================================
# SUBIR FOTOGRAFÍAS DE UNA SOLICITUD
# =========================================================

@router.post(
    "/{request_id}/photos"
)
async def upload_request_photos(
    request_id: int,
    files: list[UploadFile] = File(...)
):
    db = SessionLocal()

    try:

        # -----------------------------------------
        # BUSCAR SOLICITUD
        # -----------------------------------------

        service_request = (
            db.query(ServiceRequest)
            .filter(ServiceRequest.id == request_id)
            .first()
        )

        if not service_request:
            raise HTTPException(
                status_code=404,
                detail="Solicitud no encontrada"
            )

        # -----------------------------------------
        # CARPETA DE LA SOLICITUD
        # -----------------------------------------

        upload_dir = Path(
            f"uploads/requests/{request_id}"
        )

        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        saved_photos = []

        # -----------------------------------------
        # PROCESAR ARCHIVOS
        # -----------------------------------------

        

        for file in files:

            if not file.content_type:
                continue

            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"El archivo {file.filename} "
                        "no es una imagen válida."
                    )
                )

            extension = Path(
                file.filename or ""
            ).suffix.lower()

            allowed_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            }

            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Formato no permitido: {extension}"
                    )
                )

            # -----------------------------------------
            # NOMBRE ÚNICO
            # -----------------------------------------

            unique_name = (
                f"{uuid.uuid4().hex}{extension}"
            )

            file_path = upload_dir / unique_name

            # -----------------------------------------
            # GUARDAR ARCHIVO
            # -----------------------------------------

            content = await file.read()

            # límite aproximado de 5 MB
            if len(content) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"La imagen {file.filename} "
                        "supera el límite de 5 MB."
                    )
                )

            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # -----------------------------------------
            # GUARDAR REGISTRO EN BD
            # -----------------------------------------

            photo = RequestPhoto(
                request_id=request_id,
                file_name=file.filename or unique_name,
                file_path=str(
                    file_path
                    .as_posix()
                ),
                content_type=file.content_type
            )

            db.add(photo)

            saved_photos.append({
                "file_name": file.filename,
                "url": (
                    f"/uploads/requests/"
                    f"{request_id}/"
                    f"{unique_name}"
                )
            })

        db.commit()

        return {
            "message": "Fotografías subidas correctamente",
            "request_id": request_id,
            "photos": saved_photos
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar fotografías: {str(e)}"
        )

    finally:
        db.close()

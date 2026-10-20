from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.work import Work
from app.models.request import ServiceRequest
from app.models.request_photo import RequestPhoto


router = APIRouter(
    prefix="/works",
    tags=["Trabajos"]
)

# =========================
# ENCARGADOS DISPONIBLES
# =========================

ENCARGADOS = [
    "Juan Pablo Zarama",
    "Mauricio Eraso",
    "Vanessa Ceron"
]


# =========================
# SCHEMAS
# =========================

class WorkCreate(BaseModel):
    request_id: int
    scheduled_date: datetime | None = None
    assigned_to: str | None = None
    status: str = "Programado"
    price: float = 0
    notes: str | None = None


class WorkUpdate(BaseModel):
    scheduled_date: datetime | None = None
    assigned_to: str | None = None
    status: str | None = None
    price: float | None = None
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    is_active: bool | None = None


class WorkResponse(BaseModel):
    id: int
    request_id: int
    scheduled_date: datetime | None
    assigned_to: str | None
    status: str
    price: float
    notes: str | None
    started_at: datetime | None
    completed_at: datetime | None
    is_active: bool
    created_at: datetime | None

    photos: list[dict] = Field(default_factory=list)


# =========================
# FUNCIÓN PARA OBTENER FOTOS
# =========================

def get_work_photos(
    db: Session,
    request_id: int
):
    photos = (
        db.query(RequestPhoto)
        .filter(RequestPhoto.request_id == request_id)
        .all()
    )

    return [
        {
            "file_name": photo.file_name,
            "url": (
                f"/uploads/requests/"
                f"{request_id}/"
                f"{photo.file_path.split('/')[-1]}"
            )
        }
        for photo in photos
    ]


# =========================
# CREAR TRABAJO
# =========================

@router.post("/", response_model=WorkResponse)
def create_work(data: WorkCreate):

    db: Session = SessionLocal()

    try:
        request = (
            db.query(ServiceRequest)
            .filter(ServiceRequest.id == data.request_id)
            .first()
        )

        if not request:
            raise HTTPException(
                status_code=404,
                detail="La solicitud no existe"
            )

        existing_work = (
            db.query(Work)
            .filter(
                Work.request_id == data.request_id,
                Work.is_active == True
            )
            .first()
        )

        if existing_work:
            raise HTTPException(
                status_code=400,
                detail="Esta solicitud ya tiene un trabajo activo"
            )

        work = Work(
            request_id=data.request_id,
            scheduled_date=data.scheduled_date,
            assigned_to=data.assigned_to,
            status=data.status,
            price=data.price,
            notes=data.notes
        )

        db.add(work)
        db.commit()
        db.refresh(work)

        return {
            "id": work.id,
            "request_id": work.request_id,
            "scheduled_date": work.scheduled_date,
            "assigned_to": work.assigned_to,
            "status": work.status,
            "price": float(work.price),
            "notes": work.notes,
            "started_at": work.started_at,
            "completed_at": work.completed_at,
            "is_active": work.is_active,
            "created_at": work.created_at,
            "photos": get_work_photos(
                db,
                work.request_id
            )
        }

    finally:
        db.close()


# =========================
# LISTAR TRABAJOS
# =========================

@router.get("/", response_model=list[WorkResponse])
def get_works():

    db: Session = SessionLocal()

    try:
        works = (
            db.query(Work)
            .filter(Work.is_active == True)
            .order_by(Work.created_at.desc())
            .all()
        )

        result = []

        for work in works:

            result.append({
                "id": work.id,
                "request_id": work.request_id,
                "scheduled_date": work.scheduled_date,
                "assigned_to": work.assigned_to,
                "status": work.status,
                "price": float(work.price),
                "notes": work.notes,
                "started_at": work.started_at,
                "completed_at": work.completed_at,
                "is_active": work.is_active,
                "created_at": work.created_at,
                "photos": get_work_photos(
                    db,
                    work.request_id
                )
            })

        return result

    finally:
        db.close()

        # =========================
# CONSULTAR DISPONIBILIDAD
# =========================

@router.get("/availability")
def get_availability(
    scheduled_date: datetime = Query(...)
):
    db: Session = SessionLocal()

    try:
        # -----------------------------------------
        # DETERMINAR LA JORNADA
        # -----------------------------------------

        if scheduled_date.hour < 12:
            start_time = scheduled_date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

            end_time = scheduled_date.replace(
                hour=11,
                minute=59,
                second=59,
                microsecond=999999
            )

            jornada = "Mañana"

        else:
            start_time = scheduled_date.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0
            )

            end_time = scheduled_date.replace(
                hour=23,
                minute=59,
                second=59,
                microsecond=999999
            )

            jornada = "Tarde"

        # -----------------------------------------
        # BUSCAR TRABAJOS OCUPADOS
        # -----------------------------------------

        occupied_works = (
            db.query(Work)
            .filter(
                Work.scheduled_date >= start_time,
                Work.scheduled_date <= end_time,
                Work.is_active == True,
                Work.status.in_([
                    "Programado",
                    "En proceso"
                ])
            )
            .all()
        )

        # -----------------------------------------
        # OBTENER ENCARGADOS OCUPADOS
        # -----------------------------------------

        occupied_names = {
            work.assigned_to
            for work in occupied_works
            if work.assigned_to
        }

        # -----------------------------------------
        # RESPUESTA
        # -----------------------------------------

        return {
            "scheduled_date": scheduled_date,
            "jornada": jornada,
            "encargados": [
                {
                    "name": name,
                    "available": name not in occupied_names
                }
                for name in ENCARGADOS
            ],
            "available_count": sum(
                name not in occupied_names
                for name in ENCARGADOS
            )
        }

    finally:
        db.close()


# =========================
# OBTENER UN TRABAJO
# =========================

@router.get("/{work_id}", response_model=WorkResponse)
def get_work(work_id: int):

    db: Session = SessionLocal()

    try:
        work = (
            db.query(Work)
            .filter(
                Work.id == work_id,
                Work.is_active == True
            )
            .first()
        )

        if not work:
            raise HTTPException(
                status_code=404,
                detail="Trabajo no encontrado"
            )

        return {
            "id": work.id,
            "request_id": work.request_id,
            "scheduled_date": work.scheduled_date,
            "assigned_to": work.assigned_to,
            "status": work.status,
            "price": float(work.price),
            "notes": work.notes,
            "started_at": work.started_at,
            "completed_at": work.completed_at,
            "is_active": work.is_active,
            "created_at": work.created_at,
            "photos": get_work_photos(
                db,
                work.request_id
            )
        }

    finally:
        db.close()


# =========================
# ACTUALIZAR TRABAJO
# =========================

@router.put("/{work_id}", response_model=WorkResponse)
def update_work(
    work_id: int,
    data: WorkUpdate
):

    db: Session = SessionLocal()

    try:
        work = (
            db.query(Work)
            .filter(
                Work.id == work_id,
                Work.is_active == True
            )
            .first()
        )

        if not work:
            raise HTTPException(
                status_code=404,
                detail="Trabajo no encontrado"
            )

        # Guardar el estado anterior
        previous_status = work.status

        # Obtener solamente los campos enviados
        update_data = data.model_dump(
            exclude_unset=True
        )

        # Aplicar los cambios
        for field, value in update_data.items():
            setattr(work, field, value)

        # ==========================================
        # CONTROL AUTOMÁTICO DE FECHAS
        # ==========================================

        # Programado → En proceso
        if (
            work.status == "En proceso"
            and previous_status != "En proceso"
            and work.started_at is None
        ):
            work.started_at = datetime.now()

        # En proceso → Completado
        if (
            work.status == "Completado"
            and previous_status != "Completado"
            and work.completed_at is None
        ):
            work.completed_at = datetime.now()

        db.commit()
        db.refresh(work)

        return {
            "id": work.id,
            "request_id": work.request_id,
            "scheduled_date": work.scheduled_date,
            "assigned_to": work.assigned_to,
            "status": work.status,
            "price": float(work.price),
            "notes": work.notes,
            "started_at": work.started_at,
            "completed_at": work.completed_at,
            "is_active": work.is_active,
            "created_at": work.created_at,
            "photos": get_work_photos(
                db,
                work.request_id
            )
        }

    finally:
        db.close()
# =========================
# DESACTIVAR TRABAJO
# =========================

@router.delete("/{work_id}")
def delete_work(work_id: int):

    db: Session = SessionLocal()

    try:
        work = (
            db.query(Work)
            .filter(
                Work.id == work_id,
                Work.is_active == True
            )
            .first()
        )

        if not work:
            raise HTTPException(
                status_code=404,
                detail="Trabajo no encontrado"
            )

        work.is_active = False

        db.commit()

        return {
            "message": "Trabajo desactivado correctamente",
            "work_id": work_id
        }

    finally:
        db.close()
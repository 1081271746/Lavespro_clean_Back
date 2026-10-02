from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.user import User
from app.models.client import Client
from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.models.service import Service
from app.routes.services import router as services_router
from app.models.request import ServiceRequest
from app.routes.requests import router as requests_router
from app.models.request_photo import RequestPhoto
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CleanPro API",
    description="API para la plataforma de gestión de CleanPro",
    version="1.0.0"
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# Permitir comunicación con el frontend de Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(services_router)
app.include_router(requests_router) 


@app.get("/")
def root():
    return {
        "message": "CleanPro API funcionando correctamente"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }
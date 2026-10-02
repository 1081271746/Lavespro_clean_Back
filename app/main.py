from fastapi import FastAPI

from app.database import Base, engine
from app.models.user import User


# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CleanPro API",
    description="API para la plataforma de gestión de CleanPro",
    version="1.0.0"
)


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
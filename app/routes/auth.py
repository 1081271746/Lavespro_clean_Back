from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.password import verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == credentials.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="El usuario está desactivado"
        )

    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    access_token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "name": user.name
    })

    return {
        "message": "Inicio de sesión exitoso",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


# Obtener información del usuario autenticado
@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
from getpass import getpass

from app.database import SessionLocal
from app.models.user import User
from app.auth.password import hash_password


def create_admin():
    db = SessionLocal()

    try:
        name = "Carolina Sotelo"
        email = "cleanpro.pasto@gmail.com"

        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            print("El administrador ya existe.")
            return

        password = getpass("Ingrese la contraseña del administrador: ")
        confirm_password = getpass("Confirme la contraseña: ")

        if password != confirm_password:
            print("Las contraseñas no coinciden.")
            return

        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Administrador creado correctamente.")
        print(f"ID: {admin.id}")
        print(f"Nombre: {admin.name}")
        print(f"Email: {admin.email}")
        print(f"Rol: {admin.role}")

    except Exception as e:
        db.rollback()
        print(f"Error al crear administrador: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
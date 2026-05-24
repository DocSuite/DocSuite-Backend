from app.db.session import SessionLocal
from app.schemas.user import UserCreate
from app.services.db.user_service import create_user, get_user_by_email


def seed() -> None:
    db = SessionLocal()
    try:
        email = "docente@docsuite.local"
        if get_user_by_email(db, email) is None:
            create_user(
                db,
                UserCreate(email=email, full_name="Docente Demo", password="DocSuite123"),
            )
            print("Usuario demo creado")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

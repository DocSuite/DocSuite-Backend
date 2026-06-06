from app.core.config import get_settings
from app.db.session import get_session_local
from app.schemas.user import UserCreate
from app.services.db.user_service import create_user, get_user_by_email


def seed() -> None:
    settings = get_settings()
    db = get_session_local()()
    try:
        if get_user_by_email(db, settings.admin_email) is not None:
            print(f"Admin existente: {settings.admin_email}")
            return

        create_user(
            db,
            UserCreate(
                email=settings.admin_email,
                full_name=settings.admin_full_name,
                password=settings.admin_password,
            ),
        )
        print(f"Admin creado: {settings.admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

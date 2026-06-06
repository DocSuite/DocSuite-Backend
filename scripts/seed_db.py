import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.db.session import get_session_local
from app.schemas.user import UserCreate
from app.services.db.role_service import ADMIN_ROLE_NAME, get_role_by_name, seed_access_control
from app.services.db.user_service import create_user, get_user_by_email


def seed() -> None:
    settings = get_settings()
    db = get_session_local()()
    try:
        seed_access_control(db, settings.admin_email)
        existing_admin = get_user_by_email(db, settings.admin_email)
        if existing_admin is not None:
            admin_role = get_role_by_name(db, ADMIN_ROLE_NAME)
            if admin_role is not None and existing_admin.role_id != admin_role.id:
                existing_admin.role_id = admin_role.id
                db.commit()
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
        seed_access_control(db, settings.admin_email)
        print(f"Admin creado: {settings.admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

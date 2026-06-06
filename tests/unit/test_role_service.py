from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import (
    Acta,
    ActaJobRecord,
    Analysis,
    AppView,
    AuditLog,
    Role,
    RoleViewPermission,
    User,
)
from app.schemas.user import UserAdminCreate
from app.services.db.role_service import seed_access_control, user_has_permission
from app.services.db.user_service import create_user_by_admin


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    _ = (Acta, ActaJobRecord, Analysis, AppView, AuditLog, Role, RoleViewPermission, User)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_admin_has_all_permissions() -> None:
    db = _session()
    seed_access_control(db, "admin@docsuite.edu.pe")
    admin = User(
        email="admin@docsuite.edu.pe",
        full_name="Admin",
        hashed_password="hash",
        role_id=1,
    )

    assert user_has_permission(db, admin, "/admin/roles", "delete")


def test_docente_cannot_access_admin_permissions() -> None:
    db = _session()
    seed_access_control(db, "admin@docsuite.edu.pe")
    docente = User(
        email="docente@docsuite.edu.pe",
        full_name="Docente",
        hashed_password="hash",
        role_id=2,
    )

    assert user_has_permission(db, docente, "/doc-acta", "create")
    assert not user_has_permission(db, docente, "/admin/roles", "read")


def test_admin_creates_user_with_dni_password(monkeypatch) -> None:
    db = _session()
    seed_access_control(db, "admin@docsuite.edu.pe")
    sent_email = {}

    def fake_send_user_created_email(full_name: str, email: str, dni: str) -> None:
        sent_email.update({"full_name": full_name, "email": email, "dni": dni})

    monkeypatch.setattr(
        "app.services.db.user_service.send_user_created_email",
        fake_send_user_created_email,
    )

    user = create_user_by_admin(
        db,
        UserAdminCreate(
            full_name="Docente Demo",
            email="docente@docsuite.edu.pe",
            dni="12345678",
            role_id=2,
        ),
    )

    assert user.dni == "12345678"
    assert user.role_id == 2
    assert sent_email == {
        "full_name": "Docente Demo",
        "email": "docente@docsuite.edu.pe",
        "dni": "12345678",
    }

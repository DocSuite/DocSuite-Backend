from app.db.base import Base
from app.db.session import get_engine
from app.models import Acta, Analysis, User


def init_db() -> None:
    _ = (Acta, Analysis, User)
    Base.metadata.create_all(bind=get_engine())

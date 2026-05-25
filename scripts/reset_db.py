from app.db.base import Base
from app.db.session import get_engine
from app.models import Acta, Analysis, User


if __name__ == "__main__":
    _ = (Acta, Analysis, User)
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Base de datos reiniciada")

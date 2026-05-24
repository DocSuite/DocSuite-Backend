from app.db.base import Base
from app.db.session import engine
from app.models import Acta, Analysis, User


if __name__ == "__main__":
    _ = (Acta, Analysis, User)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Base de datos reiniciada")

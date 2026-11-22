from app.core.settings import get_settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
sessionlocal = sessionmaker(bind=engine)


def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

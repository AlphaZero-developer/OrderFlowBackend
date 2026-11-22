from sqlalchemy.orm import Session
from app.services.user import UsersService
from app.services.order import OrderService
from app.db.sessions import get_db
from fastapi import Depends


def get_user_service(db: Session = Depends(get_db)):
    """Функция для инъекции зависимости Task Service"""
    return UsersService(db)


def get_order_service(db: Session = Depends(get_db)):
    return OrderService(db)

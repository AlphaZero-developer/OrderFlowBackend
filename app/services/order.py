from fastapi import HTTPException

from app.repositories.order import OrderRepository
from app.repositories.users import UsersRepository
from app.jwt_token.user_token import decode_token, jwt
from app.schemas.order import Order
from app.exceptions.exceptions import InsufficientPermissionsError
from sqlalchemy.orm import Session
from app.core.order_status import ALLOWED_TRANSITIONS


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repository = OrderRepository(db)
        self.users_repository = UsersRepository(db)

    def create_order(
        self, access_token: str, title: str, description: str, budget_rub: int
    ) -> Order:

        try:
            id_user = decode_token(access_token)
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)
        if id_user == "":
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        new_order = self.order_repository.create(
            owner_id=id_user,
            title=title,
            description=description,
            budget_rub=budget_rub,
        )
        self.db.commit()

        return Order.model_validate(new_order)

    def get_all_orders_current_user(self, access_token: str) -> list[Order]:

        try:
            decoded_token = decode_token(access_token)
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)

        user = self.users_repository.get_user_by_id(decoded_token)

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if user.role != "manager":
            return [
                Order.model_validate(order)
                for order in self.order_repository.get_all_orders_current_user(
                    decoded_token
                )
            ]
        else:
            return [
                Order.model_validate(order)
                for order in self.order_repository.get_all_orders()
            ]

    def get_current_order(self, access_token: str, id: str) -> Order:

        try:
            user = self.users_repository.get_user_by_id(decode_token(access_token))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)

        order = self.order_repository.get_current_order_by_id(id=id)

        if order is None:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if order.owner_id != user.id:
            if user.role == "client":
                raise HTTPException(status_code=404, detail="Заказ не найден")

        return Order.model_validate(order)

    def cancel_order(self, access_token: str, id: str) -> Order:

        try:
            user = self.users_repository.get_user_by_id(decode_token(access_token))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)

        order = self.order_repository.get_current_order_by_id(id=id)

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if order is None:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.owner_id != user.id:
            if user.role != "manager":
                raise HTTPException(status_code=404, detail="Заказ не найден")
            else:
                raise HTTPException(
                    status_code=403, detail="Доступ к запрошенному ресурсу запрещён"
                )
        if order.status != "new":
            raise HTTPException(status_code=409)

        result = self.order_repository.cancel_order(id=id)

        self.db.commit()

        return Order.model_validate(result)

    def update_status_order(self, access_token: str, id: str, status: str) -> Order:

        current_order = self.order_repository.update_status_order(id, status)

        if current_order is None:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        try:
            user = self.users_repository.get_user_by_id(decode_token(access_token))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if user.role != "manager":
            raise HTTPException(
                status_code=403, detail="Доступ к запрошенному ресурсу запрещён"
            )

        if status not in ALLOWED_TRANSITIONS[current_order.status]:
            raise HTTPException(
                status_code=409,
                detail=f"Переход {current_order.status} -> {status} запрещён",
            )
        self.db.commit()
        self.db.refresh(current_order)
        return Order.model_validate(current_order)

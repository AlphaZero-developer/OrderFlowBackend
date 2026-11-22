from fastapi import HTTPException

from app.repositories.order import OrderRepository
from app.repositories.users import UsersRepository
from app.jwt_token.user_token import decode_token
from app.schemas.order import Order
from app.exceptions.exceptions import InsufficientPermissionsError
from sqlalchemy.orm import Session


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repository = OrderRepository(db)
        self.users_repository = UsersRepository(db)

    def create_order(
        self, access_token: str, title: str, description: str, budget_rub: int
    ) -> Order:

        id_user = decode_token(access_token)

        new_order = self.order_repository.create(
            owner_id=id_user,
            title=title,
            description=description,
            budget_rub=budget_rub,
        )
        self.db.commit()

        return Order.model_validate(new_order)

    def get_all_orders_current_user(self, access_token: str) -> list[Order]:
        user = self.users_repository.get_user_by_id(decode_token(access_token))

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if user.role and not None != "manager":
            return [
                Order.model_validate(order)
                for order in self.order_repository.get_all_orders_current_user(
                    decode_token(access_token)
                )
            ]
        else:
            return [
                Order.model_validate(order)
                for order in self.order_repository.get_all_orders()
            ]

    def get_current_order(self, id: str) -> Order:
        return Order.model_validate(self.order_repository.get_current_order_by_id(id))

    def delete_order(self, id: str) -> None:
        self.order_repository.delete_order(id)
        self.db.commit()

    def update_status_order(self, access_token: str, id: str, status: str) -> Order:

        user = self.users_repository.get_user_by_id(decode_token(access_token))

        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        if user.role and not None != "manager":
            raise InsufficientPermissionsError

        current_order = self.order_repository.update_status_order(id, status)
        self.db.commit()
        return Order.model_validate(current_order)

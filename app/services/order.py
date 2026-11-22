from app.repositories.order import OrderRepository
from app.repositories.users import UsersRepository
from app.jwt_token.user_token import decode_token
from app.schemas.order import Order
from app.exceptions.exceptions import (
    UnauthorizedError,
    NotFoundError,
    ForbiddenError,
    ConflictError,
)
from sqlalchemy.orm import Session
from app.core.order_status import ALLOWED_TRANSITIONS
from app.cache.redis_cache import RedisCache


class OrderService:
    def __init__(self, db: Session, cache: RedisCache):
        self.db = db
        self.order_repository = OrderRepository(db)
        self.users_repository = UsersRepository(db)
        self.redis_cache = cache

    def create_order(
        self, access_token: str, title: str, description: str, budget_rub: int
    ) -> Order:

        id_user = decode_token(access_token)

        user = self.users_repository.get_user_by_id(id_user)

        if user is None:
            raise UnauthorizedError()

        if user.role == "manager":
            raise ForbiddenError()

        new_order = self.order_repository.create(
            owner_id=id_user,
            title=title,
            description=description,
            budget_rub=budget_rub,
        )

        self.db.commit()
        self._ivalidate_orders_cache(user.id)

        return Order.model_validate(new_order)

    def get_all_orders_current_user(self, access_token: str) -> list[Order]:

        decoded_token = decode_token(access_token)

        user = self.users_repository.get_user_by_id(decoded_token)

        if user is None:
            raise UnauthorizedError()

        cache_key = "orders:all" if user.role == "manager" else f"orders:user:{user.id}"

        cached = self.redis_cache.get(cache_key)

        if cached is not None:
            return [Order.model_validate(item) for item in cached]

        if user.role == "manager":
            orders_orm = self.order_repository.get_all_orders()
        else:
            orders_orm = self.order_repository.get_all_orders_current_user(user.id)

        orders = [Order.model_validate(o) for o in orders_orm]

        self.redis_cache.set(cache_key, [o.model_dump(mode="json") for o in orders])

        return orders

    def get_current_order(self, access_token: str, id: str) -> Order:

        user = self.users_repository.get_user_by_id(decode_token(access_token))

        order = self.order_repository.get_current_order_by_id(id=id)

        if order is None:
            raise NotFoundError()

        if user is None:
            raise UnauthorizedError()

        if order.owner_id != user.id:
            if user.role == "client":
                raise NotFoundError()

        return Order.model_validate(order)

    def cancel_order(self, access_token: str, id: str) -> Order:

        user = self.users_repository.get_user_by_id(decode_token(access_token))

        order = self.order_repository.get_current_order_by_id(id=id)

        if user is None:
            raise UnauthorizedError()

        if order is None:
            raise NotFoundError()

        if order.owner_id != user.id:
            if user.role != "manager":
                raise NotFoundError()
            else:
                raise ForbiddenError()
        if order.status != "new":
            raise ConflictError()

        result = self.order_repository.cancel_order(id=id)

        self.db.commit()

        self._ivalidate_orders_cache(user.id)

        return Order.model_validate(result)

    def update_status_order(self, access_token: str, id: str, status: str) -> Order:

        current_order = self.order_repository.get_current_order_by_id(id)

        if current_order is None:
            raise NotFoundError()

        user = self.users_repository.get_user_by_id(decode_token(access_token))

        if user is None:
            raise UnauthorizedError()

        if user.role != "manager":
            raise ForbiddenError()

        if status not in ALLOWED_TRANSITIONS[current_order.status]:
            raise ConflictError(detail="Переход запрещён")

        current_order = self.order_repository.update_status_order(id=id, status=status)

        self.db.commit()
        self.db.refresh(current_order)

        self._ivalidate_orders_cache(current_order.owner_id)

        return Order.model_validate(current_order)

    def _ivalidate_orders_cache(self, owner_id: str) -> None:
        self.redis_cache.delete(f"orders:user:{owner_id}", "orders:all")

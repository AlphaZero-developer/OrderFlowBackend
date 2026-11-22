from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.order import OrderORM


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, owner_id: str, title: str, description: str, budget_rub: int
    ) -> OrderORM:

        new_order = OrderORM(
            owner_id=owner_id,
            title=title,
            description=description,
            budget_rub=budget_rub,
        )
        self.db.add(new_order)
        return new_order

    def get_all_orders_current_user(self, owner_id: str) -> list[OrderORM]:
        return list(
            self.db.scalars(
                select(OrderORM)
                .where(OrderORM.owner_id == owner_id)
                .order_by(OrderORM.created_at.desc())
            ).all()
        )

    def get_current_order_by_id(self, id: str) -> OrderORM | None:
        return self.db.scalar(select(OrderORM).where(OrderORM.id == id))

    def delete_order(self, id: str) -> None:

        order_for_delete = self.get_current_order_by_id(id)

        self.db.delete(order_for_delete)

    def update_status_order(self, id: str, status: str) -> OrderORM:

        order_for_update = self.get_current_order_by_id(id)

        order_for_update.status = status

        return order_for_update

    def get_all_orders(self) -> list[OrderORM]:
        return list(
            self.db.scalars(select(OrderORM).order_by(OrderORM.created_at.desc())).all()
        )

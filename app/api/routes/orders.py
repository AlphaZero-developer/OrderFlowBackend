from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException, status
from app.schemas.order import OrderCreateSchema, Order, OrderUpgradeSchema
from app.services.order import OrderService
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.api.dependencies import get_order_service

router = APIRouter(prefix="/api/v1")

security = HTTPBearer(auto_error=False)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateSchema,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    order_service: OrderService = Depends(get_order_service),
) -> Order:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Токен отсутствует")

    new_order = order_service.create_order(
        access_token=credentials.credentials,
        title=payload.title,
        description=payload.description,
        budget_rub=payload.budget_rub,
    )

    return new_order


@router.get("/orders", status_code=status.HTTP_200_OK)
def get_all_orders_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:

    if credentials is None:
        raise HTTPException(status_code=401, detail="Токен отсутствует")

    return order_service.get_all_orders_current_user(
        access_token=credentials.credentials
    )


@router.get("/orders/{id}", status_code=status.HTTP_200_OK)
def get_current_order(
    id: str,
    order_service: OrderService = Depends(get_order_service),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Order:

    if credentials is None:
        raise HTTPException(status_code=401, detail="Нету токена")

    return order_service.get_current_order(access_token=credentials.credentials, id=id)


@router.post("/orders/{id}/cancel")
def cancel_order(
    id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    order_service: OrderService = Depends(get_order_service),
) -> Order:

    if credentials is None:
        raise HTTPException(status_code=401, detail="Нету токена")

    return order_service.cancel_order(access_token=credentials.credentials, id=id)


@router.patch("/orders/{id}/status")
def update_status_order(
    id: str,
    payload: OrderUpgradeSchema,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    order_service: OrderService = Depends(get_order_service),
) -> Order:

    if credentials is None:
        raise HTTPException(status_code=401, detail="Нету токена")

    return order_service.update_status_order(
        access_token=credentials.credentials, id=id, status=payload.status
    )

from fastapi import APIRouter
from app.schemas.health import HealthSchema

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def return_status_backend() -> HealthSchema:
    return HealthSchema(status="ok")

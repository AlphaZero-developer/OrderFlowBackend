from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.user import router as users_router
from app.api.routes.orders import router as orders_router
from app.core.settings import get_settings

app = FastAPI()

app.include_router(router=health_router)
app.include_router(router=users_router)
app.include_router(router=orders_router)


settings = get_settings()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

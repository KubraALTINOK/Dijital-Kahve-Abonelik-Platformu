from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.shops import router as shops_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.users import router as users_router
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="KahveCell API", lifespan=lifespan)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(shops_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
def home() -> str:
    return "çalışıyor"

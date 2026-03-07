import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .presentation.routers.product_router import router as product_router
from .presentation.routers.product_category_router import router as product_category_router
from .presentation.routers.offer_router import router as offer_router
from .presentation.routers.sale_router import router as sale_router
from .presentation.routers.dashboard_router import router as dashboard_router
from .presentation.routers.auth_router import router as auth_router
from .presentation.routers.user_router import router as user_router
from .presentation.routers.audit_router import router as audit_router
from .presentation.routers.expense_category_router import router as expense_category_router
from .presentation.routers.expense_router import router as expense_router
from .presentation.routers.stock_router import router as stock_router
from .presentation.routers.health_router import router as health_router
from app.domain import *
from app.containers import Container
from app.infrastructure.middleware.http_logging_middleware import HttpLoggingMiddleware
from app.presentation.middleware.jwt_middleware import JWTMiddleware
from app.infrastructure.config.settings import settings
from app.infrastructure.logging import get_logger

container = Container()
container.wire()

# Inicializar logging
logger = container.logging()
logger.debug("Inicializando PizzaFiori API")

app = FastAPI(title="PizzaFiori API")

# Middleware de JWT (antes de los routers para validar tokens)
app.add_middleware(JWTMiddleware, logger=get_logger("auth.jwt"))

# Middleware de logging de requests
app.add_middleware(
    HttpLoggingMiddleware,
    logger=get_logger("http.external"),
    log_response_body=settings.debug,
    max_body_size=50_000,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear la carpeta si no existe (por seguridad al arrancar)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Agregar los routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(product_category_router)
app.include_router(offer_router)
app.include_router(sale_router)
app.include_router(dashboard_router)
app.include_router(audit_router)
app.include_router(expense_category_router)
app.include_router(expense_router)
app.include_router(stock_router)
app.include_router(health_router)

# Servir el frontend buildeado (producción) si existe el directorio dist/.
# Cuando corre como PyInstaller bundle, __file__ está dentro del temp dir de
# extracción; navegar desde sys.executable (el .exe en backend/) en su lugar.
import sys as _sys
if getattr(_sys, 'frozen', False):
    _FRONTEND_DIST = Path(_sys.executable).resolve().parent.parent / "frontend" / "dist"
else:
    _FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    from fastapi.staticfiles import StaticFiles as _StaticFiles
    app.mount("/", _StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="spa")
else:
    @app.get("/")
    def root():
        return {"mensaje": "API PizzaFiori funcionando"}


import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .presentation.routers.product_router import router as product_router
from .presentation.routers.category_router import router as category_router
from .presentation.routers.offer_router import router as offer_router
from .presentation.routers.sale_router import router as sale_router
from app.domain import *
from app.containers import Container
from app.infrastructure.middleware.http_logging_middleware import HttpLoggingMiddleware
from app.infrastructure.config.settings import settings
from app.infrastructure.logging import get_logger

container = Container()
container.wire()

# Inicializar logging
logger = container.logging()
logger.debug("Inicializando PizzaFiori API")

app = FastAPI(title="PizzaFiori API")

# Middleware de logging de requests
app.add_middleware(
    HttpLoggingMiddleware,
    logger=get_logger("http.external"),
    log_response_body=settings.debug,
    max_body_size=50_000,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear la carpeta si no existe (por seguridad al arrancar)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Agregar el router
app.include_router(product_router)
app.include_router(category_router)
app.include_router(offer_router)
app.include_router(sale_router)

# Ruta raíz opcional
@app.get("/")
def root():
    return {"mensaje": "API PizzaFiori funcionando"}

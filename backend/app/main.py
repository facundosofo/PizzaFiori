import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import http_exception_handler
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


def _run_migrations() -> None:
    """Ejecuta `alembic upgrade head` programáticamente.

    Cuando corre como bundle PyInstaller, los archivos de alembic están en
    sys._MEIPASS.  En desarrollo se usan las rutas normales del proyecto.
    """
    from alembic.config import Config
    from alembic import command as alembic_command

    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent.parent

    cfg = Config(str(base_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(base_dir / "alembic"))
    alembic_command.upgrade(cfg, "head")


async def _auto_seed() -> None:
    """Ejecuta el seed inicial solo si el sistema está completamente vacío."""
    import traceback
    from app.infrastructure.database import AsyncSessionLocal
    from sqlalchemy import text

    TABLAS = [
        '"productos_categorias"',
        '"Productos"',
        '"Ofertas"',
        '"gastos_categorias"',
        '"Usuarios"',
    ]

    try:
        async with AsyncSessionLocal() as session:
            for tabla in TABLAS:
                result = await session.execute(text(f"SELECT 1 FROM {tabla} LIMIT 1"))
                if result.first() is not None:
                    logger.info("Seed omitido — datos ya existen en %s.", tabla)
                    return

        logger.info("Sistema vacío — ejecutando seed inicial...")
        import seeds
        await seeds.main()
        logger.info("Seed completado.")

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"\n[AUTO-SEED ERROR] {exc}\n{tb}", file=sys.stderr, flush=True)
        logger.error("Error en auto-seed (la app continua): %s\n%s", exc, tb)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aplicando migraciones de base de datos...")
    try:
        _run_migrations()
        logger.info("Migraciones aplicadas correctamente.")
    except Exception as exc:
        logger.error(f"Error al aplicar migraciones (la app continua): {exc}")
    await _auto_seed()
    yield


# Calcular ruta del frontend. En bundle PyInstaller el exe vive en
# C:\PizzaFiori\backend\dist\pizzafiori.exe -> parent*3 = C:\PizzaFiori\
if getattr(sys, 'frozen', False):
    _FRONTEND_DIST = Path(sys.executable).resolve().parent.parent.parent / "frontend" / "dist"
else:
    _FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


app = FastAPI(title="PizzaFiori API", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def _spa_exception_handler(request: Request, exc: HTTPException):
    """Para F5 en rutas con auth (401/403): el browser manda Accept: text/html
    pero sin token. Devolvemos index.html para que React cargue y rediriga a /login.
    Axios siempre manda Accept: application/json, nunca entra por aqui."""
    if exc.status_code in (401, 403):
        accept = request.headers.get("Accept", "")
        if "text/html" in accept and _FRONTEND_DIST.is_dir():
            return FileResponse(
                str(_FRONTEND_DIST / "index.html"),
                headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
            )
    return await http_exception_handler(request, exc)


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

if _FRONTEND_DIST.is_dir():
    # Montar los assets estaticos directamente para MIME types correctos
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="spa-assets")
    # Catch-all SPA route — se registra DESPUES de todos los routers de API,
    # por lo que solo captura paths que ningun router reconoce.
    # Sirve archivos estaticos reales (JS/CSS/imagenes) o index.html para
    # cualquier ruta de React Router (dashboard, reportes, auditoria, etc.)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Archivo estatico real: JS, CSS, PNG, SVG, favicon, etc.
        candidate = (_FRONTEND_DIST / full_path).resolve()
        dist_root = _FRONTEND_DIST.resolve()
        if str(candidate).startswith(str(dist_root)) and candidate.is_file():
            return FileResponse(str(candidate))
        # Todo lo demas (rutas de React Router) -> index.html
        return FileResponse(
            str(_FRONTEND_DIST / "index.html"),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
        )
else:
    @app.get("/")
    def root():
        return {"mensaje": "API PizzaFiori funcionando"}


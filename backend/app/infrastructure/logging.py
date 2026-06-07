import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

import structlog
from structlog.typing import EventDict


# ----------------------
# Procesadores
# ----------------------

def add_app_context(_: object, __: str, event_dict: EventDict) -> EventDict:
    """Agrega metadatos de la aplicación a todos los logs."""
    from app.infrastructure.config.settings import settings

    event_dict["app"] = settings.app_name
    event_dict["env"] = settings.env
    return event_dict


SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "x-csrf-token",
    "proxy-authorization",
}


def sanitize_headers(headers: dict[str, str], redacted: str = "***") -> dict[str, str]:
    """Redacta headers sensibles antes de loguearlos."""
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            sanitized[key] = redacted
        else:
            sanitized[key] = value
    return sanitized


# ----------------------
# Configuración principal
# ----------------------

def configure_logging() -> structlog.BoundLogger:
    """Configura structlog con salida JSON para toda la app."""
    from app.infrastructure.config.settings import settings

    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # --- Handlers ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    file_handler = _make_rotating_handler(log_dir / "app.log", log_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Logger separado para HTTP (no propaga al root)
    external_logger = logging.getLogger("http.external")
    external_logger.setLevel(log_level)
    external_logger.propagate = False
    external_logger.addHandler(_make_rotating_handler(log_dir / "app-http.log", log_level))

    # --- Procesadores compartidos ---
    # Usados por structlog para logs propios de la app
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso", utc=False, key="timestamp"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Usados por ProcessorFormatter para logs de librerías terceras
    foreign_pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso", utc=False, key="timestamp"),
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]

    # Siempre JSON — legible por cualquier plataforma de logs
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=foreign_pre_chain,
    )

    for handler in [console_handler, file_handler]:
        handler.setFormatter(formatter)

    for handler in external_logger.handlers:
        handler.setFormatter(formatter)

    # --- Configurar structlog ---
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# ----------------------
# Helpers internos
# ----------------------

def _make_rotating_handler(path: Path, level: int) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        filename=path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.suffix = "%Y%m%d"
    handler.namer = lambda name: name.replace(".log.", "-") + ".log"
    handler.setLevel(level)
    return handler


# ----------------------
# Obtener logger
# ----------------------

def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
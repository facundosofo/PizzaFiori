import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import structlog
from structlog.typing import EventDict

# ----------------------
# Renderer simple
# ----------------------
def plain_renderer(_: any, __: str, event_dict: dict) -> str:
    """
    Formatea logs en texto plano:
    [timestamp - correlation_id - LEVEL] mensaje + campos extra
    """
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    message = event_dict.pop("event", "")
    correlation_id = event_dict.pop("request_id", "-")

    # Eliminar campos internos
    event_dict.pop("_prefix", None)
    event_dict.pop("logger", None)

    log_line = f"[{timestamp} - {correlation_id} - {level}] {message}"

    # Agregar extras si existen
    if event_dict:
        extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
        log_line += f" {extras}"

    return log_line

# ----------------------
# Procesadores
# ----------------------
def add_app_context(logger: any, method_name: str, event_dict: EventDict) -> EventDict:
    """Agrega app y env a todos los logs."""
    # Lazy import para evitar problemas de circular imports
    from app.infrastructure.config.settings import settings
    return event_dict

def add_log_prefix(logger: any, method_name: str, event_dict: EventDict) -> EventDict:
    """Prefijo por registro: [timestamp - correlation_id - LEVEL]"""
    timestamp = event_dict.get("timestamp", "")
    correlation_id = event_dict.get("request_id", "-")
    level = event_dict.get("level", "info").upper()
    event_dict["_prefix"] = f"[{timestamp} - {correlation_id} - {level}]"
    return event_dict

# ----------------------
# Configuración principal
# ----------------------
def configure_logging() -> structlog.BoundLogger:
    """Configura structlog simplificado para toda la app."""
    from app.infrastructure.config.settings import settings

    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Handlers para el logger principal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y%m%d"
    file_handler.namer = lambda name: name.replace(".log.", "-") + ".log"
    file_handler.setLevel(log_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Logger separado para HTTP requests (external log)
    external_logger = logging.getLogger("http.external")
    external_logger.setLevel(log_level)
    external_logger.propagate = False 
    
    external_file_handler = TimedRotatingFileHandler(
        filename=log_dir / "app-http.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    external_file_handler.suffix = "%Y%m%d"
    external_file_handler.namer = lambda name: name.replace(".log.", "-") + ".log"
    external_file_handler.setLevel(log_level)

    # Procesadores comunes
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        add_log_prefix,
        structlog.processors.TimeStamper(fmt="iso", utc=False, key="timestamp"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Formateadores
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=plain_renderer if settings.debug else structlog.processors.JSONRenderer(),
        foreign_pre_chain=processors,
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    external_file_handler.setFormatter(formatter)
    
    # Agregar handler al logger externo
    external_logger.addHandler(external_file_handler)

    # Configurar structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# ----------------------
# Obtener logger
# ----------------------
def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)

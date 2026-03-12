import io
import os
import aiofiles
from fastapi import UploadFile, HTTPException
from uuid import uuid4
from pathlib import Path
from typing import Optional

try:
    from PIL import Image as _PIL_Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

_MAX_IMAGE_PX = 800  # Máximo lado en píxeles tras resize
_JPEG_QUALITY = 80   # Calidad JPEG (0-100)

class FileService:
    def __init__(self, base_path: str = "uploads/productos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {".jpg", ".jpeg", ".png"}
        self.max_size = 5 * 1024 * 1024  # 5MB

    async def save_file(self, file: UploadFile, filename_base: Optional[str] = None) -> str:
        # 1. Validar Extensión usando pathlib
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="Extensión no permitida")

        # 2. Validar MIME Type (Doble seguridad)
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="El contenido no es una imagen válida")

        # 3. Leer contenido y validar tamaño
        contents = await file.read()
        if len(contents) > self.max_size:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 5MB)")

        # 3.5 Redimensionar y comprimir con Pillow (evita subir fotos de 4MB)
        if _HAS_PIL:
            try:
                img = _PIL_Image.open(io.BytesIO(contents))
                # Convertir a RGB (descarta canal alfa y modos raros)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Reducir solo si supera el máximo; mantiene proporción
                if img.width > _MAX_IMAGE_PX or img.height > _MAX_IMAGE_PX:
                    img.thumbnail((_MAX_IMAGE_PX, _MAX_IMAGE_PX), _PIL_Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=_JPEG_QUALITY, optimize=True)
                contents = buf.getvalue()
                file_ext = '.jpg'
            except Exception:
                pass  # Si Pillow falla, se sube el original sin redimensionar

        # 4. Determinar nombre de archivo y ruta
        if filename_base:
            # Nombre basado en SKU: siempre .jpg para extension unificada
            filename = f"{filename_base}.jpg"
            file_path = self.base_path / filename
            mode = "wb"
        else:
            # Sin SKU: nombre UUID con creación exclusiva para evitar colisiones
            filename = f"{uuid4().hex}{file_ext}"
            file_path = self.base_path / filename
            mode = "xb"

        # 5. Guardado asíncrono
        async with aiofiles.open(file_path, mode=mode) as f:
            await f.write(contents)

        return str(file_path).replace("\\", "/") # Normalizar ruta para BD

    def delete_file(self, file_path: str) -> None:
        if not file_path:
            return
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except OSError as e:
            # Loguear pero no propagar: el archivo viejo huérfano no debe romper la operación
            import logging
            logging.getLogger(__name__).warning(
                "No se pudo eliminar archivo: %s — %s", file_path, e
            )
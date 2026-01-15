import os
import aiofiles
from fastapi import UploadFile, HTTPException
from uuid import uuid4
from pathlib import Path

class FileService:
    def __init__(self, base_path: str = "uploads/productos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {".jpg", ".jpeg", ".png"}
        self.max_size = 5 * 1024 * 1024  # 5MB

    async def save_file(self, file: UploadFile) -> str:
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

        # 4. Generar nombre único y ruta
        filename = f"{uuid4().hex}{file_ext}"
        file_path = self.base_path / filename

        # 5. Guardado Asíncrono para no bloquear el servidor
        async with aiofiles.open(file_path, mode="wb") as f:
            await f.write(contents)

        return str(file_path).replace("\\", "/") # Normalizar ruta para BD

    def delete_file(self, file_path: str):
        if file_path:
            path = Path(file_path)
            if path.exists():
                path.unlink()
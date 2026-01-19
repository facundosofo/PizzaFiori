import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .presentation.routers.product_router import router as product_router
from .presentation.routers.category_router import router as category_router
from app.domain import *

app = FastAPI(title="PizzaFiori API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
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

# Ruta raíz opcional
@app.get("/")
def root():
    return {"mensaje": "API PizzaFiori funcionando"}

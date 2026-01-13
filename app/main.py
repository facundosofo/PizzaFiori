from fastapi import FastAPI
from .presentation.routers.product_router import router as product_router

app = FastAPI(title="PizzaFiori API")

# Agregar el router
app.include_router(product_router)

# Ruta raíz opcional
@app.get("/")
def root():
    return {"mensaje": "API PizzaFiori funcionando"}

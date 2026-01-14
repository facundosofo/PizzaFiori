from fastapi import FastAPI
from .presentation.routers.product_router import router as product_router
from .presentation.routers.category_router import router as category_router

app = FastAPI(title="PizzaFiori API")

# Agregar el router
app.include_router(product_router)
app.include_router(category_router)

# Ruta raíz opcional
@app.get("/")
def root():
    return {"mensaje": "API PizzaFiori funcionando"}

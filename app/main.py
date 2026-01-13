from fastapi import FastAPI

app = FastAPI(
    title="PizzaFiori API",
    description="API para gestión de stock y ventas de la pizzería Pizza Fiori",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "PizzaFiori API funcionando 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

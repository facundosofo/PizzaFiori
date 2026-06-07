# PizzaFiori

Aplicación web desarrollada para la gestión de una pizzería familiar, pensada para usuarios sin conocimientos técnicos.

## 📚 Documentación Completa

Toda la documentación del proyecto se encuentra en la carpeta [`docs/`](docs/README.md).

### Inicio Rápido

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Configurar .env
   alembic upgrade head
   uvicorn app.main:app --reload  # o: hypercorn app.main:app --reload --bind 0.0.0.0:8000 (recomendado, soporta HTTP/2)
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   # Configurar .env
   npm run dev
   ```

### Documentación Disponible

- **[📖 Documentación Principal](docs/README.md)** - Índice completo de documentación
- **[🏗️ Arquitectura](docs/ARQUITECTURA.md)** - Arquitectura Clean Architecture
- **[🗄️ Base de Datos](docs/DIAGRAMA_BASE_DATOS.md)** - Modelo de datos y relaciones
- **[⚙️ Instalación](docs/INSTALACION.md)** - Guía paso a paso de instalación
- **[🔌 API](docs/API.md)** - Documentación completa de endpoints
- **[🧪 Testing](docs/TESTING.md)** - Suite de tests y guía de testing
- **[➕ Crear Endpoints](docs/GUIA_CREAR_ENDPOINT.md)** - Guía para agregar endpoints al backend
- **[🎨 Crear Páginas Frontend](docs/GUIA_CREAR_PAGINA_FRONTEND.md)** - Guía para crear páginas en React

## 🛠️ Stack Tecnológico

- **Backend:** FastAPI (Python), SQLAlchemy, SQL Server
- **Frontend:** React 19, TypeScript, Vite
- **Arquitectura:** Clean Architecture
- **Testing:** pytest, 86% coverage, 202 tests

## 🧪 Testing

```bash
cd backend

# Ejecutar todos los tests
pytest tests/

# Con coverage
pytest tests/ --cov=app --cov-report=term-missing

# Solo routers/services/schemas
pytest tests/routers/ -v
pytest tests/application/ -v
pytest tests/presentation/schemas/ -v
```

**Estado:** ✅ 202 tests pasando | 86% coverage  
**Documentación completa:** [docs/TESTING.md](docs/TESTING.md)

## 📁 Estructura del Proyecto

```
PizzaFiori/
├── backend/          # API FastAPI
├── frontend/         # Aplicación React
└── docs/            # Documentación completa
```

Para más información, consulta la [documentación completa](docs/README.md).

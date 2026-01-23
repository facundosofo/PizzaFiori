# Documentación del Proyecto PizzaFiori

Bienvenido a la documentación completa del proyecto **PizzaFiori**, una aplicación web desarrollada para la gestión de una pizzería familiar.

## 📋 Índice de Documentación

### Documentación Principal

- **[Arquitectura del Sistema](ARQUITECTURA.md)**  
  Descripción detallada de la arquitectura Clean Architecture implementada, capas, patrones de diseño y flujos de datos.

- **[Diagrama de Base de Datos](DIAGRAMA_BASE_DATOS.md)**  
  Modelo entidad-relación completo, descripción de tablas, relaciones, constraints y optimizaciones.

- **[Guía de Instalación](INSTALACION.md)**  
  Instrucciones paso a paso para configurar y ejecutar el proyecto en tu entorno local.

- **[Documentación de API](API.md)**  
  Referencia completa de todos los endpoints disponibles, parámetros, respuestas y ejemplos de uso.

- **[Guía para Crear Endpoints](GUIA_CREAR_ENDPOINT.md)**  
  Guía detallada paso a paso para agregar nuevos endpoints siguiendo la arquitectura del proyecto.

- **[Guía para Crear Páginas Frontend](GUIA_CREAR_PAGINA_FRONTEND.md)**  
  Guía detallada paso a paso para crear nuevas páginas y componentes en el frontend React.

- **[Testing](TESTING.md)**  
  Suite completa de tests unitarios, guía de testing, comandos útiles y mejores prácticas.

## 🎯 Descripción del Proyecto

PizzaFiori es una aplicación web desarrollada para gestionar productos, categorías, precios y ofertas de una pizzería. Está diseñada para ser simple de usar, incluso para usuarios sin conocimientos técnicos.

### Características Principales

- ✅ Gestión de productos con imágenes
- ✅ Categorización de productos
- ✅ Precios escalonados por cantidad
- ✅ Sistema de ofertas/combos
- ✅ Interfaz web moderna y responsive
- ✅ API REST completa
- ✅ Arquitectura escalable y mantenible

## 🛠️ Stack Tecnológico

### Backend

- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy (Async)
- **Base de Datos:** SQL Server (MSSQL)
- **Migraciones:** Alembic
- **Dependency Injection:** dependency-injector
- **Logging:** structlog
- **Validación:** Pydantic
- **Testing:** pytest, pytest-asyncio, pytest-cov (86% coverage)

### Frontend

- **Framework:** React 19
- **Lenguaje:** TypeScript
- **Build Tool:** Vite
- **Routing:** React Router DOM
- **Animaciones:** Framer Motion

### Arquitectura

- **Patrón:** Clean Architecture
- **Patrones de Diseño:**
  - Repository Pattern
  - Unit of Work Pattern
  - Dependency Injection
  - Service Layer Pattern

## 📁 Estructura del Proyecto

```
PizzaFiori/
├── backend/                 # Backend FastAPI
│   ├── app/
│   │   ├── application/     # Capa de aplicación (servicios)
│   │   ├── domain/          # Capa de dominio (modelos, repositorios abstractos)
│   │   ├── infrastructure/  # Capa de infraestructura (BD, repositorios concretos)
│   │   ├── presentation/    # Capa de presentación (routers, schemas)
│   │   ├── containers.py    # Configuración de Dependency Injection
│   │   └── main.py          # Punto de entrada
│   ├── tests/               # Suite de tests (202 tests, 86% coverage)
│   │   ├── application/     # Tests de servicios (64 tests)
│   │   ├── presentation/    # Tests de schemas (80 tests)
│   │   ├── routers/         # Tests de endpoints (58 tests)
│   │   ├── conftest.py      # Fixtures globales
│   │   └── helpers.py       # Utilidades para tests
│   ├── alembic/             # Migraciones de base de datos
│   ├── logs/                # Archivos de log
│   ├── uploads/             # Archivos subidos (imágenes)
│   ├── pytest.ini           # Configuración de pytest
│   └── requirements.txt     # Dependencias Python
│
├── frontend/                 # Frontend React
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/           # Páginas de la aplicación
│   │   ├── services/        # Servicios de API
│   │   ├── types/           # Tipos TypeScript
│   │   └── styles/          # Estilos CSS
│   └── package.json         # Dependencias Node.js
│
└── docs/                     # Documentación del proyecto
    ├── README.md            # Este archivo
    ├── ARQUITECTURA.md      # Arquitectura del sistema
    ├── DIAGRAMA_BASE_DATOS.md  # Modelo de datos
    ├── INSTALACION.md       # Guía de instalación
    ├── API.md               # Documentación de API
    ├── TESTING.md           # Suite de tests y guía de testing
    ├── GUIA_CREAR_ENDPOINT.md  # Guía para crear endpoints
    └── GUIA_CREAR_PAGINA_FRONTEND.md  # Guía para crear páginas frontend
```

## 🚀 Inicio Rápido

1. **Clonar el repositorio** (si aplica)
2. **Configurar el backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Configurar variables de entorno (.env)
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

3. **Configurar el frontend:**
   ```bash
   cd frontend
   npm install
   # Configurar variables de entorno
   npm run dev
   ```

Para instrucciones detalladas, consulta la [Guía de Instalación](INSTALACION.md).

## 📚 Documentación Adicional

### Para Desarrolladores

- **[Arquitectura](ARQUITECTURA.md)**: Entiende cómo está estructurado el código
- **[Guía para Crear Endpoints](GUIA_CREAR_ENDPOINT.md)**: Aprende a agregar nuevas funcionalidades al backend
- **[Guía para Crear Páginas Frontend](GUIA_CREAR_PAGINA_FRONTEND.md)**: Aprende a crear nuevas páginas y componentes en React
- **[API](API.md)**: Consulta todos los endpoints disponibles

### Para Administradores

- **[Instalación](INSTALACION.md)**: Configura el proyecto desde cero
- **[Diagrama de Base de Datos](DIAGRAMA_BASE_DATOS.md)**: Entiende la estructura de datos

## 🔧 Configuración

### Variables de Entorno Backend

Crea un archivo `.env` en `backend/` con:

```env
app_name=PizzaFiori
env=development
debug=true
db_host=localhost
db_name=PizzaFiori
db_driver={ODBC Driver 17 for SQL Server}
api_port=8000
log_dir=logs
log_file=app.log
```

### Variables de Entorno Frontend

Crea un archivo `.env` en `frontend/` con:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📝 Convenciones del Proyecto

### Nomenclatura

- **Modelos:** Singular en inglés (`Product`, `Category`, `Offer`)
- **Tablas:** Plural en español (`Productos`, `Categorias`, `Ofertas`)
- **Servicios:** `[Entity]Service` (`ProductService`, `CategoryService`)
- **Repositorios:** `Abstract[Entity]Repository` y `SqlAlchemy[Entity]Repository`
- **Schemas:** `[Entity][Action]Request/Response` (`ProductoCreateRequest`)

### Estructura de Código

- Cada módulo sigue la estructura de Clean Architecture
- Los servicios retornan `ServiceResult` para manejo consistente de errores
- Se usa logging estructurado con `structlog`
- Las transacciones se gestionan mediante Unit of Work

## 🧪 Testing

(Sección a completar cuando se implementen tests)

## 🤝 Contribución

(Sección a completar con guías de contribución)

## 📄 Licencia

(Sección a completar con información de licencia)

## 📞 Soporte

Para consultas o problemas:
- Revisa la documentación en esta carpeta
- Consulta los logs en `backend/logs/`
- Revisa la documentación de FastAPI: https://fastapi.tiangolo.com/

## 🔗 Enlaces Útiles

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Última actualización:** Enero 2026

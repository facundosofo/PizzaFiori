# Guía de Instalación - PizzaFiori

Esta guía te ayudará a configurar y ejecutar el proyecto PizzaFiori en tu entorno local.

## 📋 Requisitos Previos

### Software Necesario

- **Python 3.9+** (recomendado 3.11 o superior)
- **Node.js 18+** y npm (o yarn)
- **SQL Server** (cualquier versión reciente) o SQL Server Express
- **ODBC Driver 17 for SQL Server** (o superior)
- **Git** (opcional, para clonar el repositorio)

### Verificar Instalaciones

```bash
# Verificar Python
python --version
# Debe mostrar Python 3.9 o superior

# Verificar Node.js
node --version
# Debe mostrar v18 o superior

# Verificar npm
npm --version
```

## 🗄️ Configuración de Base de Datos

### 1. Instalar SQL Server

Si no tienes SQL Server instalado:

1. Descarga **SQL Server Express** (gratuito) desde: https://www.microsoft.com/sql-server/sql-server-downloads
2. Instala siguiendo el asistente
3. Durante la instalación, configura la autenticación mixta (Windows + SQL Server)

### 2. Instalar ODBC Driver

1. Descarga **ODBC Driver 17 for SQL Server** desde: https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Instala el driver
3. Verifica la instalación ejecutando:
   ```bash
   odbcinst -q -d
   ```
   Debe mostrar el driver instalado.

### 3. Crear la Base de Datos

1. Abre **SQL Server Management Studio (SSMS)** o usa **sqlcmd**
2. Conéctate al servidor SQL Server
3. Ejecuta el siguiente comando para crear la base de datos:

```sql
CREATE DATABASE PizzaFiori;
GO
```

O usando sqlcmd desde la terminal:

```bash
sqlcmd -S localhost -Q "CREATE DATABASE PizzaFiori"
```

## 🔧 Configuración del Backend

### 1. Navegar al Directorio Backend

```bash
cd backend
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio `backend/` con el siguiente contenido:

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

**Notas importantes:**
- `db_host`: Cambia `localhost` si tu SQL Server está en otro servidor
- `db_driver`: Verifica el nombre exacto del driver con `odbcinst -q -d`
- Si usas autenticación SQL Server en lugar de Windows Authentication, necesitarás modificar la cadena de conexión en `database.py`

### 5. Ejecutar Migraciones

Las migraciones crean las tablas en la base de datos:

```bash
# Aplicar todas las migraciones
alembic upgrade head

# Ver el estado de las migraciones
alembic current

# Si necesitas revertir (cuidado)
alembic downgrade -1
```

### 6. Verificar la Conexión

Antes de ejecutar el servidor, verifica que la conexión a la base de datos funciona:

```bash
python -c "from app.infrastructure.database import engine; import asyncio; asyncio.run(engine.connect())"
```

Si no hay errores, la conexión está correcta.

### 7. Ejecutar el Servidor Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: **http://localhost:8000**

### 8. Verificar el Backend

- Abre tu navegador en: http://localhost:8000
- Deberías ver: `{"mensaje": "API PizzaFiori funcionando"}`
- Documentación interactiva: http://localhost:8000/docs
- Esquema alternativo: http://localhost:8000/redoc

## 🎨 Configuración del Frontend

### 1. Navegar al Directorio Frontend

```bash
cd frontend
```

### 2. Instalar Dependencias

```bash
npm install
```

### 3. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio `frontend/` con:

```env
VITE_API_BASE_URL=http://localhost:8000
```

**Nota:** Asegúrate de que la URL coincida con la del backend.

### 4. Ejecutar el Servidor de Desarrollo

```bash
npm run dev
```

El frontend estará disponible en: **http://localhost:5173**

### 5. Verificar el Frontend

- Abre tu navegador en: http://localhost:5173
- Deberías ver la página principal de PizzaFiori

## ✅ Verificación Completa

### Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] Node.js 18+ instalado
- [ ] SQL Server instalado y ejecutándose
- [ ] ODBC Driver instalado
- [ ] Base de datos `PizzaFiori` creada
- [ ] Entorno virtual de Python creado y activado
- [ ] Dependencias del backend instaladas
- [ ] Archivo `.env` del backend configurado
- [ ] Migraciones aplicadas correctamente
- [ ] Backend ejecutándose en http://localhost:8000
- [ ] Dependencias del frontend instaladas
- [ ] Archivo `.env` del frontend configurado
- [ ] Frontend ejecutándose en http://localhost:5173

## 🐛 Solución de Problemas Comunes

### Error: "No se puede conectar a SQL Server"

**Posibles causas:**
1. SQL Server no está ejecutándose
   - **Solución:** Inicia el servicio SQL Server desde "Servicios" de Windows

2. Nombre del servidor incorrecto
   - **Solución:** Verifica el nombre del servidor en `db_host` del `.env`

3. ODBC Driver no encontrado
   - **Solución:** Verifica el nombre exacto del driver con `odbcinst -q -d`

4. Autenticación incorrecta
   - **Solución:** Si usas autenticación SQL Server, modifica `database.py` para incluir usuario y contraseña

### Error: "ModuleNotFoundError" en Python

**Solución:**
```bash
# Asegúrate de estar en el entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstala las dependencias
pip install -r requirements.txt
```

### Error: "Cannot find module" en Node.js

**Solución:**
```bash
# Elimina node_modules y reinstala
rm -rf node_modules package-lock.json
npm install
```

### Error: "Alembic: Can't locate revision"

**Solución:**
```bash
# Verifica que estás en el directorio backend
cd backend

# Verifica el estado de las migraciones
alembic current

# Si es necesario, inicializa Alembic
alembic upgrade head
```

### Error: CORS en el Frontend

Si ves errores de CORS al hacer peticiones desde el frontend:

1. Verifica que `VITE_API_BASE_URL` en el frontend apunta al backend correcto
2. Verifica que el backend tiene configurado CORS en `main.py`:
   ```python
   allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
   ```

### Error: "Port already in use"

Si el puerto 8000 o 5173 está ocupado:

**Backend:**
```bash
# Usa otro puerto
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
# Vite usará automáticamente otro puerto si 5173 está ocupado
# O especifica uno manualmente en vite.config.ts
```

## 📝 Comandos Útiles

### Backend

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Ejecutar servidor
uvicorn app.main:app --reload

# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Ver logs
# Los logs se guardan en backend/logs/
```

### Frontend

```bash
# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev

# Compilar para producción
npm run build

# Preview de producción
npm run preview
```

## 🔐 Configuración de Producción

Para producción, considera:

1. **Variables de entorno:**
   - Cambiar `debug=false`
   - Cambiar `env=production`
   - Usar credenciales seguras para la base de datos

2. **Base de datos:**
   - Usar una instancia de SQL Server dedicada
   - Configurar backups automáticos
   - Usar conexiones encriptadas

3. **Seguridad:**
   - Configurar HTTPS
   - Implementar autenticación si es necesario
   - Configurar CORS apropiadamente

4. **Logging:**
   - Configurar rotación de logs
   - Configurar niveles de log apropiados

## 📚 Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Alembic](https://alembic.sqlalchemy.org/)
- [Documentación de Vite](https://vitejs.dev/)
- [Documentación de React](https://react.dev/)

## 🆘 Obtener Ayuda

Si encuentras problemas:

1. Revisa los logs en `backend/logs/`
2. Verifica la configuración de variables de entorno
3. Consulta la documentación en `docs/`
4. Revisa los issues conocidos (si aplica)

---

**Última actualización:** Enero 2026

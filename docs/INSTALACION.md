# Guía de Instalación - PizzaFiori

Esta guía te ayudará a configurar y ejecutar el proyecto PizzaFiori en tu entorno local.

## 📋 Requisitos Previos

### Software Necesario

- **Python 3.9+** (recomendado 3.11 o superior)
- **Node.js 18+** y npm (o yarn)
- **PostgreSQL 16+**
- **mkcert** (para certificados SSL de desarrollo)
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

### 1. Instalar PostgreSQL

Si no tienes PostgreSQL instalado:

1. Descarga **PostgreSQL 16+** desde: https://www.postgresql.org/download/
2. Instala siguiendo el asistente (guarda la contraseña del superusuario `postgres`)
3. Asegúrate de que el servicio esté corriendo (puerto 5432 por defecto)

### 2. Crear la Base de Datos y el Usuario

Abre una terminal como superusuario de PostgreSQL y ejecuta:

```bash
# Conectarse como superusuario
psql -U postgres
```

Dentro de `psql`:

```sql
-- Crear usuario de la aplicación
CREATE USER pizzafiori_user WITH PASSWORD 'tu_contraseña_segura';

-- Crear la base de datos
CREATE DATABASE pizzafiori OWNER pizzafiori_user;

-- Salir
\q
```

O en una sola línea desde la terminal:

```bash
psql -U postgres -c "CREATE USER pizzafiori_user WITH PASSWORD 'tu_contraseña_segura';"
psql -U postgres -c "CREATE DATABASE pizzafiori OWNER pizzafiori_user;"
```

### 3. Verificar la Conexión

```bash
psql -U pizzafiori_user -d pizzafiori -h localhost
```

Si se conecta sin errores, la base de datos está lista.

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

# Base de datos PostgreSQL
db_host=localhost
db_port=5432
db_name=pizzafiori
db_user=pizzafiori_user
db_password=tu_contraseña_segura

api_port=8000
log_dir=logs
log_file=app.log

# JWT (requerido)
JWT_SECRET=cambia_esto_por_un_secreto_largo_y_aleatorio

# SSL (desarrollo local)
SSL_KEY_FILE=.\certs\localhost+2-key.pem
SSL_CERT_FILE=.\certs\localhost+2.pem
```

**Notas importantes:**
- `db_host` / `db_port`: Cambia los valores si PostgreSQL corre en otro servidor o puerto
- `db_user` / `db_password`: Usa las credenciales creadas en el paso anterior
- `JWT_SECRET`: Genera un valor aleatorio largo (mínimo 32 caracteres). Puedes usar `python -c "import secrets; print(secrets.token_hex(32))"`
- `SSL_KEY_FILE` / `SSL_CERT_FILE`: Apuntan a los certificados en `backend/certs/` (ver paso 5)

### 5. Configurar Certificados SSL

El backend y el frontend corren sobre **HTTPS** en desarrollo. Los certificados ya están incluidos en `backend/certs/`.

Si necesitas regenerarlos, instala `mkcert` y ejecuta desde el directorio `backend/certs/`:

```bash
# Instalar mkcert (solo una vez por máquina)
# Windows (con Chocolatey)
choco install mkcert

# Instalar la CA local (solo una vez)
mkcert -install

# Generar certificados para localhost
cd backend\certs
mkcert localhost 127.0.0.1 ::1
```

Esto genera `localhost+2-key.pem` y `localhost+2.pem` en el directorio `certs/`.

### 6. Ejecutar Migraciones

Las migraciones crean las tablas en la base de datos:

```bash
# Aplicar todas las migraciones
alembic upgrade head

# Ver el estado de las migraciones
alembic current

# Si necesitas revertir (cuidado)
alembic downgrade -1
```

### 7. Verificar la Conexión a la Base de Datos

Antes de ejecutar el servidor, verifica que la conexión a PostgreSQL funciona:

```bash
python -c "from app.infrastructure.database import engine; import asyncio; asyncio.run(engine.connect())"
```

Si no hay errores, la conexión está correcta.

### 8. Ejecutar el Servidor Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  --ssl-keyfile .\certs\localhost+2-key.pem \
  --ssl-certfile .\certs\localhost+2.pem
```

En Windows (PowerShell):

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 `
  --ssl-keyfile .\certs\localhost+2-key.pem `
  --ssl-certfile .\certs\localhost+2.pem
```

El servidor estará disponible en: **https://localhost:8000**

### 9. Verificar el Backend

- Abre tu navegador en: https://localhost:8000
- Deberías ver: `{"mensaje": "API PizzaFiori funcionando"}`
- Documentación interactiva: https://localhost:8000/docs
- Esquema alternativo: https://localhost:8000/redoc

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
VITE_API_BASE_URL=https://localhost:8000

# Certificados SSL para el servidor de desarrollo
VITE_CERT_KEY_PATH=../backend/certs/localhost+2-key.pem
VITE_CERT_PATH=../backend/certs/localhost+2.pem
```

**Nota:** Los certificados son los mismos que usa el backend. Si los regeneraste, las rutas deben apuntar al nuevo archivo.

### 4. Ejecutar el Servidor de Desarrollo

```bash
npm run dev
```

El frontend estará disponible en: **https://localhost:5173**

### 5. Verificar el Frontend

- Abre tu navegador en: https://localhost:5173
- Deberías ver la página principal de PizzaFiori
- Si el navegador muestra advertencia de certificado, acepta la excepción (solo ocurre si no ejecutaste `mkcert -install`)

## ✅ Verificación Completa

### Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] Node.js 18+ instalado
- [ ] PostgreSQL instalado y ejecutándose
- [ ] Base de datos y usuario PostgreSQL creados
- [ ] Certificados SSL generados en `backend/certs/`
- [ ] Entorno virtual de Python creado y activado
- [ ] Dependencias del backend instaladas
- [ ] Archivo `.env` del backend configurado (incluyendo `JWT_SECRET` y vars SSL)
- [ ] Migraciones aplicadas correctamente
- [ ] Backend ejecutándose en https://localhost:8000
- [ ] Dependencias del frontend instaladas
- [ ] Archivo `.env` del frontend configurado
- [ ] Frontend ejecutándose en https://localhost:5173

## 🐛 Solución de Problemas Comunes

### Error: "No se puede conectar a PostgreSQL"

**Posibles causas:**
1. PostgreSQL no está ejecutándose
   - **Solución:** Inicia el servicio PostgreSQL desde "Servicios" de Windows o ejecuta `pg_ctl start`

2. Credenciales incorrectas
   - **Solución:** Verifica `db_user` y `db_password` en el archivo `.env`

3. Base de datos o usuario no creados
   - **Solución:** Ejecuta nuevamente los comandos `psql` de la sección "Configuración de Base de Datos"

4. Puerto incorrecto
   - **Solución:** Verifica que `db_port=5432` en el `.env` (o el puerto que configuraste en PostgreSQL)

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

1. Verifica que `VITE_API_BASE_URL` en el frontend apunta a `https://localhost:8000`
2. Verifica que el backend tiene configurado CORS en `main.py`:
   ```python
   allow_origins=["https://localhost:5173"]
   ```
3. Asegúrate de que tanto el backend como el frontend corren sobre **HTTPS** (no mezcles HTTP y HTTPS)

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

# Ejecutar servidor con SSL (Windows PowerShell)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 `
  --ssl-keyfile .\certs\localhost+2-key.pem `
  --ssl-certfile .\certs\localhost+2.pem

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
   - Usar una instancia de PostgreSQL dedicada
   - Configurar backups automáticos con `pg_dump`
   - Usar conexiones encriptadas (SSL en PostgreSQL)

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

**Última actualización:** Marzo 2026

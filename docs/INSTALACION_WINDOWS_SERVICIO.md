# Guía de Instalación — PizzaFiori en Windows (Servicio Automático)

Esta guía está dividida en dos partes independientes:

- **Parte 1 · Desarrollador** — se realiza **una sola vez** en la máquina de desarrollo para generar el paquete entregable al cliente.
- **Parte 2 · Cliente** — se realiza **en la notebook del cliente** para instalar y poner en marcha el sistema.

---

## 📐 Arquitectura final

```
Navegador → https://pizzafiori.com.ar
               ↓   (hosts file: 127.0.0.1)
        Windows Service (NSSM)
               ↓
    pizzafiori.exe — puerto 443 — HTTPS
               ↓
    FastAPI (backend API)  +  frontend/dist/ (React buildeado)
```

Un único servicio de Windows — compilado con PyInstaller — sirve tanto la API como la interfaz web. El cliente **no necesita Python ni Node.js instalados**.

---

---

# 🧑‍💻 PARTE 1 — DESARROLLADOR

> Estos pasos se ejecutan **en la máquina del desarrollador**, no en el cliente.
> El resultado es un paquete `.zip` listo para entregar.

---

## 📋 Requisitos (máquina de desarrollo)

| Software | Versión mínima | Descarga |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |

> **Python**: durante la instalación, marcar **"Add Python to PATH"**.

### Verificar

Abrir **PowerShell** y ejecutar:

```powershell
python --version   # Python 3.11.x o superior
node --version     # v18.x o superior
npm --version
nssm version
```

---

## � D1 — Entorno Virtual Python e Instalar Dependencias

```powershell
cd C:\PizzaFiori\backend

# Crear entorno virtual
python -m venv .venv

# Activar
.venv\Scripts\Activate.ps1

# Si da error de política de ejecución, ejecutar primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependencias (incluye PyInstaller)
pip install -r requirements.txt
pip install pyinstaller
```

---

## 🎨 D2 — Buildear el Frontend

### D2.1 Configurar el `.env` del frontend

Abrir `C:\PizzaFiori\frontend\.env` y dejar el siguiente contenido:

```env
VITE_API_BASE_URL=
VITE_API_TARGET=https://pizzafiori.com.ar
VITE_CERT_KEY_PATH=
VITE_CERT_PATH=
```

> Las variables de certificado se dejan vacías porque en producción el frontend es un build estático.

### D2.2 Instalar dependencias y compilar

```powershell
cd C:\PizzaFiori\frontend
npm install
npm run build
```

Al finalizar se crea `C:\PizzaFiori\frontend\dist\`.

```powershell
Test-Path C:\PizzaFiori\frontend\dist\index.html
# Debe devolver: True
```

---

## 📦 D3 — Compilar el Backend con PyInstaller

PyInstaller empaqueta el backend junto con Python y todas sus dependencias en un **único archivo `.exe`**. El cliente **no necesita Python instalado**.

### D3.1 Compilar

Con el entorno virtual activo desde `backend\`:

```powershell
cd C:\PizzaFiori\backend
.venv\Scripts\Activate.ps1

pyinstaller pizzafiori.spec
```

Al finalizar se crea `backend\dist\pizzafiori.exe`. El proceso puede tardar 1-3 minutos.

```powershell
Test-Path C:\PizzaFiori\backend\dist\pizzafiori.exe
# Debe devolver: True
```

---

## 🗜️ D4 — Armar el Paquete Entregable

Copiar la siguiente estructura en una carpeta limpia y comprimir en un ZIP para entregar al cliente:

```
PizzaFiori-entregable\
├── backend\
│   ├── dist\
│   │   └── pizzafiori.exe        ← ejecutable compilado
│   ├── rename_imagenes.ps1       ← renombrador de imagenes
│   └── rename_imagenes.bat       ← doble clic para ejecutar
└── frontend\
    └── dist\                     ← build React (HTML/JS/CSS)
```

> **No incluir:** `.venv\`, `node_modules\`, código fuente, ni archivos `.env`.
> Los certificados y el `.env` los genera/configura el técnico directamente en el cliente.
> Las migraciones se ejecutan **automáticamente** la primera vez que arranca el servicio.

### Para actualizaciones posteriores: `deploy.ps1`

El repositorio incluye el script `deploy.ps1` en la raíz del proyecto. Para deployar una actualización al cliente **desde la máquina de desarrollo** (con acceso a `C:\PizzaFiori\` del cliente vía red o en la misma máquina):

```powershell
cd C:\Users\Facundo\Desktop\PizzaFiori
.\deploy.ps1
```

El script detiene el servicio, copia el EXE y reemplaza el `frontend\dist\` completo, y reinicia el servicio. Si la ruta de instalación del cliente es diferente a `C:\PizzaFiori`:

```powershell
.\deploy.ps1 -Destino "D:\PizzaFiori"
```

> ⚠️ Siempre se deben deployar **EXE y `frontend\dist\` juntos**. Copiar solo el EXE deja el JS viejo en el cliente y causa errores de pantalla negra / datos NaN en producción.

---

---

# 🖥️ PARTE 2 — CLIENTE

> Estos pasos se ejecutan **en la notebook del cliente** con el paquete entregable copiado.

---

## 📋 Requisitos (máquina del cliente)

| Software | Versión mínima | Descarga |
|---|---|---|
| PostgreSQL | 16+ | https://www.postgresql.org/download/windows/ |
| mkcert | última | https://github.com/FiloSottile/mkcert/releases |
| NSSM | 2.24+ | https://nssm.cc/download |

> **mkcert**: descargar el ejecutable `.exe`, renombrarlo a `mkcert.exe` y copiarlo a `C:\Windows\System32\`.
>
> **NSSM**: descargar el zip, extraer y copiar `nssm-2.24\win64\nssm.exe` a `C:\Windows\System32\`.

### Verificar

Abrir **PowerShell** y ejecutar:

```powershell
psql --version     # psql (PostgreSQL) 16.x
mkcert --version
nssm version
```

---

## 📁 C1 — Copiar el Paquete

Descomprimir el ZIP entregable en el destino definitivo. Se recomienda una ruta sin espacios:

```
C:\PizzaFiori\
```

Estructura resultante:

```
C:\PizzaFiori\
├── backend\
│   └── dist\
│       └── pizzafiori.exe
└── frontend\
    └── dist\
```

> ⚠️ La ruta **no debe cambiar** después de instalar el servicio. Mover la carpeta requiere reconfigurar el servicio.

Desde este punto los comandos asumen `C:\PizzaFiori`. Reemplazar con la ruta real si es diferente.

---

## 🗄️ C2 — Configurar PostgreSQL

### 2.1 Crear usuario y base de datos

Abrir **PowerShell como Administrador** y conectarse a PostgreSQL:

```powershell
psql -U postgres
```

Dentro del prompt `postgres=#` ejecutar:

```sql
-- Crear usuario de la aplicaci\u00f3n (cambiar la contrase\u00f1a)
CREATE USER pizzafiori_user WITH PASSWORD 'CambiarEstaContrasena123!';

-- Crear la base de datos
CREATE DATABASE pizzafiori OWNER pizzafiori_user;

-- Salir
\q
```

### 2.2 Verificar la conexi\u00f3n

```powershell
psql -U pizzafiori_user -d pizzafiori -h localhost
```

Si no da error, la base de datos est\u00e1 lista. Escribir `\q` para salir.

---

## 🔒 C3 — Certificados SSL para `pizzafiori.com.ar`

Los certificados permiten que el navegador conf\u00ede en `https://pizzafiori.com.ar` localmente.

### C3.1 Instalar la CA local (solo una vez por m\u00e1quina)

Abrir **PowerShell como Administrador**:

```powershell
mkcert -install
```

Confirmar cuando Windows pregunte si confiar en el certificado.

### C3.2 Generar los certificados

```powershell
cd C:\PizzaFiori\backend\certs

mkcert pizzafiori.com.ar 127.0.0.1 localhost
```

Esto crea dos archivos en `backend\certs\`:

- `pizzafiori.com.ar+2.pem` — certificado p\u00fablico
- `pizzafiori.com.ar+2-key.pem` — clave privada

---

## 🌐 C4 — Configurar el archivo `hosts`

Este paso hace que `pizzafiori.com.ar` apunte a `127.0.0.1` en esta m\u00e1quina.

Abrir **Bloc de notas como Administrador** (clic derecho → "Ejecutar como administrador") y abrir el archivo:

```
C:\Windows\System32\drivers\etc\hosts
```

Agregar al final:

```
127.0.0.1   pizzafiori.com.ar
```

Guardar y cerrar.

> Para verificar: abrir PowerShell y ejecutar `ping pizzafiori.com.ar` — debe responder desde `127.0.0.1`.

---

## ⚙️ C5 — Configurar el Backend (`.env`)

Crear el archivo `C:\PizzaFiori\backend\.env` con el siguiente contenido:

```env
APP_NAME=PizzaFiori API
ENV=production
DEBUG=false

# Base de datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pizzafiori
DB_USER=pizzafiori_user
DB_PASSWORD=CambiarEstaContrasena123!

API_PORT=443

# Logging
LOG_DIR=logs
LOG_FILE=app.log

# JWT
JWT_SECRET=reemplazar_con_un_secreto_aleatorio_de_64_caracteres

# CORS
CORS_ORIGINS=https://pizzafiori.com.ar

# Certificados SSL
SSL_KEY_FILE=./certs/pizzafiori.com.ar+2-key.pem
SSL_CERT_FILE=./certs/pizzafiori.com.ar+2.pem
```

### Generar un JWT_SECRET seguro

> Si el cliente no tiene Python instalado, el desarrollador puede generar este valor y entregarlo con el `.env` pre-configurado.

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copiar el resultado y pegarlo como valor de `JWT_SECRET`.

---

## 🗃️ C6 — Migraciones de Base de Datos

> Las migraciones se ejecutan **automáticamente** cada vez que el servicio arranca.
> No es necesario ningún paso manual — al iniciar el servicio por primera vez en el Paso C7,
> las tablas se crean solas.

Para verificar que las tablas fueron creadas correctamente (después del Paso C7):

```powershell
psql -U pizzafiori_user -d pizzafiori -h localhost
```

Dentro del prompt ejecutar:

```sql
\dt
-- Debe listar las tablas: users, products, sales, expenses, etc.
\q
```

### (Opcional) Cargar datos iniciales

Si se quiere pre-cargar el menú y el usuario administrador inicial, incluir `seeds.py` en el ZIP entregable y ejecutar desde la máquina del cliente:

> Requiere Python instalado. Si el cliente ya tiene Python, o el desarrollador puede ejecutarlo antes de entregar.

```powershell
cd C:\PizzaFiori\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install alembic "psycopg[binary]" python-dotenv sqlalchemy
python seeds.py
```

---

## 🔧 C7 — Instalar el Servicio de Windows con NSSM

> ⚠️ Todos los comandos de este paso requieren **PowerShell como Administrador**.

### C7.1 Crear el servicio (GUI)

```powershell
nssm install PizzaFiori
```

Se abre la ventana de NSSM. Completar la pestaña **Application**:

| Campo | Valor |
|---|---|
| Path | `C:\PizzaFiori\backend\dist\pizzafiori.exe` |
| Startup directory | `C:\PizzaFiori\backend` |
| Arguments | *(dejar vacío — lee todo desde `.env`)* |

Pestaña **Details**:

| Campo | Valor |
|---|---|
| Display name | `PizzaFiori` |
| Description | `Sistema de gestión PizzaFiori` |
| Startup type | `Automatic` |

Pestaña **Log on**:

| Campo | Valor |
|---|---|
| Log on as | `Local System account` |

Hacer clic en **Install service**.

### C7.2 Alternativa: configurar por línea de comandos

```powershell
$exe     = "C:\PizzaFiori\backend\dist\pizzafiori.exe"
$workDir = "C:\PizzaFiori\backend"

nssm install PizzaFiori $exe
nssm set PizzaFiori AppParameters ""
nssm set PizzaFiori AppDirectory $workDir
nssm set PizzaFiori DisplayName "PizzaFiori"
nssm set PizzaFiori Description "Sistema de gestión PizzaFiori"
nssm set PizzaFiori Start SERVICE_AUTO_START
nssm set PizzaFiori ObjectName LocalSystem
```

### C7.3 Configurar logs del servicio (recomendado)

```powershell
New-Item -ItemType Directory -Force -Path "C:\PizzaFiori\backend\logs"

nssm set PizzaFiori AppStdout "C:\PizzaFiori\backend\logs\service_stdout.log"
nssm set PizzaFiori AppStderr "C:\PizzaFiori\backend\logs\service_stderr.log"
nssm set PizzaFiori AppRotateFiles 1
nssm set PizzaFiori AppRotateBytes 5242880
```

### C7.4 Iniciar el servicio

```powershell
nssm start PizzaFiori
nssm status PizzaFiori
# Debe mostrar: SERVICE_RUNNING
```

---

## ✅ C8 — Verificación Final

1. Abrir el navegador y navegar a: **https://pizzafiori.com.ar**
2. Debe cargar la pantalla de login de PizzaFiori (sin advertencias de certificado)
3. Iniciar sesión con el usuario administrador

### Verificar que el servicio sobrevive un reinicio

```powershell
Restart-Computer
```

Luego del reinicio, abrir `https://pizzafiori.com.ar` — debe funcionar sin intervención manual.

---

## �️ C9 — Cargar imágenes de productos

> Ejecutar **después** de que el servicio haya iniciado al menos una vez.
> El sistema registra los productos con sus SKUs durante el primer arranque (seed automático).

### C9.1 — Copiar las imágenes

Copiar todos los archivos de imágenes a:

```
C:\PizzaFiori\backend\uploads\productos\
```

Los archivos pueden tener cualquier número al final (ej: `PIZ-MUZZA-99999.jpg`). El script del paso siguiente los renombra automáticamente al SKU exacto.

### C9.2 — Ejecutar el renombrador

Hacer doble clic en:

```
C:\PizzaFiori\backend\rename_imagenes.bat
```

O desde PowerShell (para previsualizar sin cambiar nada):

```powershell
cd C:\PizzaFiori\backend
.\rename_imagenes.ps1 -DryRun   # previsualizar
.\rename_imagenes.ps1            # aplicar
```

El script lee las credenciales del `.env`, consulta los SKUs reales desde la base de datos y renombra cada imagen al nombre exacto esperado por el sistema.

Significado de los estados al finalizar:

| Estado | Significado | Acción |
|---|---|---|
| `[OK]` | Renombrado correctamente | — |
| `[SKIP]` | Ya tenía el nombre correcto | — |
| `[NO ENCONTRADO]` | Producto sin imagen en la carpeta | Copiar la imagen y volver a ejecutar |
| `[AMBIGUO]` | Más de una imagen con el mismo prefijo | Eliminar la duplicada y volver a ejecutar |
| `[ADVERTENCIA]` | El archivo destino ya existe con otro origen | Revisar manualmente |

> El script es seguro de ejecutar varias veces — ante cualquier duda no toca nada.

---

## �🛑 Comandos de gestión del servicio

```powershell
nssm start PizzaFiori     # Iniciar
nssm stop PizzaFiori      # Detener
nssm restart PizzaFiori   # Reiniciar
nssm status PizzaFiori    # Ver estado
nssm edit PizzaFiori      # Editar configuración (GUI)
nssm remove PizzaFiori confirm  # Desinstalar el servicio
```

---

## 🐛 Solución de Problemas

### El servicio no arranca — "Error 5: Access Denied" (puerto 443)

El puerto 443 requiere privilegios de administrador. El servicio debe correr como `Local System account` (configurado en el Paso 9).

Verificar con:

```powershell
nssm get PizzaFiori ObjectName
# Debe mostrar: LocalSystem
```

Si no es así:
```powershell
nssm set PizzaFiori ObjectName LocalSystem
nssm restart PizzaFiori
```

### El servicio arranca pero la web no carga

Ver los logs:

```powershell
Get-Content "C:\PizzaFiori\backend\logs\service_stderr.log" -Tail 50
```

También verificar el log de la aplicación:

```powershell
Get-Content "C:\PizzaFiori\backend\logs\app.log" -Tail 50
```

### "NET::ERR_CERT_AUTHORITY_INVALID" en el navegador

La CA de mkcert no fue instalada correctamente. Desde PowerShell **como Administrador**:

```powershell
mkcert -install
```

Luego cerrar y volver a abrir el navegador.

### "No se puede conectar a PostgreSQL"

1. Verificar que el servicio PostgreSQL está corriendo:
   ```powershell
   Get-Service postgresql*
   ```
2. Verificar las credenciales en `backend\.env` (`DB_USER`, `DB_PASSWORD`, `DB_NAME`).
3. Probar conexión manual:
   ```powershell
   psql -U pizzafiori_user -d pizzafiori -h localhost
   ```

### El hosts file no funciona (sigue yendo a internet)

Algunos navegadores (Chrome) tienen DNS-over-HTTPS que ignora el hosts file. Deshabilitar:

- **Chrome**: `chrome://settings/security` → desactivar "Usar DNS seguro"
- **Edge**: `edge://settings/privacy` → desactivar "Usar DNS seguro"

También vaciar la caché DNS de Windows:

```powershell
ipconfig /flushdns
```

### Error al buildear el frontend: "Cannot find module" / cert error

Verificar que `VITE_CERT_KEY_PATH` y `VITE_CERT_PATH` están **vacíos** en `frontend\.env` (no deben apuntar a archivos que no existen en tiempo de build).

### "alembic: can't locate revision"

Asegurarse de estar en el directorio `backend\` y con el entorno virtual activado:

```powershell
cd C:\PizzaFiori\backend
.venv\Scripts\Activate.ps1
alembic upgrade head
```

---

## 🔄 Actualizar la Aplicación

### En la máquina de desarrollo: generar nuevo paquete

```powershell
# 1. Actualizar dependencias Python (si cambió requirements.txt)
cd C:\PizzaFiori\backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Aplicar nuevas migraciones
alembic upgrade head

# 3. Rebuildear el frontend (si hubo cambios)
cd C:\PizzaFiori\frontend
npm install
npm run build

# 4. Recompilar el ejecutable
cd C:\PizzaFiori\backend
.venv\Scripts\Activate.ps1
pyinstaller pizzafiori.spec

# 5. Armar y entregar el nuevo ZIP (igual que D4)
```

### En la máquina del cliente: instalar la actualización

Usando `deploy.ps1` (recomendado — copia EXE y frontend juntos y reinicia el servicio automáticamente):

```powershell
cd C:\Users\Facundo\Desktop\PizzaFiori
.\deploy.ps1
```

Si la ruta del cliente es diferente:

```powershell
.\deploy.ps1 -Destino "D:\PizzaFiori"
```

> El script **no pisa** `backend\.env` ni `backend\certs\` — solo reemplaza el EXE y el `frontend\dist\`.
> Las migraciones nuevas se aplican **automáticamente** al reiniciar el servicio.

---

## �️ Desinstalación Completa

Estos pasos eliminan **todo** lo instalado: servicio, base de datos, certificados, entrada del hosts y archivos del proyecto.

> ⚠️ Todos los comandos requieren **PowerShell como Administrador**.

### 1 — Detener y eliminar el servicio de Windows

```powershell
nssm stop PizzaFiori
nssm remove PizzaFiori confirm
```

Verificar que ya no aparece en servicios:

```powershell
Get-Service PizzaFiori 2>&1
# Debe dar error "no se encontró ningún servicio" — eso es correcto
```

### 2 — Eliminar la entrada del hosts file

Abrir **Bloc de notas como Administrador** y abrir:

```
C:\Windows\System32\drivers\etc\hosts
```

Buscar y eliminar la línea:

```
127.0.0.1   pizzafiori.com.ar
```

Guardar y cerrar. Limpiar la caché DNS:

```powershell
ipconfig /flushdns
```

### 3 — Desinstalar la CA de mkcert

Esto revoca la confianza del navegador en todos los certificados generados con mkcert en esta máquina:

```powershell
mkcert -uninstall
```

### 4 — Eliminar la base de datos y el usuario PostgreSQL

```powershell
psql -U postgres
```

Dentro del prompt `postgres=#`:

```sql
-- Terminar conexiones activas antes de borrar
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'pizzafiori';

-- Eliminar la base de datos
DROP DATABASE pizzafiori;

-- Eliminar el usuario
DROP USER pizzafiori_user;

-- Salir
\q
```

### 5 — Eliminar los archivos del proyecto

```powershell
Remove-Item -Recurse -Force "C:\PizzaFiori"
```

> Si da error de permisos en la carpeta `.venv`, cerrar cualquier terminal o proceso que tenga el entorno virtual activo e intentar de nuevo.

### 6 — Desinstalar el software

> Solo si el software no se necesita para otros proyectos.

#### Python

```powershell
# Localizar el instalador de Python en el registro y desinstalar silenciosamente
$pyPath = (Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" |
    Get-ItemProperty | Where-Object { $_.DisplayName -like "Python 3*" } |
    Select-Object -First 1).UninstallString

if ($pyPath) {
    Start-Process "msiexec.exe" -ArgumentList "/x $($pyPath -replace 'MsiExec.exe /I','') /qn" -Wait
    Write-Host "Python desinstalado."
} else {
    Write-Host "Python no encontrado via registro. Desinstalar manualmente desde: Panel de control → Programas."
}
```

O manualmente: **Panel de control → Programas → Desinstalar un programa** → seleccionar todas las entradas **Python 3.x** → Desinstalar.

Luego limpiar los restos:

```powershell
# Eliminar carpetas de Python del usuario (pip cache, etc.)
Remove-Item -Recurse -Force "$env:APPDATA\Python" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Python" -ErrorAction SilentlyContinue
```

#### Node.js

```powershell
$nodePath = (Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" |
    Get-ItemProperty | Where-Object { $_.DisplayName -like "Node.js*" } |
    Select-Object -First 1).UninstallString

if ($nodePath) {
    Start-Process "msiexec.exe" -ArgumentList "/x $($nodePath -replace 'MsiExec.exe /I','') /qn" -Wait
    Write-Host "Node.js desinstalado."
} else {
    Write-Host "Node.js no encontrado via registro. Desinstalar manualmente desde: Panel de control → Programas."
}
```

Luego limpiar restos:

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\npm" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\npm-cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\nodejs" -ErrorAction SilentlyContinue
```

#### PostgreSQL

PostgreSQL trae su propio desinstalador. Ejecutar desde PowerShell como Administrador:

```powershell
# Ruta típica del desinstalador (ajustar versión si es diferente)
$pgUninstaller = "C:\Program Files\PostgreSQL\16\uninstall-postgresql.exe"

if (Test-Path $pgUninstaller) {
    Start-Process $pgUninstaller -ArgumentList "--mode unattended" -Wait
    Write-Host "PostgreSQL desinstalado."
} else {
    Write-Host "Desinstalador no encontrado. Usar: Panel de control → Programas → PostgreSQL 16."
}
```

Luego eliminar los datos residuales (⚠️ **esto borra todas las bases de datos**):

```powershell
Remove-Item -Recurse -Force "C:\Program Files\PostgreSQL" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Program Files (x86)\PostgreSQL" -ErrorAction SilentlyContinue
# Datos de las bases (ruta por defecto)
Remove-Item -Recurse -Force "C:\Program Files\PostgreSQL\16\data" -ErrorAction SilentlyContinue
```

#### NSSM y mkcert

Estos son ejecutables sueltos sin instalador:

```powershell
Remove-Item -Force "C:\Windows\System32\nssm.exe" -ErrorAction SilentlyContinue
Remove-Item -Force "C:\Windows\System32\mkcert.exe" -ErrorAction SilentlyContinue
```

### Verificación post-desinstalación

```powershell
# Servicio eliminado
Get-Service PizzaFiori 2>&1        # debe dar error "no encontrado"

# Carpeta eliminada
Test-Path "C:\PizzaFiori"          # debe devolver False

# DNS ya no apunta a 127.0.0.1
Resolve-DnsName pizzafiori.com.ar  # debe fallar o resolver externamente
```

---

## �🗝️ Resumen de Credenciales y Rutas

| Elemento | Valor |
|---|---|
| URL de la app | `https://pizzafiori.com.ar` |
| Puerto del servicio | `443` |
| Directorio del proyecto | `C:\PizzaFiori\` |
| Backend `.env` | `C:\PizzaFiori\backend\.env` |
| Frontend `.env` | `C:\PizzaFiori\frontend\.env` |
| Certificados | `C:\PizzaFiori\backend\certs\` |
| Logs del servicio | `C:\PizzaFiori\backend\logs\service_stderr.log` |
| Logs de la app | `C:\PizzaFiori\backend\logs\app.log` |
| Nombre del servicio Windows | `PizzaFiori` |

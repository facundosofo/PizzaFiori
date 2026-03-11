<#
.SYNOPSIS
    Renombra las imagenes de productos para que coincidan con los SKUs de la base de datos.
.DESCRIPTION
    Conecta a PostgreSQL leyendo las credenciales del archivo .env, consulta los SKUs
    de todos los productos activos, y renombra los archivos en uploads\productos\ para
    que coincidan exactamente con el SKU de cada producto.
.PARAMETER DryRun
    Muestra los cambios que se realizarian sin aplicarlos.
.EXAMPLE
    .\rename_imagenes.ps1
    .\rename_imagenes.ps1 -DryRun
#>

[CmdletBinding()]
param([switch]$DryRun)

# -- Leer .env ----------------------------------------------------------------

$envFile = Join-Path $PSScriptRoot '.env'
if (-not (Test-Path $envFile)) {
    Write-Host ('ERROR: No se encontro el archivo .env en: {0}' -f $PSScriptRoot) -ForegroundColor Red
    Write-Host 'Asegurate de ejecutar este script desde la carpeta backend\' -ForegroundColor Red
    exit 1
}

$config = @{}
Get-Content $envFile -Encoding UTF8 | ForEach-Object {
    if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*?)\s*$') {
        $config[$Matches[1].ToUpper()] = $Matches[2]
    }
}

$dbHost     = $config['DB_HOST'];     if (-not $dbHost)     { $dbHost = 'localhost' }
$dbPort     = $config['DB_PORT'];     if (-not $dbPort)     { $dbPort = '5432' }
$dbName     = $config['DB_NAME'];     if (-not $dbName)     { $dbName = 'pizzafiori' }
$dbUser     = $config['DB_USER']
$dbPassword = $config['DB_PASSWORD']

if (-not $dbUser -or -not $dbPassword) {
    Write-Host 'ERROR: DB_USER o DB_PASSWORD no encontrados en el archivo .env' -ForegroundColor Red
    exit 1
}

# -- Verificar carpeta de uploads ---------------------------------------------

$uploadsDir = Join-Path $PSScriptRoot 'uploads\productos'
if (-not (Test-Path $uploadsDir)) {
    Write-Host ('ERROR: No se encontro la carpeta de imagenes: {0}' -f $uploadsDir) -ForegroundColor Red
    exit 1
}

# -- Consultar productos a la BD ----------------------------------------------

Write-Host ''
Write-Host ('Conectando a PostgreSQL ({0}:{1}/{2})...' -f $dbHost, $dbPort, $dbName) -ForegroundColor Cyan

$tmpSql = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tmpSql -Value 'SELECT nombre, sku FROM "Productos" WHERE activo = true ORDER BY nombre' -Encoding UTF8

$env:PGPASSWORD = $dbPassword
$psqlOutput = & psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -t -A -F '|' -f $tmpSql 2>&1
$env:PGPASSWORD = $null

Remove-Item $tmpSql -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: No se pudo conectar a PostgreSQL.' -ForegroundColor Red
    Write-Host $psqlOutput -ForegroundColor Red
    Write-Host ''
    Write-Host 'Asegurate de que:' -ForegroundColor Yellow
    Write-Host '  1. El servicio PizzaFiori haya iniciado al menos una vez' -ForegroundColor Yellow
    Write-Host '  2. PostgreSQL este en ejecucion' -ForegroundColor Yellow
    Write-Host '  3. Las credenciales en .env sean correctas' -ForegroundColor Yellow
    exit 1
}

$productos = @()
foreach ($line in ($psqlOutput -split "`n")) {
    $line = $line.Trim()
    if (-not $line) { continue }
    $parts = $line -split '\|', 2
    if ($parts.Count -eq 2) {
        $nombre = $parts[0].Trim()
        $sku    = $parts[1].Trim()
        if ($sku -match '^[A-Z]{3}-[A-Z0-9]+-\d{5}$') {
            $productos += @{ nombre = $nombre; sku = $sku }
        }
    }
}

if ($productos.Count -eq 0) {
    Write-Host 'ERROR: No se encontraron productos en la base de datos.' -ForegroundColor Red
    Write-Host 'Asegurate de que el servicio haya iniciado al menos una vez (seeds ejecutados).' -ForegroundColor Yellow
    exit 1
}

Write-Host ('{0} productos encontrados en la BD.' -f $productos.Count) -ForegroundColor Cyan

if ($DryRun) {
    Write-Host ''
    Write-Host '=== MODO DRY-RUN: no se renombrara ningun archivo ===' -ForegroundColor Yellow
}
Write-Host ''
Write-Host ('Carpeta de imagenes: {0}' -f $uploadsDir)
Write-Host ''

# -- Procesar cada producto ---------------------------------------------------

$renombrados   = 0
$skips         = 0
$noEncontrados = 0
$advertencias  = 0
$extensiones   = @('jpg', 'jpeg', 'png', 'webp')

foreach ($prod in $productos) {
    $sku    = $prod.sku
    $nombre = $prod.nombre
    $prefix = $sku -replace '-\d{5}$', ''

    $encontrados = @()
    foreach ($ext in $extensiones) {
        $encontrados += Get-ChildItem -Path (Join-Path $uploadsDir ('{0}-*.{1}' -f $prefix, $ext)) -ErrorAction SilentlyContinue
    }

    if ($encontrados.Count -eq 0) {
        Write-Host ('  [NO ENCONTRADO]  {0}' -f $nombre) -ForegroundColor DarkYellow
        Write-Host ('                   Esperado: {0}-XXXXX.jpg' -f $prefix) -ForegroundColor DarkYellow
        $noEncontrados++
        continue
    }

    if ($encontrados.Count -gt 1) {
        Write-Host ('  [AMBIGUO]        {0} - multiples archivos con prefijo {1}-:' -f $nombre, $prefix) -ForegroundColor Red
        foreach ($f in $encontrados) {
            Write-Host ('                   {0}' -f $f.Name) -ForegroundColor Red
        }
        Write-Host '                   Dejar solo uno y volver a ejecutar.' -ForegroundColor Red
        $advertencias++
        continue
    }

    $archivo    = $encontrados[0]
    $nombreDest = '{0}.jpg' -f $sku
    $rutaDest   = Join-Path $uploadsDir $nombreDest

    if ($archivo.Name -eq $nombreDest) {
        Write-Host ('  [SKIP]           {0}' -f $nombreDest) -ForegroundColor DarkGray
        $skips++
        continue
    }

    if (Test-Path $rutaDest) {
        Write-Host ('  [ADVERTENCIA]    El destino ya existe: {0}' -f $nombreDest) -ForegroundColor Magenta
        Write-Host ('                   Origen: {0} - revisar manualmente.' -f $archivo.Name) -ForegroundColor Magenta
        $advertencias++
        continue
    }

    if ($DryRun) {
        Write-Host ('  [DRY-RUN]        {0}  ->  {1}' -f $archivo.Name, $nombreDest) -ForegroundColor Cyan
    } else {
        Rename-Item -Path $archivo.FullName -NewName $nombreDest
        Write-Host ('  [OK]             {0}  ->  {1}' -f $archivo.Name, $nombreDest) -ForegroundColor Green
        $renombrados++
    }
}

# -- Resumen ------------------------------------------------------------------

Write-Host ''
Write-Host '-------------------------------------------------------------' -ForegroundColor DarkGray
if ($DryRun) {
    Write-Host '  Dry-run completado. Ejecutar sin -DryRun para aplicar los cambios.' -ForegroundColor Yellow
} else {
    Write-Host ('  Renombrados:        {0}' -f $renombrados) -ForegroundColor Green

    if ($skips -gt 0) {
        Write-Host ('  Ya correctos:       {0}' -f $skips) -ForegroundColor DarkGray
    }

    if ($noEncontrados -gt 0) {
        Write-Host ('  Sin imagen:         {0}' -f $noEncontrados) -ForegroundColor DarkYellow
        Write-Host '                      Copiar las imagenes faltantes y volver a ejecutar.' -ForegroundColor DarkYellow
    } else {
        Write-Host ('  Sin imagen:         {0}' -f $noEncontrados) -ForegroundColor DarkGray
    }

    if ($advertencias -gt 0) {
        Write-Host ('  Requieren atencion: {0}' -f $advertencias) -ForegroundColor Red
        Write-Host '                      Ver detalles arriba y resolver manualmente.' -ForegroundColor Red
    } else {
        Write-Host ('  Advertencias:       {0}' -f $advertencias) -ForegroundColor DarkGray
    }

    if ($noEncontrados -eq 0 -and $advertencias -eq 0) {
        Write-Host ''
        Write-Host '  Todas las imagenes estan correctamente vinculadas.' -ForegroundColor Green
    }
}
Write-Host ''
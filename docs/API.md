# Documentación de API - PizzaFiori

Documentación completa de la API REST de PizzaFiori.

## Información General

- **Base URL:** `http://localhost:8000`
- **Formato:** JSON
- **Autenticación:** No requerida (por ahora)

## Documentación Interactiva

FastAPI proporciona documentación interactiva automática:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Endpoints Disponibles

### Productos

#### Crear un Producto

```http
POST /productos
```

**Descripción:** Crea un nuevo producto con precios escalonados.

**Content-Type:** `multipart/form-data`

**Parámetros:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | Sí | Nombre del producto (1-255 caracteres) |
| `categoria_id` | integer | Sí | ID de la categoría (debe ser > 0) |
| `precios` | string (JSON) | Sí | Array JSON de precios. Ejemplo: `[{"cantidad":1,"precio":1200}]` |
| `imagen` | file | No | Imagen del producto (opcional) |

**Formato de `precios`:**
```json
[
  {
    "cantidad": 1,
    "precio": 1200.00
  },
  {
    "cantidad": 2,
    "precio": 2200.00
  }
]
```

**Validaciones:**
- Debe existir al menos un precio
- No se permiten cantidades duplicadas
- Cantidad: 1-1000
- Precio: > 0, máximo 1,000,000

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "nombre": "Muzzarella",
  "categoria_id": 1,
  "precios": [
    {
      "id": 1,
      "cantidad": 1,
      "precio": 1200.00
    },
    {
      "id": 2,
      "cantidad": 2,
      "precio": 2200.00
    }
  ],
  "imagen": "productos/muzzarella.jpg",
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00"
}
```

**Errores:**
- `400`: Datos inválidos del producto
- `400`: Precios inválidos o duplicados

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/productos" \
  -F "nombre=Muzzarella" \
  -F "categoria_id=1" \
  -F 'precios=[{"cantidad":1,"precio":1200}]' \
  -F "imagen=@/ruta/a/imagen.jpg"
```

---

#### Obtener Todos los Productos

```http
GET /productos
```

**Descripción:** Obtiene la lista de todos los productos con filtros opcionales.

**Query Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `categoria` | integer | No | Filtrar por ID de categoría |
| `active` | boolean | No | Filtrar por estado activo/inactivo |

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "nombre": "Muzzarella",
    "categoria_id": 1,
    "precios": [
      {
        "id": 1,
        "cantidad": 1,
        "precio": 1200.00
      }
    ],
    "imagen": "productos/muzzarella.jpg",
    "activo": true,
    "fecha_creacion": "2026-01-19T18:00:00"
  }
]
```

**Ejemplo:**
```bash
# Obtener todos los productos
curl "http://localhost:8000/productos"

# Filtrar por categoría
curl "http://localhost:8000/productos?categoria=1"

# Solo productos activos
curl "http://localhost:8000/productos?active=true"
```

---

#### Obtener un Producto por ID

```http
GET /productos/{producto_id}
```

**Descripción:** Obtiene un producto específico por su ID.

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | integer | Sí | ID único del producto (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Muzzarella",
  "categoria_id": 1,
  "precios": [
    {
      "id": 1,
      "cantidad": 1,
      "precio": 1200.00
    }
  ],
  "imagen": "productos/muzzarella.jpg",
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00"
}
```

**Errores:**
- `404`: Producto no encontrado

**Ejemplo:**
```bash
curl "http://localhost:8000/productos/1"
```

---

#### Actualizar un Producto

```http
PUT /productos/{producto_id}
```

**Descripción:** Actualiza un producto existente. Todos los campos son opcionales.

**Content-Type:** `multipart/form-data`

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | integer | Sí | ID único del producto (≥ 1) |

**Parámetros (todos opcionales):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre` | string | Nuevo nombre del producto |
| `categoria_id` | integer | Nueva categoría |
| `precios` | string (JSON) | Nueva lista de precios |
| `imagen` | file | Nueva imagen del producto |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Muzzarella Actualizada",
  "categoria_id": 1,
  "precios": [
    {
      "id": 1,
      "cantidad": 1,
      "precio": 1300.00
    }
  ],
  "imagen": "productos/muzzarella_nueva.jpg",
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00"
}
```

**Errores:**
- `404`: Producto no encontrado
- `400`: Datos inválidos

**Ejemplo:**
```bash
curl -X PUT "http://localhost:8000/productos/1" \
  -F "nombre=Muzzarella Actualizada" \
  -F 'precios=[{"cantidad":1,"precio":1300}]'
```

---

#### Desactivar un Producto

```http
PATCH /productos/{producto_id}/desactivar
```

**Descripción:** Desactiva un producto (soft delete).

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | integer | Sí | ID único del producto (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Muzzarella",
  "categoria_id": 1,
  "precios": [...],
  "imagen": "productos/muzzarella.jpg",
  "activo": false,
  "fecha_creacion": "2026-01-19T18:00:00"
}
```

**Errores:**
- `404`: Producto no encontrado

**Ejemplo:**
```bash
curl -X PATCH "http://localhost:8000/productos/1/desactivar"
```

---

### Categorías

#### Crear una Categoría

```http
POST /categorias
```

**Descripción:** Crea una nueva categoría de productos.

**Content-Type:** `application/json`

**Body:**
```json
{
  "nombre": "Pizzas",
  "descripcion": "Pizzas de todos los gustos"
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | Sí | Nombre de la categoría |
| `descripcion` | string | No | Descripción opcional |

**Validaciones:**
- `nombre` debe ser único

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "nombre": "Pizzas",
  "descripcion": "Pizzas de todos los gustos"
}
```

**Errores:**
- `400`: Datos inválidos o nombre duplicado

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Pizzas",
    "descripcion": "Pizzas de todos los gustos"
  }'
```

---

#### Obtener Todas las Categorías

```http
GET /categorias
```

**Descripción:** Obtiene la lista de todas las categorías.

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "nombre": "Pizzas",
    "descripcion": "Pizzas de todos los gustos"
  },
  {
    "id": 2,
    "nombre": "Bebidas",
    "descripcion": null
  }
]
```

**Ejemplo:**
```bash
curl "http://localhost:8000/categorias"
```

---

#### Obtener una Categoría por ID

```http
GET /categorias/{categoria_id}
```

**Descripción:** Obtiene una categoría específica por su ID.

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `categoria_id` | integer | Sí | ID único de la categoría (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Pizzas",
  "descripcion": "Pizzas de todos los gustos"
}
```

**Errores:**
- `404`: Categoría no encontrada

**Ejemplo:**
```bash
curl "http://localhost:8000/categorias/1"
```

---

#### Actualizar una Categoría

```http
PUT /categorias/{categoria_id}
```

**Descripción:** Actualiza una categoría existente.

**Content-Type:** `application/json`

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `categoria_id` | integer | Sí | ID único de la categoría (≥ 1) |

**Body (todos los campos opcionales):**
```json
{
  "nombre": "Pizzas Especiales",
  "descripcion": "Nueva descripción"
}
```

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Pizzas Especiales",
  "descripcion": "Nueva descripción"
}
```

**Errores:**
- `404`: Categoría no encontrada
- `400`: Datos inválidos

**Ejemplo:**
```bash
curl -X PUT "http://localhost:8000/categorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Pizzas Especiales",
    "descripcion": "Nueva descripción"
  }'
```

---

#### Eliminar una Categoría

```http
DELETE /categorias/{categoria_id}
```

**Descripción:** Elimina una categoría existente.

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `categoria_id` | integer | Sí | ID único de la categoría (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "detalle": "Categoría eliminada correctamente"
}
```

**Errores:**
- `404`: Categoría no encontrada

**Ejemplo:**
```bash
curl -X DELETE "http://localhost:8000/categorias/1"
```

---

### Ofertas

#### Crear una Oferta

```http
POST /ofertas
```

**Descripción:** Crea una nueva oferta con productos asociados.

**Content-Type:** `application/json`

**Body:**
```json
{
  "nombre": "Combo Familiar",
  "descripcion": "2 Pizzas + 2 Bebidas",
  "precio": 3500.00,
  "productos": [
    {
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "producto_id": 2,
      "cantidad": 2
    }
  ]
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | Sí | Nombre de la oferta (1-255 caracteres) |
| `descripcion` | string | No | Descripción de la oferta (máx. 1000 caracteres) |
| `precio` | decimal | Sí | Precio total de la oferta (> 0, máx. 1,000,000) |
| `productos` | array | Sí | Lista de productos incluidos (mín. 1 producto) |

**Validaciones:**
- Debe tener al menos un producto
- No se permiten productos duplicados
- Todos los productos deben existir

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "nombre": "Combo Familiar",
  "descripcion": "2 Pizzas + 2 Bebidas",
  "precio": 3500.00,
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00",
  "fecha_actualizacion": "2026-01-19T18:00:00",
  "productos": [
    {
      "id": 1,
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "id": 2,
      "producto_id": 2,
      "cantidad": 2
    }
  ]
}
```

**Errores:**
- `400`: Datos inválidos
- `404`: Uno o más productos no encontrados

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/ofertas" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Combo Familiar",
    "descripcion": "2 Pizzas + 2 Bebidas",
    "precio": 3500.00,
    "productos": [
      {"producto_id": 1, "cantidad": 2},
      {"producto_id": 2, "cantidad": 2}
    ]
  }'
```

---

#### Obtener Todas las Ofertas

```http
GET /ofertas
```

**Descripción:** Obtiene la lista de todas las ofertas con filtros opcionales.

**Query Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `active` | boolean | No | Filtrar por estado activo/inactivo |

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "nombre": "Combo Familiar",
    "descripcion": "2 Pizzas + 2 Bebidas",
    "precio": 3500.00,
    "activo": true,
    "fecha_creacion": "2026-01-19T18:00:00",
    "fecha_actualizacion": "2026-01-19T18:00:00",
    "productos": [...]
  }
]
```

**Ejemplo:**
```bash
# Todas las ofertas
curl "http://localhost:8000/ofertas"

# Solo ofertas activas
curl "http://localhost:8000/ofertas?active=true"
```

---

#### Obtener una Oferta por ID

```http
GET /ofertas/{offer_id}
```

**Descripción:** Obtiene una oferta específica por su ID con todos sus productos.

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `offer_id` | integer | Sí | ID único de la oferta (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Combo Familiar",
  "descripcion": "2 Pizzas + 2 Bebidas",
  "precio": 3500.00,
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00",
  "fecha_actualizacion": "2026-01-19T18:00:00",
  "productos": [
    {
      "id": 1,
      "producto_id": 1,
      "cantidad": 2
    }
  ]
}
```

**Errores:**
- `404`: Oferta no encontrada

**Ejemplo:**
```bash
curl "http://localhost:8000/ofertas/1"
```

---

#### Actualizar una Oferta

```http
PUT /ofertas/{offer_id}
```

**Descripción:** Actualiza una oferta existente. Todos los campos son opcionales.

**Content-Type:** `application/json`

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `offer_id` | integer | Sí | ID único de la oferta (≥ 1) |

**Body (todos los campos opcionales):**
```json
{
  "nombre": "Combo Familiar Actualizado",
  "descripcion": "Nueva descripción",
  "precio": 3800.00,
  "productos": [
    {
      "producto_id": 1,
      "cantidad": 3
    }
  ]
}
```

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Combo Familiar Actualizado",
  "descripcion": "Nueva descripción",
  "precio": 3800.00,
  "activo": true,
  "fecha_creacion": "2026-01-19T18:00:00",
  "fecha_actualizacion": "2026-01-19T19:00:00",
  "productos": [...]
}
```

**Errores:**
- `404`: Oferta o producto no encontrado
- `400`: Datos inválidos

**Ejemplo:**
```bash
curl -X PUT "http://localhost:8000/ofertas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "precio": 3800.00
  }'
```

---

#### Desactivar una Oferta

```http
PATCH /ofertas/{offer_id}/desactivar
```

**Descripción:** Desactiva una oferta (soft delete).

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `offer_id` | integer | Sí | ID único de la oferta (≥ 1) |

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "nombre": "Combo Familiar",
  "descripcion": "2 Pizzas + 2 Bebidas",
  "precio": 3500.00,
  "activo": false,
  "fecha_creacion": "2026-01-19T18:00:00",
  "fecha_actualizacion": "2026-01-19T19:00:00",
  "productos": [...]
}
```

**Errores:**
- `404`: Oferta no encontrada

**Ejemplo:**
```bash
curl -X PATCH "http://localhost:8000/ofertas/1/desactivar"
```

---

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| `200` | OK - Operación exitosa |
| `201` | Created - Recurso creado exitosamente |
| `204` | No Content - Operación exitosa sin contenido |
| `400` | Bad Request - Datos inválidos |
| `404` | Not Found - Recurso no encontrado |
| `500` | Internal Server Error - Error del servidor |

## Manejo de Errores

Todas las respuestas de error siguen este formato:

```json
{
  "detail": "Mensaje descriptivo del error"
}
```

**Ejemplos:**

```json
{
  "detail": "Producto no encontrado"
}
```

```json
{
  "detail": "Debe existir al menos un precio"
}
```

## Acceso a Archivos Estáticos

Las imágenes de productos están disponibles en:

```
GET /uploads/{ruta_imagen}
```

**Ejemplo:**
```
http://localhost:8000/uploads/productos/muzzarella.jpg
```

## Notas Importantes

1. **Formato de Fechas:** Todas las fechas están en formato ISO 8601: `YYYY-MM-DDTHH:MM:SS`

2. **Precios:** Los precios son decimales con 2 decimales (ej: 1200.00)

3. **Imágenes:** Las imágenes se guardan en `backend/uploads/productos/` y se acceden mediante `/uploads/`

4. **Soft Delete:** Los productos y ofertas no se eliminan físicamente, se marcan como `activo: false`

5. **Validaciones:** La API valida todos los datos antes de procesarlos. Revisa los mensajes de error para más detalles.

## Ejemplos de Uso Completo

### Flujo Completo: Crear Categoría → Crear Producto → Crear Oferta

```bash
# 1. Crear categoría
CATEGORIA_ID=$(curl -s -X POST "http://localhost:8000/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Pizzas","descripcion":"Pizzas de todos los gustos"}' \
  | jq -r '.id')

# 2. Crear producto
PRODUCTO_ID=$(curl -s -X POST "http://localhost:8000/productos" \
  -F "nombre=Muzzarella" \
  -F "categoria_id=$CATEGORIA_ID" \
  -F 'precios=[{"cantidad":1,"precio":1200}]' \
  | jq -r '.id')

# 3. Crear oferta
curl -X POST "http://localhost:8000/ofertas" \
  -H "Content-Type: application/json" \
  -d "{
    \"nombre\": \"Combo Pizza\",
    \"precio\": 1200.00,
    \"productos\": [{\"producto_id\": $PRODUCTO_ID, \"cantidad\": 1}]
  }"
```

---

**Última actualización:** Enero 2026

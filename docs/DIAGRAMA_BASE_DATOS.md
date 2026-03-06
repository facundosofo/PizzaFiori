# Diagrama de Base de Datos - PizzaFiori

## Descripción General

La base de datos de PizzaFiori está diseñada para gestionar productos, categorías, precios, ofertas, ventas, gastos y usuarios de una pizzería. Utiliza SQL Server (MSSQL) como motor de base de datos y SQLAlchemy como ORM.

**Características clave:**
- ✅ Gestión de productos con SKU único
- ✅ Precios escalonados por cantidad
- ✅ Sistema de ofertas flexible
- ✅ Soporte para pizzas mitad-mitad
- ✅ **Snapshots de ventas** para preservar información histórica
- ✅ Gestión de usuarios con roles (ADMIN/USER) y bloqueo de cuentas
- ✅ Control de stock por categoría con umbrales de alerta
- ✅ Secuencia diaria de órdenes
- ✅ Gestión de gastos con categorías jerárquicas
- ✅ Auditoría completa con JSONB diffs y timestamps

## Diagrama Entidad-Relación

```mermaid
erDiagram
    ProductosCategorias ||--o{ Productos : "tiene"
    ProductosCategorias ||--o{ OfertaItems : "permite seleccionar"
    ProductosCategorias ||--o| StockCategorias : "tiene stock"
    Productos ||--o{ ProductoPrecios : "tiene"
    Productos ||--o{ OfertaItemProductos : "incluye"
    Productos ||--o{ VentaItems : "se vende en"
    Ofertas ||--o{ OfertaItems : "contiene"
    Ofertas ||--o{ VentaItems : "se vende en"
    OfertaItems ||--o{ OfertaItemProductos : "puede tener"
    Ventas ||--o{ VentaItems : "contiene"
    VentaItems ||--o{ VentaItemOfertaProductos : "snapshot de oferta"
    GastosCategorias ||--o{ Gastos : "tiene"
    GastosCategorias ||--o{ GastosCategorias : "subcategorias"
    
    Usuarios {
        int id PK
        string username UK "unique, indexed"
        string email UK "unique, indexed"
        text password_hash "not null"
        string first_name "not null"
        string last_name "not null"
        string role "default USER"
        int failed_login_attempts "default 0"
        datetime locked_until "nullable"
        datetime created_at
        datetime updated_at
    }
    
    ProductosCategorias {
        int id PK
        string nombre UK "unique, indexed"
        boolean activo "default true"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    StockCategorias {
        int categoria_id PK_FK
        int cantidad "default 0"
        int umbral_amarillo "nullable"
        int umbral_rojo "nullable"
        datetime fecha_actualizacion
    }
    
    Productos {
        int id PK
        string sku UK "unique, indexed, not null"
        string nombre "not null"
        int categoria_id FK
        string imagen "nullable"
        boolean activo "default true"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    ProductoPrecios {
        int id PK
        int producto_id FK
        int cantidad "not null"
        numeric precio "10,2"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    Ofertas {
        int id PK
        string nombre "not null"
        string descripcion "nullable"
        numeric precio "10,2"
        boolean activo "default true"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    OfertaItems {
        int id PK
        int oferta_id FK
        int categoria_id FK "nullable"
        int cantidad "default 1"
    }
    
    OfertaItemProductos {
        int oferta_item_id PK_FK
        int producto_id PK_FK
    }
    
    Ventas {
        int id PK
        string numero_orden UK "not null, unique"
        numeric total "10,2"
        datetime fecha_creacion "indexed"
        datetime fecha_actualizacion
    }
    
    OrderDailySequence {
        date business_date PK
        int last_value "not null"
    }
    
    VentaItems {
        int id PK
        int venta_id FK
        int producto_id FK "nullable"
        int oferta_id FK "nullable"
        int cantidad "not null"
        numeric precio_unitario "10,2"
        numeric subtotal "10,2"
        string producto_sku "indexed, snapshot"
        string item_nombre "not null, snapshot"
        string item_categoria "not null, snapshot"
        text item_descripcion "nullable, snapshot"
        boolean es_pizza_mitad_mitad "default false, indexed"
    }
    
    VentaItemOfertaProductos {
        int id PK
        int venta_item_id FK
        int producto_id FK "nullable"
        string producto_nombre "snapshot"
        string categoria_nombre "snapshot"
        int cantidad "not null"
    }
    
    GastosCategorias {
        int id PK
        string nombre "not null, indexed"
        int padre_id FK "nullable, self-ref"
        boolean activo "default true"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    Gastos {
        int id PK
        int categoria_gasto_id FK "not null"
        string descripcion "nullable"
        numeric monto "12,2"
        date fecha_pago "not null, indexed"
        boolean activo "default true"
        datetime fecha_creacion
        datetime fecha_actualizacion
    }
    
    AuditLogs {
        int id PK
        datetime timestamp "not null, indexed"
        string username "not null"
        string entity_type "not null, indexed"
        int entity_id "not null, indexed"
        string action "not null"
        jsonb changes "not null"
    }
```

## Descripción de Entidades

### 1. Usuarios

**Tabla:** `Usuarios`

**Descripción:** Gestiona los usuarios del sistema con autenticación, roles y mecanismo de bloqueo de cuentas por intentos fallidos.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Identificador único del usuario |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE, INDEXED | Nombre de usuario (único) |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE, INDEXED | Correo electrónico (único) |
| `password_hash` | TEXT | NOT NULL | Hash de la contraseña |
| `first_name` | VARCHAR(50) | NOT NULL | Nombre del usuario |
| `last_name` | VARCHAR(50) | NOT NULL | Apellido del usuario |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'USER' | Rol del usuario: `ADMIN` o `USER` |
| `failed_login_attempts` | INTEGER | NOT NULL, DEFAULT 0 | Contador de intentos de login fallidos |
| `locked_until` | DATETIME | NULLABLE | Fecha/hora hasta la cual la cuenta está bloqueada |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | Fecha de creación del registro |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Índices:**
- Índice único en `username`
- Índice único en `email`

**Ejemplo de datos:**
```
id | username | email              | first_name | last_name | role  | failed_login_attempts | locked_until
---|----------|--------------------|------------|-----------|-------|-----------------------|-------------
1  | admin    | admin@pizzafiori.com | Admin      | Principal | ADMIN | 0                     | NULL
2  | cajero1  | cajero@pizzafiori.com | Juan       | Pérez     | USER  | 0                     | NULL
```

### 2. ProductosCategorias

**Tabla:** `productos_categorias`

**Descripción:** Representa las categorías de productos (ej: Pizzas, Bebidas, Postres, etc.)

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Identificador único de la categoría |
| `nombre` | VARCHAR(50) | NOT NULL, UNIQUE, INDEXED | Nombre de la categoría (único) |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si la categoría está activa |
| `fecha_creacion` | DATETIME | NOT NULL, DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | NOT NULL, DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Uno a Muchos** con `Productos`: Una categoría puede tener múltiples productos
- **Uno a Muchos** con `OfertaItems`: Una categoría puede estar en múltiples items de oferta
- **Uno a Uno** con `StockCategorias`: Una categoría tiene un registro de stock

**Ejemplo de datos:**
```
id | nombre    | activo | fecha_creacion      | fecha_actualizacion
---|-----------|--------|---------------------|--------------------
1  | Pizzas    | true   | 2026-01-19 10:00:00 | 2026-01-19 10:00:00
2  | Bebidas   | true   | 2026-01-19 10:00:00 | 2026-01-19 10:00:00
3  | Postres   | true   | 2026-01-19 10:00:00 | 2026-01-19 10:00:00
```

### 3. StockCategorias

**Tabla:** `stock_categorias`

**Descripción:** Control de stock a nivel de categoría con umbrales de alerta visual (amarillo y rojo) para la interfaz de usuario.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `categoria_id` | INTEGER | PRIMARY KEY, FOREIGN KEY | ID de la categoría (relación uno-a-uno) |
| `cantidad` | INTEGER | NOT NULL, DEFAULT 0 | Cantidad actual en stock |
| `umbral_amarillo` | INTEGER | NULLABLE | Umbral para alerta amarilla (stock bajo) |
| `umbral_rojo` | INTEGER | NULLABLE | Umbral para alerta roja (stock crítico) |
| `fecha_actualizacion` | DATETIME | NOT NULL, DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Uno a Uno** con `ProductosCategorias`: Un registro de stock pertenece a una categoría

**Ejemplo de datos:**
```
categoria_id | cantidad | umbral_amarillo | umbral_rojo | fecha_actualizacion
-------------|----------|-----------------|-------------|--------------------
1            | 50       | 20              | 5           | 2026-02-15 14:30:00
2            | 120      | 30              | 10          | 2026-02-15 14:30:00
3            | 15       | 10              | 3           | 2026-02-15 14:30:00
```

### 4. Productos

**Tabla:** `Productos`

**Descripción:** Representa los productos disponibles en la pizzería (pizzas, bebidas, postres, etc.)

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del producto |
| `sku` | VARCHAR(50) | NOT NULL, UNIQUE, INDEXED | Código SKU único del producto (generado automáticamente) |
| `nombre` | VARCHAR(50) | NOT NULL | Nombre del producto |
| `categoria_id` | INTEGER | FOREIGN KEY, NULLABLE | ID de la categoría a la que pertenece |
| `imagen` | VARCHAR(255) | NULLABLE | Ruta de la imagen del producto |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si el producto está activo/disponible |
| `fecha_creacion` | DATETIME | DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | DEFAULT NOW() | Fecha de última actualización |

**Relaciones:**
- **Muchos a Uno** con `ProductosCategorias`: Un producto pertenece a una categoría (opcional)
- **Uno a Muchos** con `ProductoPrecios`: Un producto puede tener múltiples precios (cascade: all, delete-orphan)
- **Muchos a Muchos** con `OfertaItems`: Un producto puede estar en múltiples items de oferta (vía `OfertaItemProductos`)
- **Uno a Muchos** con `VentaItems`: Un producto puede venderse múltiples veces

**Índices:**
- `ix_Productos_id`: Índice en el campo `id`
- `ix_Productos_sku`: Índice único en el campo `sku`
- `ix_productos_categoria`: Índice en el campo `categoria_id`

**Ejemplo de datos:**
```
id | sku            | nombre          | categoria_id | imagen                    | activo | fecha_creacion
---|----------------|-----------------|--------------|---------------------------|--------|---------------
1  | PIZZ-MUZZ-001  | Muzzarella      | 1            | productos/muzzarella.jpg   | true   | 2026-01-19
2  | BEBI-COCA-001  | Coca Cola 1.5L  | 2            | productos/coca_cola.jpg   | true   | 2026-01-19
3  | POST-TIRA-001  | Tiramisú        | 3            | productos/tiramisu.jpg    | true   | 2026-01-19
```

**Nota sobre SKU:** El SKU se genera automáticamente al crear el producto usando la función `generar_sku_producto()` que combina categoría, nombre y un identificador único.

### 5. ProductoPrecios

**Tabla:** `ProductoPrecios`

**Descripción:** Almacena los precios escalonados de cada producto según la cantidad (ej: precio por unidad, precio por docena)

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del precio |
| `producto_id` | INTEGER | FOREIGN KEY, NOT NULL | ID del producto al que pertenece el precio |
| `cantidad` | INTEGER | NOT NULL | Cantidad de unidades para este precio |
| `precio` | NUMERIC(10,2) | NOT NULL | Precio para la cantidad especificada |
| `fecha_creacion` | DATETIME | DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Muchos a Uno** con `Productos`: Un precio pertenece a un producto

**Índices:**
- `ix_ProductoPrecios_id`: Índice en el campo `id`
- `ix_productoprecio_producto_cantidad`: Índice compuesto en (`producto_id`, `cantidad`)

**Ejemplo de datos:**
```
id | producto_id | cantidad | precio  | fecha_creacion
---|-------------|----------|---------|---------------
1  | 1           | 1        | 1200.00 | 2026-01-19
2  | 1           | 2        | 2200.00 | 2026-01-19
3  | 2           | 1        | 800.00  | 2026-01-19
```

**Nota:** Un producto puede tener múltiples precios según la cantidad. Por ejemplo, una pizza puede costar $1200 por unidad o $2200 por dos unidades.

### 6. Ofertas

**Tabla:** `Ofertas`

**Descripción:** Representa ofertas o combos que incluyen múltiples productos a un precio especial

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único de la oferta |
| `nombre` | VARCHAR(50) | NOT NULL | Nombre de la oferta |
| `descripcion` | VARCHAR(255) | NULLABLE | Descripción de la oferta |
| `precio` | NUMERIC(10,2) | NOT NULL | Precio total de la oferta |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si la oferta está activa/disponible |
| `fecha_creacion` | DATETIME | DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | DEFAULT NOW() | Fecha de última actualización |

**Relaciones:**
- **Uno a Muchos** con `OfertaItems`: Una oferta contiene múltiples items (cascade: all, delete-orphan)

**Índices:**
- `ix_Ofertas_id`: Índice en el campo `id`

**Ejemplo de datos:**
```
id | nombre              | descripcion                    | precio  | activo | fecha_creacion
---|---------------------|--------------------------------|---------|--------|---------------
1  | Combo Familiar      | 2 Pizzas + 2 Bebidas           | 3500.00 | true   | 2026-01-19
2  | Pizza + Bebida      | 1 Pizza Muzzarella + 1 Bebida | 1800.00 | true   | 2026-01-19
```

### 7. OfertaItems

**Tabla:** `OfertaItems`

**Descripción:** Representa un item dentro de una oferta. Puede ser:
- **Uno o varios productos específicos** (a través de la tabla `OfertaItemProductos`)
- **Una categoría** para que el cliente elija cualquier producto de esa categoría

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del item |
| `oferta_id` | INTEGER | FOREIGN KEY, NOT NULL | ID de la oferta |
| `categoria_id` | INTEGER | FOREIGN KEY, NULLABLE | ID de la categoría (si el cliente puede elegir de una categoría) |
| `cantidad` | INTEGER | NOT NULL, DEFAULT 1 | Cantidad del producto/categoría en la oferta |

**Relaciones:**
- **Muchos a Uno** con `Ofertas`: Un item pertenece a una oferta
- **Muchos a Uno** con `ProductosCategorias`: Un item puede referenciar una categoría (opcional, lazy="selectin")
- **Muchos a Muchos** con `Productos`: Un item puede tener múltiples productos asociados (vía `OfertaItemProductos`, lazy="selectin")

**Propiedades híbridas:**
- `categoria_nombre`: Retorna el nombre de la categoría asociada (si existe)

**Índices:**
- `ix_OfertaItems_id`: Índice en el campo `id`

**Ejemplo de datos:**
```
id | oferta_id | categoria_id | cantidad | Descripción
---|-----------|--------------|----------|-------------
1  | 1         | NULL         | 1        | 1 producto específico (ver OfertaItemProductos)
2  | 1         | 2            | 2        | 2 bebidas a elección del cliente
3  | 2         | NULL         | 1        | Opciones: Pizza Napolitana O Calabresa O Jamón (ver OfertaItemProductos)
```

### 8. OfertaItemProductos

**Tabla:** `OfertaItemProductos`

**Descripción:** Tabla intermedia (junction table) que conecta items de oferta con productos. Permite que un item tenga:
- **1 producto específico** (1 registro)
- **N productos como opciones** (N registros) - el cliente elige uno

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `oferta_item_id` | INTEGER | PRIMARY KEY, FOREIGN KEY | ID del item de oferta |
| `producto_id` | INTEGER | PRIMARY KEY, FOREIGN KEY | ID del producto |

**Relaciones:**
- **Muchos a Uno** con `OfertaItems`: Un registro pertenece a un item
- **Muchos a Uno** con `Productos`: Un registro referencia un producto

**Constraints:**
- **Primary Key Compuesta:** (`oferta_item_id`, `producto_id`)
- **Foreign Keys con CASCADE:** Si se elimina un item u oferta, se eliminan estos registros

**Ejemplo de datos:**
```
oferta_item_id | producto_id | Descripción
---------------|-------------|-------------
1              | 1           | Item 1 tiene solo Pizza Muzzarella
3              | 5           | Item 3 puede ser Pizza Napolitana
3              | 6           | Item 3 puede ser Pizza Calabresa
3              | 7           | Item 3 puede ser Pizza Jamón y Morrón
```

### 9. Ventas

**Tabla:** `Ventas`

**Descripción:** Representa las ventas o pedidos realizados. Almacena el total y fecha de cada venta.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único de la venta |
| `numero_orden` | VARCHAR(17) | NOT NULL, UNIQUE | Número de orden (generado automáticamente por `OrderDailySequence`) |
| `total` | NUMERIC(10,2) | NOT NULL | Monto total de la venta |
| `fecha_creacion` | DATETIME | DEFAULT NOW(), INDEXED | Fecha y hora de creación de la venta |
| `fecha_actualizacion` | DATETIME | DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Uno a Muchos** con `VentaItems`: Una venta contiene múltiples items (cascade: all, delete-orphan)

**Índices:**
- `ix_Ventas_id`: Índice en el campo `id`
- Índice en `fecha_creacion` para filtros de dashboard

**Ejemplo de datos:**
```
id | numero_orden      | total    | fecha_creacion      | fecha_actualizacion
---|-------------------|----------|---------------------|--------------------
1  | 20260203-001      | 12000.00 | 2026-02-03 10:30:00 | 2026-02-03 10:30:00
2  | 20260203-002      | 6000.00  | 2026-02-03 11:15:00 | 2026-02-03 11:15:00
```

### 10. OrderDailySequence

**Tabla:** `order_daily_sequence`

**Descripción:** Tabla auxiliar para generar números de orden secuenciales por día de negocio. Cada día tiene su propio contador que se incrementa con cada nueva venta.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `business_date` | DATE | PRIMARY KEY | Fecha del día de negocio |
| `last_value` | INTEGER | NOT NULL | Último valor de secuencia utilizado |

**Ejemplo de datos:**
```
business_date | last_value
--------------|----------
2026-02-03    | 15
2026-02-04    | 8
2026-02-05    | 22
```

**Nota:** Esta tabla se usa internamente para generar el campo `numero_orden` de la tabla `Ventas`. El número de orden combina la fecha y el valor secuencial del día.

### 11. VentaItems

**Tabla:** `VentaItems`

**Descripción:** Representa los items individuales de una venta. **Implementa sistema de snapshots** para preservar información histórica del producto/oferta al momento de la venta. Soporta tres tipos de items: productos individuales, ofertas y pizzas mitad-mitad.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del item |
| `venta_id` | INTEGER | FOREIGN KEY, NOT NULL | ID de la venta a la que pertenece |
| `producto_id` | INTEGER | FOREIGN KEY, NULLABLE | ID del producto vendido |
| `oferta_id` | INTEGER | FOREIGN KEY, NULLABLE | ID de la oferta vendida |
| `cantidad` | INTEGER | NOT NULL | Cantidad vendida |
| `precio_unitario` | NUMERIC(10,2) | NOT NULL | Precio unitario al momento de la venta |
| `subtotal` | NUMERIC(10,2) | NOT NULL | Subtotal del item (cantidad × precio_unitario) |
| `producto_sku` | VARCHAR(50) | NULLABLE, INDEXED | **SNAPSHOT:** SKU del producto (solo para productos) |
| `item_nombre` | VARCHAR(255) | NOT NULL | **SNAPSHOT:** Nombre del producto/oferta al momento de venta |
| `item_categoria` | VARCHAR(100) | NOT NULL | **SNAPSHOT:** Categoría al momento de venta |
| `item_descripcion` | TEXT | NULLABLE | **SNAPSHOT:** Descripción de la oferta (solo para ofertas) |
| `es_pizza_mitad_mitad` | BOOLEAN | NULLABLE, DEFAULT FALSE, INDEXED | Indica si el item es una pizza mitad-mitad |

**Relaciones:**
- **Muchos a Uno** con `Ventas`: Un item pertenece a una venta
- **Muchos a Uno** con `Productos`: Un item puede referenciar un producto (nullable)
- **Muchos a Uno** con `Ofertas`: Un item puede referenciar una oferta (nullable)
- **Uno a Muchos** con `VentaItemOfertaProductos`: Un item tiene snapshot de productos (cascade: all, delete-orphan)

**Propiedades híbridas:**
- `producto_nombre`: Retorna el nombre del producto asociado (si existe)
- `oferta_nombre`: Retorna el nombre de la oferta asociada (si existe)

**Constraints:**
- **CHECK Constraint** (`check_producto_oferta_or_mitad_mitad`): Garantiza exactamente uno de tres estados válidos:
  ```sql
  (producto_id IS NOT NULL AND oferta_id IS NULL AND es_pizza_mitad_mitad = false) OR
  (producto_id IS NULL AND oferta_id IS NOT NULL AND es_pizza_mitad_mitad = false) OR
  (producto_id IS NULL AND oferta_id IS NULL AND es_pizza_mitad_mitad = true)
  ```
  - ✅ **Producto:** `producto_id` presente, sin `oferta_id`, no es mitad-mitad
  - ✅ **Oferta:** `oferta_id` presente, sin `producto_id`, no es mitad-mitad
  - ✅ **Pizza mitad-mitad:** sin `producto_id` ni `oferta_id`, `es_pizza_mitad_mitad = true`

**Índices:**
- `ix_VentaItems_id`: Índice en el campo `id`
- `ix_ventaitems_venta_id`: Índice en `venta_id`
- `ix_ventaitems_venta_producto`: Índice compuesto en (`venta_id`, `producto_id`)
- `ix_ventaitems_venta_oferta`: Índice compuesto en (`venta_id`, `oferta_id`)
- `ix_ventaitems_item_categoria`: Índice en `item_categoria`
- Índice en `producto_sku` para reportes
- Índice en `es_pizza_mitad_mitad`

**Ejemplo de datos:**
```
id | venta_id | producto_id | oferta_id | cantidad | precio_unitario | subtotal | producto_sku  | item_nombre        | item_categoria | item_descripcion     | es_pizza_mitad_mitad
---|----------|-------------|-----------|----------|-----------------|----------|---------------|--------------------|----------------|----------------------|---------------------
1  | 1        | 1           | NULL      | 6        | 1000.00         | 6000.00  | PIZZ-MUZZ-001 | Muzzarella         | Pizzas         | NULL                 | false
2  | 1        | NULL        | 1         | 1        | 6000.00         | 6000.00  | NULL          | Combo Familiar     | Ofertas        | 2 Pizzas + 2 Bebidas | false
3  | 2        | NULL        | NULL      | 1        | 1400.00         | 1400.00  | NULL          | Muzz/Napo          | Pizzas         | NULL                 | true
```

**Nota sobre Snapshots:** Los campos `producto_sku`, `item_nombre`, `item_categoria` e `item_descripcion` preservan la información **tal como estaba al momento de la venta**. Esto permite:
- ✅ Generar reportes históricos precisos
- ✅ Ver qué se vendió exactamente, incluso si el producto se renombra después
- ✅ Mantener integridad referencial sin perder datos si se elimina un producto

**Nota sobre Pizzas Mitad-Mitad:** Cuando `es_pizza_mitad_mitad = true`, los productos que componen cada mitad se registran en la tabla `VentaItemOfertaProductos` como snapshots.

### 12. VentaItemOfertaProductos

**Tabla:** `VentaItemOfertaProductos`

**Descripción:** **Snapshot de productos incluidos en una oferta o pizza mitad-mitad** al momento de la venta. Preserva qué productos componían una oferta o las mitades de una pizza cuando se realizó la venta.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del registro |
| `venta_item_id` | INTEGER | FOREIGN KEY (CASCADE), NOT NULL | ID del item de venta al que pertenece |
| `producto_id` | INTEGER | FOREIGN KEY, NULLABLE | ID del producto (puede ser NULL si se elimina) |
| `producto_nombre` | VARCHAR(50) | NOT NULL | **SNAPSHOT:** Nombre del producto al momento de venta |
| `categoria_nombre` | VARCHAR(50) | NULLABLE | **SNAPSHOT:** Categoría del producto al momento de venta |
| `cantidad` | INTEGER | NOT NULL | Cantidad de este producto en la oferta/mitad |

**Relaciones:**
- **Muchos a Uno** con `VentaItems`: Un snapshot pertenece a un item de venta
- **Muchos a Uno** con `Productos`: Referencia opcional al producto (puede ser NULL)

**Constraints:**
- **Foreign Key CASCADE:** Si se elimina un item de venta, se eliminan sus snapshots

**Índices:**
- `ix_VentaItemOfertaProductos_id`: Índice en el campo `id`
- `ix_ventaitemofertaproductos_venta_item_id`: Índice en `venta_item_id`
- `ix_ventaitemofertaproductos_ventaitem_producto`: Índice compuesto en (`venta_item_id`, `producto_id`)
- `ix_ventaitemofertaproductos_categoria_nombre`: Índice en `categoria_nombre`
- `ix_ventaitemofertaproductos_produto_nome`: Índice en `producto_nombre`

**Ejemplo de datos:**
```
id | venta_item_id | producto_id | producto_nombre    | categoria_nombre | cantidad
---|---------------|-------------|--------------------|------------------|----------
1  | 2             | 1           | Muzzarella         | Pizzas           | 1
2  | 2             | 5           | Napolitana         | Pizzas           | 1
3  | 2             | 2           | Coca Cola 1.5L     | Bebidas          | 2
4  | 3             | 1           | Muzzarella         | Pizzas           | 1
5  | 3             | 5           | Napolitana         | Pizzas           | 1
```

**Nota:** Este snapshot permite saber exactamente qué productos contenía una oferta o qué mitades componían una pizza mitad-mitad al momento de la venta, incluso si la oferta cambia después o se eliminan productos.

### 13. GastosCategorias

**Tabla:** `gastos_categorias`

**Descripción:** Categorías de gastos con soporte jerárquico (categorías padre e hijas). Permite organizar los gastos del negocio en una estructura de árbol.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único de la categoría |
| `nombre` | VARCHAR(100) | NOT NULL, INDEXED | Nombre de la categoría de gasto |
| `padre_id` | INTEGER | FOREIGN KEY (self), NULLABLE | ID de la categoría padre (para jerarquía) |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si la categoría está activa |
| `fecha_creacion` | DATETIME | NOT NULL, DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | NOT NULL, DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Auto-referencial** con `GastosCategorias`: Una categoría puede tener subcategorías (cascade: all, delete-orphan)
- **Uno a Muchos** con `Gastos`: Una categoría puede tener múltiples gastos

**Índices:**
- `ix_gastos_categorias_id`: Índice en el campo `id`
- Índice en `nombre`
- `ix_gastos_categorias_padre`: Índice en `padre_id`

**Ejemplo de datos:**
```
id | nombre              | padre_id | activo | fecha_creacion
---|---------------------|----------|--------|---------------
1  | Insumos             | NULL     | true   | 2026-01-19
2  | Harinas             | 1        | true   | 2026-01-19
3  | Quesos              | 1        | true   | 2026-01-19
4  | Servicios           | NULL     | true   | 2026-01-19
5  | Electricidad        | 4        | true   | 2026-01-19
```

### 14. Gastos

**Tabla:** `gastos`

**Descripción:** Registra los gastos del negocio, vinculados a categorías jerárquicas. Utiliza NUMERIC(12,2) para alta precisión en montos financieros.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Identificador único del gasto |
| `categoria_gasto_id` | INTEGER | FOREIGN KEY, NOT NULL | ID de la categoría de gasto |
| `descripcion` | VARCHAR(255) | NULLABLE | Descripción del gasto |
| `monto` | NUMERIC(12,2) | NOT NULL | Monto del gasto |
| `fecha_pago` | DATE | NOT NULL | Fecha de pago del gasto |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si el gasto está activo (soft delete) |
| `fecha_creacion` | DATETIME | NOT NULL, DEFAULT NOW() | Fecha de creación del registro |
| `fecha_actualizacion` | DATETIME | NOT NULL, DEFAULT NOW(), ON UPDATE | Fecha de última actualización |

**Relaciones:**
- **Muchos a Uno** con `GastosCategorias`: Un gasto pertenece a una categoría

**Índices:**
- `ix_gastos_id`: Índice en el campo `id`
- `ix_gastos_categoria`: Índice en `categoria_gasto_id`
- `ix_gastos_fecha`: Índice en `fecha_pago` para reportes financieros

**Ejemplo de datos:**
```
id | categoria_gasto_id | descripcion          | monto     | fecha_pago | activo
---|--------------------|----------------------|-----------|------------|-------
1  | 2                  | Harina 000 x 50kg    | 15000.00  | 2026-02-01 | true
2  | 5                  | Factura electricidad  | 45000.00  | 2026-02-05 | true
3  | 3                  | Muzzarella x 10kg    | 28000.00  | 2026-02-10 | true
```

### 15. AuditLogs

**Tabla:** `audit_logs`

**Descripción:** Registra todas las acciones del sistema para auditoría. Almacena quién hizo qué, sobre qué entidad, cuándo y qué cambió, usando JSONB para guardar el diff completo de cambios.

**Campos:**

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Identificador único del registro |
| `timestamp` | DATETIME | NOT NULL, INDEXED | Fecha y hora de la acción |
| `username` | VARCHAR(50) | NOT NULL | Nombre de usuario que realizó la acción (referencia inmutable) |
| `entity_type` | VARCHAR(50) | NOT NULL, INDEXED | Tipo de entidad afectada ("Product", "User", "Sale", etc.) |
| `entity_id` | INTEGER | NOT NULL, INDEXED | ID de la entidad afectada |
| `action` | VARCHAR(20) | NOT NULL | Tipo de acción: `CREATE`, `UPDATE`, `DELETE` |
| `changes` | JSONB | NOT NULL | Diff completo con valores anteriores y nuevos (`{old_values: {}, new_values: {}}`) |

**Índices:**
- Índice en `timestamp`
- Índice en `entity_type`
- Índice en `entity_id`
- `ix_audit_entity_timestamp`: Índice compuesto en (`entity_type`, `entity_id`, `timestamp`)
- `ix_audit_username_timestamp`: Índice compuesto en (`username`, `timestamp`)
- `ix_audit_timestamp_desc`: Índice descendente en `timestamp`

**Ejemplo de datos:**
```json
{
  "id": 1,
  "timestamp": "2026-02-03T10:30:00",
  "username": "admin",
  "entity_type": "Product",
  "entity_id": 5,
  "action": "UPDATE",
  "changes": {
    "old_values": {"nombre": "Muzarella", "precio": 1000.00},
    "new_values": {"nombre": "Muzzarella", "precio": 1200.00}
  }
}
```

## Relaciones Detalladas

### Relación ProductosCategorias → Productos

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una categoría puede tener cero o muchos productos
- **Foreign Key:** `Productos.categoria_id` → `productos_categorias.id`
- **Comportamiento:** Si se elimina una categoría, los productos asociados mantienen `categoria_id = NULL` (no se eliminan)

### Relación ProductosCategorias → StockCategorias

- **Tipo:** Uno a Uno (1:1)
- **Cardinalidad:** Una categoría tiene cero o un registro de stock
- **Foreign Key:** `stock_categorias.categoria_id` → `productos_categorias.id`
- **Comportamiento:** Relación uno-a-uno, `uselist=False` en el ORM

### Relación Productos → ProductoPrecios

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Un producto puede tener uno o muchos precios
- **Foreign Key:** `ProductoPrecios.producto_id` → `Productos.id`
- **Comportamiento:** Si se elimina un producto, se eliminan sus precios (CASCADE, delete-orphan)

### Relación Ofertas → OfertaItems

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una oferta puede tener uno o muchos items
- **Foreign Key:** `OfertaItems.oferta_id` → `Ofertas.id`
- **Comportamiento:** Si se elimina una oferta, se eliminan sus items (CASCADE, delete-orphan)

### Relación ProductosCategorias → OfertaItems

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una categoría puede estar en cero o muchos items de oferta
- **Foreign Key:** `OfertaItems.categoria_id` → `productos_categorias.id`
- **Comportamiento:** Si se elimina una categoría, los items mantienen `categoria_id = NULL`

### Relación OfertaItems → OfertaItemProductos

- **Tipo:** Muchos a Muchos (N:M) vía tabla intermedia
- **Cardinalidad:** Un item puede tener uno o muchos productos asociados
- **Foreign Key:** `OfertaItemProductos.oferta_item_id` → `OfertaItems.id`
- **Comportamiento:** Si se elimina un item, se eliminan sus productos asociados (CASCADE)

### Relación Productos → OfertaItemProductos

- **Tipo:** Muchos a Muchos (N:M) vía tabla intermedia
- **Cardinalidad:** Un producto puede estar en cero o muchos items de oferta
- **Foreign Key:** `OfertaItemProductos.producto_id` → `Productos.id`
- **Comportamiento:** Si se elimina un producto, se eliminan las asociaciones (CASCADE)

### Relación Ventas → VentaItems

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una venta contiene uno o muchos items
- **Foreign Key:** `VentaItems.venta_id` → `Ventas.id`
- **Comportamiento:** Si se elimina una venta, se eliminan sus items (CASCADE, delete-orphan)

### Relación Productos → VentaItems

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Un producto puede venderse en cero o muchos items de venta
- **Foreign Key:** `VentaItems.producto_id` → `Productos.id`
- **Comportamiento:** **NULL** - Si se elimina un producto, las ventas mantienen `producto_id = NULL` pero conservan los datos snapshot
- **Nota:** La relación es opcional porque los datos históricos se preservan en campos snapshot

### Relación Ofertas → VentaItems

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una oferta puede venderse en cero o muchos items de venta
- **Foreign Key:** `VentaItems.oferta_id` → `Ofertas.id`
- **Comportamiento:** **NULL** - Si se elimina una oferta, las ventas mantienen `oferta_id = NULL` pero conservan los datos snapshot
- **Nota:** La relación es opcional porque los datos históricos se preservan en campos snapshot y tabla de snapshot

### Relación VentaItems → VentaItemOfertaProductos

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Un item de venta (oferta o mitad-mitad) puede tener cero o muchos productos en su snapshot
- **Foreign Key:** `VentaItemOfertaProductos.venta_item_id` → `VentaItems.id`
- **Comportamiento:** Si se elimina un item de venta, se eliminan sus snapshots de productos (CASCADE, delete-orphan)

### Relación Productos → VentaItemOfertaProductos

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Un producto puede estar en cero o muchos snapshots de ofertas vendidas
- **Foreign Key:** `VentaItemOfertaProductos.producto_id` → `Productos.id`
- **Comportamiento:** **NULL** - Si se elimina un producto, los snapshots mantienen `producto_id = NULL` pero conservan el nombre del producto

### Relación GastosCategorias → GastosCategorias (Auto-referencial)

- **Tipo:** Uno a Muchos (1:N) auto-referencial
- **Cardinalidad:** Una categoría puede tener cero o muchas subcategorías
- **Foreign Key:** `gastos_categorias.padre_id` → `gastos_categorias.id`
- **Comportamiento:** Si se elimina una categoría padre, se eliminan sus subcategorías (CASCADE, delete-orphan, single_parent=True)

### Relación GastosCategorias → Gastos

- **Tipo:** Uno a Muchos (1:N)
- **Cardinalidad:** Una categoría de gasto puede tener cero o muchos gastos
- **Foreign Key:** `gastos.categoria_gasto_id` → `gastos_categorias.id`
- **Comportamiento:** Un gasto debe tener una categoría (NOT NULL)

## Constraints y Validaciones

### Constraints de Base de Datos

1. **Primary Keys:** Todas las tablas tienen una clave primaria (`id` o campo específico como `business_date`, `categoria_id`)
2. **Foreign Keys:** Todas las relaciones están definidas con foreign keys
3. **Unique Constraints:** 
   - `productos_categorias.nombre` es único
   - `Productos.sku` es único
   - `Ventas.numero_orden` es único y NOT NULL
   - `Usuarios.username` es único
   - `Usuarios.email` es único
4. **CHECK Constraints:**
   - `VentaItems` (`check_producto_oferta_or_mitad_mitad`): Tri-estado entre `producto_id`, `oferta_id` y `es_pizza_mitad_mitad` (exactamente uno de los tres estados debe ser válido)
5. **NOT NULL:** Campos críticos como `nombre`, `precio`, `activo`, `sku`, `numero_orden`, `password_hash`, `monto`, `fecha_pago` son obligatorios
6. **Default Values:** 
   - `activo` tiene valor por defecto `TRUE`
   - `fecha_creacion` y `fecha_actualizacion` tienen valor por defecto `NOW()`
   - `cantidad` en `OfertaItems` tiene valor por defecto `1`
   - `role` en `Usuarios` tiene valor por defecto `'USER'`
   - `failed_login_attempts` en `Usuarios` tiene valor por defecto `0`
   - `cantidad` en `stock_categorias` tiene valor por defecto `0`
   - `es_pizza_mitad_mitad` en `VentaItems` tiene valor por defecto `FALSE`

### Validaciones de Negocio (a nivel de aplicación)

1. **Usuarios:**
   - El username y email deben ser únicos
   - La contraseña se almacena hasheada (nunca en texto plano)
   - El rol debe ser `ADMIN` o `USER`
   - La cuenta se bloquea tras múltiples intentos fallidos de login

2. **Productos:**
   - El nombre no puede estar vacío
   - El SKU se genera automáticamente al crear el producto
   - La imagen debe ser una ruta válida si se proporciona
   - Debe tener al menos un precio asociado
   - La categoría debe existir si se proporciona

3. **ProductoPrecios:**
   - La cantidad debe ser mayor a 0
   - El precio debe ser mayor a 0
   - No puede haber precios duplicados para la misma cantidad del mismo producto

4. **Ofertas:**
   - El precio debe ser mayor a 0
   - Debe tener al menos un producto asociado

5. **OfertaItems:**
   - La cantidad debe ser mayor a 0
   - Debe tener productos asociados (vía `OfertaItemProductos`) O una categoría, pero no ambos
   - Si tiene productos, deben existir y estar activos
   - Si tiene `producto_opciones` (múltiples productos), debe tener al menos 2 productos
   - Si tiene categoría, la categoría debe existir

6. **Ventas:**
   - Debe tener al menos un item
   - El total debe ser mayor a 0
   - El número de orden se genera automáticamente vía `OrderDailySequence`
   - Cada item debe tener `producto_id` XOR `oferta_id` XOR `es_pizza_mitad_mitad=true`
   - Los snapshots se capturan automáticamente al crear la venta

7. **Gastos:**
   - El monto debe ser mayor a 0
   - Debe tener una categoría de gasto válida
   - La fecha de pago es obligatoria

8. **Stock:**
   - La cantidad no puede ser negativa
   - Los umbrales son opcionales pero si se definen, `umbral_rojo` < `umbral_amarillo`

## Índices y Optimizaciones

### Índices Existentes

1. **Usuarios:**
   - Índice único en `username`
   - Índice único en `email`

2. **ProductosCategorias:**
   - Índice único en `nombre`

3. **Productos:**
   - `ix_Productos_id`: Índice en `id` (automático por PRIMARY KEY)
   - `ix_Productos_sku`: Índice único en `sku`
   - `ix_productos_categoria`: Índice en `categoria_id`

4. **ProductoPrecios:**
   - `ix_ProductoPrecios_id`: Índice en `id`
   - `ix_productoprecio_producto_cantidad`: Índice compuesto en (`producto_id`, `cantidad`)

5. **Ofertas:**
   - `ix_Ofertas_id`: Índice en `id`

6. **OfertaItems:**
   - `ix_OfertaItems_id`: Índice en `id`
   - Índices implícitos en `oferta_id` y `categoria_id` (FOREIGN KEYS)

7. **Ventas:**
   - `ix_Ventas_id`: Índice en `id`
   - Índice en `fecha_creacion` para filtros de dashboard

8. **VentaItems:**
   - `ix_VentaItems_id`: Índice en `id`
   - `ix_ventaitems_venta_id`: Índice en `venta_id`
   - `ix_ventaitems_venta_producto`: Índice compuesto en (`venta_id`, `producto_id`)
   - `ix_ventaitems_venta_oferta`: Índice compuesto en (`venta_id`, `oferta_id`)
   - `ix_ventaitems_item_categoria`: Índice en `item_categoria`
   - Índice en `producto_sku` para reportes
   - Índice en `es_pizza_mitad_mitad`

9. **VentaItemOfertaProductos:**
   - `ix_VentaItemOfertaProductos_id`: Índice en `id`
   - `ix_ventaitemofertaproductos_venta_item_id`: Índice en `venta_item_id`
   - `ix_ventaitemofertaproductos_ventaitem_producto`: Índice compuesto en (`venta_item_id`, `producto_id`)
   - `ix_ventaitemofertaproductos_categoria_nombre`: Índice en `categoria_nombre`
   - `ix_ventaitemofertaproductos_produto_nome`: Índice en `producto_nombre`

10. **GastosCategorias:**
    - `ix_gastos_categorias_id`: Índice en `id`
    - Índice en `nombre`
    - `ix_gastos_categorias_padre`: Índice en `padre_id`

11. **Gastos:**
    - `ix_gastos_id`: Índice en `id`
    - `ix_gastos_categoria`: Índice en `categoria_gasto_id`
    - `ix_gastos_fecha`: Índice en `fecha_pago`

12. **AuditLogs:**
    - Índice en `timestamp`
    - Índice en `entity_type`
    - Índice en `entity_id`
    - `ix_audit_entity_timestamp`: Índice compuesto en (`entity_type`, `entity_id`, `timestamp`)
    - `ix_audit_username_timestamp`: Índice compuesto en (`username`, `timestamp`)
    - `ix_audit_timestamp_desc`: Índice descendente en `timestamp`

### Optimizaciones Recomendadas

1. **Índice compuesto en Productos:**
   ```sql
   CREATE INDEX idx_productos_categoria_activo 
   ON Productos(categoria_id, activo);
   ```
   Útil para consultas que filtran por categoría y estado activo.

2. **Índice en Ofertas:**
   ```sql
   CREATE INDEX idx_ofertas_activo 
   ON Ofertas(activo);
   ```
   Útil para filtrar ofertas activas.

3. **Índice compuesto en VentaItems para reportes:**
   ```sql
   CREATE INDEX idx_ventaitems_fecha_categoria
   ON VentaItems(fecha_creacion, item_categoria);
   ```
   Útil para reportes de ventas por período y categoría.

4. **Índice en VentaItems para búsqueda por nombre:**
   ```sql
   CREATE INDEX idx_ventaitems_nombre
   ON VentaItems(item_nombre);
   ```
   Útil para búsquedas de productos vendidos por nombre.

## Snapshots y Preservación de Datos Históricos

### ¿Por qué Snapshots?

El sistema implementa **snapshots** en las ventas para preservar la información histórica exacta al momento de cada transacción. Esto resuelve problemas comunes en sistemas de ventas:

**Problemas sin snapshots:**
- ❌ Si renombras "Muzarella" a "Muzzarella", los reportes históricos muestran el nuevo nombre
- ❌ Si eliminas un producto, pierdes el historial de qué se vendió
- ❌ Si cambias una oferta, no sabes qué incluía cuando se vendió
- ❌ Reportes inexactos por cambios en categorías o descripciones

**Solución con snapshots:**
- ✅ Los reportes muestran exactamente cómo estaba nombrado el producto al venderlo
- ✅ El historial se mantiene incluso si eliminas productos/ofertas
- ✅ Sabes exactamente qué contenía cada oferta vendida
- ✅ Reportes precisos e inmutables

### Campos Snapshot

#### En VentaItems:
- `producto_sku`: SKU del producto (inmutable para reportes)
- `item_nombre`: Nombre exacto al momento de venta
- `item_categoria`: Categoría al momento de venta  
- `item_descripcion`: Descripción de oferta (si aplica)

#### En VentaItemOfertaProductos:
- `producto_nombre`: Nombre del producto en la oferta o mitad de pizza
- `categoria_nombre`: Categoría del producto
- `cantidad`: Cantidad incluida en la oferta o mitad

### Tipos de Items en Ventas

El sistema soporta tres tipos de items de venta, controlados por el CHECK constraint tri-estado:

#### 1. Producto Individual
```python
venta_item = SaleItem(
    venta_id=1,
    producto_id=5,
    cantidad=6,
    precio_unitario=1000.00,
    subtotal=6000.00,
    es_pizza_mitad_mitad=False,
    # SNAPSHOTS:
    producto_sku=producto.sku,            # "PIZZ-MUZZ-001"
    item_nombre=producto.nombre,           # "Muzzarella"
    item_categoria=producto.categoria.nombre,  # "Pizzas"
    item_descripcion=None
)
```

#### 2. Oferta/Combo
```python
venta_item = SaleItem(
    venta_id=1,
    oferta_id=1,
    cantidad=1,
    precio_unitario=3500.00,
    subtotal=3500.00,
    es_pizza_mitad_mitad=False,
    # SNAPSHOTS:
    producto_sku=None,
    item_nombre=oferta.nombre,             # "Combo Familiar"
    item_categoria="Ofertas",
    item_descripcion=oferta.descripcion    # "2 Pizzas + 2 Bebidas"
)
# + registros en VentaItemOfertaProductos con los productos de la oferta
```

#### 3. Pizza Mitad-Mitad
```python
venta_item = SaleItem(
    venta_id=1,
    producto_id=None,
    oferta_id=None,
    cantidad=1,
    precio_unitario=1400.00,
    subtotal=1400.00,
    es_pizza_mitad_mitad=True,
    # SNAPSHOTS:
    producto_sku=None,
    item_nombre="Muzz/Napo",
    item_categoria="Pizzas",
    item_descripcion=None
)
# + registros en VentaItemOfertaProductos con cada mitad de la pizza
```

**Ventajas:**
- 📊 Reportes confiables a través del tiempo
- 🔍 Auditoría completa de qué se vendió
- 🛡️ Protección contra cambios accidentales
- 📈 Análisis histórico preciso
- 🍕 Trazabilidad de pizzas mitad-mitad

## Migraciones

Las migraciones de base de datos se gestionan mediante **Alembic**. El esquema inicial se encuentra en:

`backend/alembic/versions/1152e57d7573_initial_schema.py`

### Comandos de Migración

```bash
# Crear una nueva migración
cd backend
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## Modelo de Datos en SQLAlchemy

Los modelos están definidos en `backend/app/domain/models/`:

- `base.py` → Clase `Base` (declarative_base de SQLAlchemy)
- `user.py` → Tabla `Usuarios`
- `product_category.py` → Tabla `productos_categorias`
- `category_stock.py` → Tabla `stock_categorias`
- `product.py` → Tabla `Productos`
- `product_price.py` → Tabla `ProductoPrecios`
- `offer.py` → Tabla `Ofertas`
- `offer_item.py` → Tabla `OfertaItems` y tabla intermedia `OfertaItemProductos`
- `sale.py` → Tabla `Ventas`
- `sale_item.py` → Tabla `VentaItems`
- `sale_item_offer_product.py` → Tabla `VentaItemOfertaProductos`
- `order_daily_sequence.py` → Tabla `order_daily_sequence`
- `expense_category.py` → Tabla `gastos_categorias`
- `expense.py` → Tabla `gastos`
- `audit_log.py` → Tabla `audit_logs`

Cada modelo extiende de `Base` (SQLAlchemy) y define las relaciones usando `relationship()`.

## Consideraciones de Diseño

### Ventajas del Diseño Actual

✅ **SKU único:** Cada producto tiene un identificador inmutable para reportes  
✅ **Flexibilidad de precios:** Permite precios escalonados por cantidad  
✅ **Ofertas configurables:** Las ofertas pueden incluir cualquier combinación de productos  
✅ **Pizzas mitad-mitad:** Soporte nativo para vender pizzas combinadas con snapshot de cada mitad  
✅ **Soft delete:** El campo `activo` permite desactivar sin eliminar  
✅ **Gestión de usuarios:** Sistema de roles (ADMIN/USER) con bloqueo de cuentas por seguridad  
✅ **Control de stock:** Stock por categoría con umbrales de alerta visual (amarillo/rojo)  
✅ **Secuencia de órdenes:** Numeración automática diaria de órdenes  
✅ **Gestión de gastos:** Categorías jerárquicas con soft delete y reportes por fecha  
✅ **Auditoría completa:** Registro de todas las acciones con JSONB diffs, timestamps y usuario  
✅ **Normalización:** Diseño normalizado que evita redundancia  
✅ **Snapshots de ventas:** Preserva información histórica exacta e inmutable  
✅ **Integridad referencial flexible:** Foreign keys opcionales con datos preservados en snapshots

### Sistema de Snapshots

El diseño implementa un **patrón de snapshot híbrido**:

1. **Referencia opcional:** `producto_id` y `oferta_id` pueden ser NULL
2. **Datos inmutables:** Los campos snapshot (`item_nombre`, `producto_sku`, etc.) son NOT NULL
3. **Snapshot relacional:** `VentaItemOfertaProductos` preserva la composición de ofertas y pizzas mitad-mitad

Este enfoque combina:
- **Integridad referencial** cuando los datos existen
- **Preservación histórica** cuando se eliminan
- **Reportes precisos** basados en snapshots, no en referencias

### Posibles Mejoras Futuras

- Agregar tabla de **Clientes** para tracking de ventas por cliente
- Agregar campo `orden` en `OfertaItems` para definir el orden de visualización
- Agregar campo `descuento_porcentaje` en `Ofertas` como alternativa al precio fijo
- Agregar índices full-text en `item_nombre` para búsquedas avanzadas
- Implementar particionamiento de tabla `Ventas` por fecha para mejorar performance en reportes históricos

---

**Última actualización:** Marzo 2026  
**Versión del esquema:** 3.0 (con usuarios, stock, gastos, auditoría y pizzas mitad-mitad)

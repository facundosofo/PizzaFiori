# Lógica de cálculo de fracciones para reportes y analíticas

## Objetivo

Explicar cómo se calculan y formatean las cantidades fraccionarias en los reportes y servicios de analítica de PizzaFiori.

## Regla general

Cuando una cantidad no es entera, se convierte a una fracción o a una mezcla de entero + fracción para que sea legible en pantalla o en PDF.

Ejemplos:
- 1 -> "1"
- 0.5 -> "1/2"
- 1.25 -> "1 2/8"
- 1.5 -> "1 4/8"

## Proceso de cálculo

1. Se toma la cantidad vendida como valor decimal.
2. Se identifica un denominador de referencia:
   - si el producto tiene una base fraccionaria menor a 1, se infiere el denominador a partir de esa base;
   - si no, se usa el denominador por defecto 8.
3. Se transforma la parte fraccional en numerador sobre ese denominador.
4. Se formatea como:
   - entero puro si no hay fracción;
   - fracción simple si la cantidad es menor a 1;
   - entero + fracción si hay parte entera y parte fraccionaria.

## De dónde sale la porción del producto

La porción no se calcula desde un campo de texto libre ni desde una regla fija del nombre del producto. Se identifica a partir de la estructura del producto y del precio asociado.

### 1) Producto normal

Cuando una venta contiene un producto directo, el sistema intenta leer el precio del producto con una cantidad base menor a 1. Ese dato viene de la tabla de precios del producto.

Campo relevante:
- ProductPrice.cantidad
- ProductPrice.precio

La lógica hace lo siguiente:
- busca los precios cuyo valor de cantidad sea menor a 1;
- toma la menor cantidad fraccionaria que encuentre;
- a partir de esa base, deduce el denominador compatible (2, 4 u 8).

Ejemplo:
- si el producto tiene un precio con cantidad 0.5, entonces la base es 1/2;
- si tiene 0.25, entonces es 1/4;
- si tiene 0.125, entonces es 1/8.

### 2) Producto dentro de una oferta

Cuando el producto se vende dentro de una oferta, la lógica no busca el precio del producto principal directamente. En ese caso se usa el snapshot de la oferta, que guarda los productos incluidos en esa promoción.

Campo relevante:
- SaleItemOfferProduct
- SaleItem.oferta_productos_snapshot

Esto permite que el reporte pueda seguir mostrando la porción correcta incluso cuando el producto fue vendido como parte de una promoción.

La lógica de la oferta hace lo siguiente:
- recorre los productos que quedaron guardados en el snapshot de la oferta;
- por cada producto, toma su cantidad y su categoría;
- usa la misma inferencia de base para obtener el denominador correcto.

## Cómo se identifica la porción

La identificación de la porción se hace de forma indirecta:

1. Se mira la cantidad base del precio del producto.
2. Si esa cantidad es menor a 1, se convierte a una fracción interna.
3. Se calcula el inverso de esa base para obtener el denominador.

Ejemplo:
- base 0.5 => 1 / 0.5 = 2 => denominador 2
- base 0.25 => 1 / 0.25 = 4 => denominador 4
- base 0.125 => 1 / 0.125 = 8 => denominador 8

## Qué pasa si hay varios productos mezclados

Si una categoría contiene productos con diferentes bases, se resuelve un denominador común para poder sumar correctamente.

Por ejemplo:
- 1/2 + 1/4 + 1/8

Se convierte a denominador 8:
- 4/8 + 2/8 + 1/8 = 7/8

Eso es lo que evita que el resumen se vea mal.

## Denominadores soportados

Los denominadores usados normalmente son:
- 2 para medios
- 4 para cuartos
- 8 para octavos

## Cálculo para agregados por categoría

Cuando una categoría mezcla productos con bases diferentes, por ejemplo:
- Papas: 1/2
- Tartas: 1/4
- Pizzas: 1/8

el sistema debe usar un denominador común para que la suma se represente correctamente.

En ese caso se resuelve un denominador común usando el mínimo común múltiplo de los denominadores involucrados.

Ejemplo:
- 1/2, 1/4 y 1/8 -> denominador común 8

Esto evita que una suma se muestre con una base inconsistente.

## Funciones involucradas

- format_mixed_fraction_quantity(value, denominator): formatea la cantidad final.
- infer_fraction_denominator(...): intenta inferir el denominador según la base del producto.
- resolve_fraction_denominator(...): resuelve un denominador común cuando hay varias fracciones mezcladas.

## Recomendación de negocio

Para que la visualización sea consistente:
- si un elemento individual tiene una base propia, usar esa base;
- si se está agregando por categoría o por resumen general, usar un denominador común para toda la mezcla.

## Ejemplo práctico

Supongamos que una categoría tiene:
- 1 unidad de un producto de base 1/2
- 1 unidad de un producto de base 1/4
- 1 unidad de un producto de base 1/8

La representación más consistente es:
- 1/2 + 1/4 + 1/8 = 7/8

Y se mostrará como:
- 7/8

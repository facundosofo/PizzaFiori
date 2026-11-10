# Guía UX: componentes y modos de color

La interfaz está organizada con CSS Modules por superficie funcional. Cada módulo usa una clase local en la raíz del componente para limitar sus reglas a esa superficie. Así, cambiar un título, precio, botón, campo o tarjeta no debería modificar otra pantalla.

## Mapa de pantallas y componentes

| Pantalla o componente | Estilos |
| --- | --- |
| Estructura principal, encabezado, marca, hero, cierre y pie | [`AppShell.module.css`](./src/AppShell.module.css) |
| Menú, navegación, categorías y sección de promociones | [`Menu.module.css`](./src/Menu.module.css) |
| Estado de carga, tarjetas skeleton, error de catálogo y menú vacío | [`States.module.css`](./src/States.module.css) |
| Tarjetas de producto, imágenes, presentaciones, precios y cantidades | [`Product.module.css`](./src/Product.module.css) |
| Pizza mitad y mitad: tarjeta de entrada, selección de sabores y diálogo de confirmación | [`PizzaHalf.module.css`](./src/PizzaHalf.module.css) |
| Sección de promociones, tarjetas y configuración de promo | [`Offer.module.css`](./src/Offer.module.css) |
| Carrito, pasos de checkout, datos de entrega/pago, revisión y enlace a WhatsApp | [`Checkout.module.css`](./src/Checkout.module.css) |
| Reset, variables de tema, foco accesible y utilidades globales | [`styles.css`](./src/styles.css) |

Las clases locales de raíz se aplican en [`App.tsx`](./src/App.tsx). Dentro de cada módulo, los selectores de las clases existentes del HTML están bajo esa raíz local; no agregues selectores de una pantalla en otro módulo.

## Cómo hacer un cambio visual

1. Identificá la pantalla o componente en el mapa y abrí su módulo.
2. Modificá el selector del elemento concreto. Por ejemplo, el botón de agregar de una promo se ajusta en `Offer.module.css`, sin alterar agregar producto, pizza mitad y mitad ni checkout.
3. Si el elemento tiene una regla `[data-theme="dark"]`, actualizá también esa variante.
4. Si el cambio aplica solo a mobile, ajustá la media query de ese módulo; evitá introducir reglas responsive globales.
5. Si un elemento no tiene una clase propia y necesitás modificarlo de forma independiente, asignale una clase semántica y estilala en el módulo de su componente.
6. Reservá `styles.css` para tokens compartidos, reset, foco accesible, movimiento reducido y utilidades que intencionalmente usan varias pantallas. No agregues ahí estilos visuales específicos de un componente.

`action-button` es una utilidad intencionalmente compartida solo para alinear el contenido base de ciertos botones. Sus dimensiones, tipografía, colores, bordes y estados se definen en el módulo del componente.

## Modo claro y modo oscuro

`src/styles.css` es la única fuente de verdad de los colores. `:root` define el tema claro y `[data-theme="dark"]` sobrescribe los tokens semánticos para el oscuro; `[data-theme="light"]` ajusta los acentos de marca. Los siete CSS Modules consumen variables y no deben contener valores de color literales.

| Variable | Uso | Claro | Oscuro |
| --- | --- | --- | --- |
| `--color-bg` | Fondo de página y diálogos | `#fffaf1` | `#0d0d0d` |
| `--color-surface` | Superficie de tarjetas | `#fffdf8` | `#151515` |
| `--color-text` | Texto principal | `#2e332b` | `#f5f5f5` |
| `--color-text-muted` | Texto secundario | `#77766d` | `#9ca3af` |
| `--color-border` | Bordes y separadores | `#e9e3d7` | `rgba(255, 255, 255, .08)` |
| `--color-green` | Acciones y énfasis verdes | `#536b4b` | `#22c55e` |
| `--color-heading` | Títulos de tono verde | `#384c35` | `#d5e1cf` |
| `--color-brand-green` | Acento verde de marca | `#168344` | `#22c55e` |
| `--color-brand-red` | Acento rojo de marca y promociones | `#c93632` | `#ef4444` |
| `--color-brand-green-glow` | Resplandor opcional del acento verde | `none` | `0 0 8px rgba(34, 197, 94, .42)` |
| `--color-brand-red-glow` | Resplandor opcional del acento rojo | `none` | `0 0 8px rgba(239, 68, 68, .34)` |
| `--color-white` | Blanco explícito en estados y contenido | `#fff` | `#fff` |

El rojo en PizzaFiori también es un acento de marca (por ejemplo, promociones); no se debe tratar automáticamente como color destructivo. La referencia de otro proyecto aporta la centralización semántica, no una paleta ni significados que haya que copiar literalmente.

### Cambiar un color

1. Para un color compartido, ajustá el token semántico correspondiente en `:root` y su valor en `[data-theme="dark"]`. Conservá el significado del token en ambos temas.
2. Para una excepción ya existente, buscá su `--palette-*` en `styles.css`; esos tokens conservan los colores locales que todavía no tienen un rol compartido. Un solo token puede aparecer en varias pantallas.
3. Si una nueva excepción solo pertenece a un componente, definí un token semántico con alcance claro (por ejemplo, `--color-offer-card-bg`) en la sección global de tokens, asignale valores para ambos temas y consumilo desde el CSS Module de esa pantalla. No agregues el color literal al módulo.
4. No agregues nuevos usos de `--palette-*` para estilos nuevos: preferí un token semántico. Los tokens de paleta existentes son una capa de compatibilidad para preservar exactamente el aspecto de los colores que se centralizaron.

Los `--palette-*` mantienen expresiones de color ya usadas en componentes, con nombres basados en el hexadecimal o en sus canales RGB/alpha para encontrarlas fácilmente. Los valores hex, `rgb()` y `rgba()` solo se escriben en `styles.css`, al definir tokens.

La web actualmente fuerza el modo oscuro desde `App.tsx` y el selector de tema está deshabilitado. Los estilos y tokens claros se conservan, pero para inspeccionarlos durante el desarrollo hay que quitar temporalmente `data-theme="dark"` del elemento raíz o probarlos con una herramienta de estilos; no se ofrece un control de tema al cliente.

## Criterios de experiencia para todas las pantallas

- Mantené texto normal con contraste mínimo de 4.5:1 y texto grande o elementos visuales esenciales con 3:1. Medilo sobre el fondo final, incluyendo transparencias y degradados.
- En modo claro, priorizá texto oscuro sobre superficies claras; en modo oscuro, texto claro sobre superficies oscuras. No uses grises tenues para información importante.
- Mantené jerarquía clara entre título, contenido, precio y acción. No dependas solo del color para comunicar selección, error o disponibilidad.
- Conservá estados distinguibles para hover, foco de teclado, seleccionado, error y deshabilitado. El foco debe seguir visible en ambos temas.
- Revisá el checkout completo (carrito, datos y confirmación), los diálogos y las tarjetas en mobile, incluyendo anchos pequeños y texto ampliado.
- Los controles táctiles deben mantener un área cómoda; el texto no debe recortarse ni solaparse con iconos.
- Respetá `prefers-reduced-motion` para animaciones y transiciones.

## Verificación

Desde `web-pedidos`, ejecutá:

```powershell
npm run build
```

Además del build, revisá visualmente modo claro y oscuro, mobile y desktop; el build no detecta problemas de contraste, recorte o jerarquía.

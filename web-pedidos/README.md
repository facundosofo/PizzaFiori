# Web pública de pedidos Pizza Fiori

Aplicación React + TypeScript + Vite independiente del frontend administrativo. Lee el catálogo público, permite armar un carrito, valida los datos del pedido y prepara un mensaje para enviar manualmente por WhatsApp.

## Desarrollo local

Para ajustar los estilos aislados de las pantallas y componentes, y consultar los criterios de ambos temas, usá la [Guía UX de componentes y modos de color](./UX-THEME-GUIDE.md).

1. Copiar `.env.example` a `.env.local` (o configurar esas variables en `.env`).
2. Cambiar `VITE_CATALOG_POINTER_URL` por la URL HTTPS pública del objeto `catalogo-actual.json` en R2.
3. Configurar `VITE_HIDDEN_CATEGORIES` con los nombres exactos de las categorías que no se deben mostrar, separados por comas (por ejemplo, `Extra`).
4. Configurar `VITE_WHATSAPP_PHONE` con el teléfono comercial en formato internacional, solo dígitos (código de país + número, sin `+`, espacios ni guiones).
5. Opcionalmente, configurar `VITE_INSTAGRAM_URL`, `VITE_FACEBOOK_URL`, `VITE_GOOGLE_MAPS_URL` y `VITE_WHATSAPP_URL` para mostrar esos accesos en el footer. Para Maps, pegar el enlace compartido de la ubicación de Google Maps. `VITE_WHATSAPP_URL` puede omitirse para generar el enlace desde `VITE_WHATSAPP_PHONE`. Configurar `VITE_PHONE_NUMBER` para un teléfono de llamadas; si se omite, el botón de teléfono reutiliza `VITE_WHATSAPP_PHONE`. Los accesos sin URL válida no se muestran.
6. Desde esta carpeta, ejecutar:

   ```powershell
   npm install
   npm run dev
   ```

La web pública se sirve en `http://localhost:5174`, separada del frontend administrativo que usa el puerto `5173`. El puerto es estricto: si `5174` está ocupado, Vite informa el conflicto en lugar de cambiar silenciosamente a otro.

Si la URL de prueba no está configurada o R2 no permite CORS para el origen `http://localhost:5174`, la página muestra un error y permite reintentar. No se incluyen datos de muestra que puedan confundirse con el menú real.

## Cloudflare Pages

- **Directorio raíz del proyecto:** `web-pedidos`
- **Comando de build:** `npm run build`
- **Directorio de salida:** `dist`
- **Variables de build:**
  - `VITE_CATALOG_POINTER_URL=https://<dominio-publico>/catalogo-actual.json`
  - `VITE_WHATSAPP_PHONE=<código-de-país-y-número-solo-dígitos>`
  - `VITE_HIDDEN_CATEGORIES=Extra`
  - `VITE_INSTAGRAM_URL=https://instagram.com/<cuenta>` (opcional)
  - `VITE_FACEBOOK_URL=https://facebook.com/<cuenta>` (opcional)
  - `VITE_GOOGLE_MAPS_URL=<enlace-compartido-de-Google-Maps>` (opcional)
  - `VITE_WHATSAPP_URL=https://wa.me/<código-de-país-y-número>` (opcional; si falta, se deriva de `VITE_WHATSAPP_PHONE`)
  - `VITE_PHONE_NUMBER=<código-de-país-y-número-solo-dígitos>` (opcional; si falta, reutiliza `VITE_WHATSAPP_PHONE`)

Las variables de build identifican el catálogo público, teléfonos, enlaces de redes y categorías que se ocultan; no deben contener credenciales. Los accesos sociales, ubicación y contacto se muestran únicamente cuando tienen una URL o número válido. Los medios de pago son Efectivo y Transferencia. El porcentaje de recargo por transferencia y el monto mínimo para delivery gratis se administran desde Configuración en el portal interno y se publican en el catálogo de R2. El mínimo inicial para delivery es $13.000, calculado sobre el subtotal de productos y promociones antes del recargo por transferencia. Cuando el pedido no alcanza ese monto, la opción de delivery se deshabilita y se indica cuánto falta; Retiro sigue disponible. Después de cambiar cualquiera de esos valores en Configuración, volvé a publicar el catálogo para actualizar la web pública. Los nombres de categoría se comparan sin distinguir mayúsculas y minúsculas. El número se valida (8 a 15 dígitos) y se normaliza antes de generar el enlace oficial de WhatsApp. Configurá las variables en Cloudflare Pages y volvé a desplegar tras modificarlas. Configurar en R2 CORS para el dominio de Pages y permitir GET/HEAD desde ese origen. El puntero se solicita con revalidación y el catálogo versionado con caché larga.

## Publicar o actualizar el catálogo y su PDF

La aplicación de pedidos en Pages es estática. El endpoint autenticado del backend `POST /config/catalog/publish` genera y publica en R2 tanto el JSON que consume la web como el PDF público para compartir. El backend y el portal administrativo no necesitan estar desplegados en Pages, pero sí deben estar ejecutándose con acceso a la base de datos y con R2 configurado al momento de publicar.

1. Guardá en el sistema los productos, categorías, precios, imágenes, promociones y configuración que querés hacer públicos.
2. Iniciá el backend con R2 habilitado (`R2_ENABLED=true`) y las variables `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` y `R2_PUBLIC_BASE_URL` configuradas en el `.env` del backend. Nunca agregues las credenciales de escritura a Pages ni a variables `VITE_*`.
3. En el portal administrativo, iniciá sesión como administrador y abrí **Configuración → Catálogo para pedidos → Publicar catálogo**.
4. Al terminar, usá el enlace del PDF público que aparece en Configuración. El endpoint devuelve esa misma URL como `menu_pdf_url`; la dirección estable es `{R2_PUBLIC_BASE_URL}/menu-pizza-fiori.pdf`.

El backend carga primero las imágenes nuevas, publica el JSON versionado y el PDF, y actualiza `catalogo-actual.json` al final. El PDF se sirve inline con revalidación para que la misma URL muestre la versión más reciente. Si ya existía un catálogo sin PDF, la siguiente publicación también genera y carga el PDF. Las reglas de caché de Cloudflare deben excluir `catalogo-actual.json` y `menu-pizza-fiori.pdf` de caché larga.

## Alcance implementado

- Lectura del puntero actual y del JSON versionado, sin autenticación ni llamadas al backend administrativo.
- Validación de la estructura del contrato público antes de mostrar los datos.
- Navegación por categorías, tarjetas con imágenes y precios por presentación, y sección de ofertas publicadas.
- Entrada de pizza mitad/mitad al inicio de la categoría de pizzas; abre una pantalla completa con selección vertical de sabores y fotografías. Se requieren dos sabores distintos y se usa el precio unitario más alto, igual que en el backend.
- Las cantidades de precio fraccionarias se muestran como porciones (por ejemplo, `0.5` como «Porción 1/2»).
- Las ofertas permiten elegir cantidades dentro de una categoría o seleccionar una opción; los productos fijos se incluyen automáticamente.
- Alternativa visual para productos sin imagen o cuya imagen no carga.
- Estados de carga, error con reintento y catálogo vacío.
- Carrito en memoria con presentaciones/precios del catálogo y ajustes de cantidad, en un paso separado de los datos del cliente.
- Las pizzas mitad/mitad conservan sus dos sabores en el carrito y en el mensaje de WhatsApp, y se pueden agregar varias unidades de la misma combinación.
- Checkout a pantalla completa en tres pasos: revisar el carrito, completar entrega y pago, y confirmar el resumen antes de abrir WhatsApp.
- Observaciones separadas para extras o sustituciones de comida en el carrito, e indicaciones de entrega o pago en el formulario; ambas se incluyen por separado en el mensaje de WhatsApp.
- Formulario validado para delivery o retiro, con Efectivo o Transferencia.
- Recargo porcentual de transferencia incluido en el catálogo público; se aplica y se informa en el resumen y el mensaje de WhatsApp solo cuando el cliente elige ese medio de pago.
- Delivery gratis disponible desde el monto mínimo publicado; el checkout bloquea la opción por debajo del umbral y muestra cuánto falta. El umbral usa el subtotal antes del recargo por transferencia.
- Resumen final con productos, cantidades, subtotales, datos de entrega/pago y total estimado; si corresponde, informa el envío gratis.
- Mensaje dinámico codificado y enlace oficial a WhatsApp; el cliente debe presionar «Enviar» y el local confirmar el pedido.
- El pedido se confirma manualmente por el local; abrir WhatsApp no crea ni confirma el pedido.
- Modo oscuro exclusivo.
- Maquetación responsive, navegación accesible y respeto de `prefers-reduced-motion`.

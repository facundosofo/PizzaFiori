# Web pública de pedidos Pizza Fiori

Aplicación React + TypeScript + Vite independiente del frontend administrativo. Lee el catálogo público, permite armar un carrito, valida los datos del pedido y prepara un mensaje para enviar manualmente por WhatsApp.

## Desarrollo local

1. Copiar `env.example` a `.env.local` (o configurar esas variables en `.env`).
2. Cambiar `VITE_CATALOG_POINTER_URL` por la URL HTTPS pública del objeto `catalogo-actual.json` en R2.
3. Ajustar `VITE_ORDER_PAYMENT_METHODS` a los medios de pago aprobados por el local, separados por comas.
4. Configurar `VITE_WHATSAPP_PHONE` con el teléfono comercial en formato internacional, solo dígitos (código de país + número, sin `+`, espacios ni guiones).
5. Desde esta carpeta, ejecutar:

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
  - `VITE_ORDER_PAYMENT_METHODS=Efectivo,Transferencia`

Las variables de build identifican el catálogo público, el teléfono comercial y los medios de pago a mostrar; no deben contener credenciales. El número se valida (8 a 15 dígitos) y se normaliza antes de generar el enlace `wa.me`. Configurá las variables en Cloudflare Pages y volvé a desplegar tras modificarlas. Configurar en R2 CORS para el dominio de Pages y permitir GET/HEAD desde ese origen. El puntero se solicita con revalidación y el catálogo versionado con caché larga.

## Alcance implementado

- Lectura del puntero actual y del JSON versionado, sin autenticación ni llamadas al backend administrativo.
- Validación de la estructura del contrato público antes de mostrar los datos.
- Navegación por categorías, tarjetas con imágenes y precios por presentación, y sección de ofertas publicadas.
- Las cantidades de precio fraccionarias se muestran como porciones (por ejemplo, `0.5` como «Porción 1/2»).
- Las ofertas permiten elegir cantidades dentro de una categoría o seleccionar una opción; los productos fijos se incluyen automáticamente.
- Alternativa visual para productos sin imagen o cuya imagen no carga.
- Estados de carga, error con reintento y catálogo vacío.
- Carrito en memoria con presentaciones/precios del catálogo y ajustes de cantidad.
- Formulario validado para delivery o retiro y medios de pago configurables.
- Resumen final con productos, cantidades, subtotales, datos de entrega/pago y total estimado.
- Mensaje dinámico codificado y enlace oficial a WhatsApp; el cliente debe presionar «Enviar» y el local confirmar el pedido.
- Envío indicado como «A confirmar»; no se crean pedidos ni se muestra confirmación automática.
- Modo oscuro predeterminado con alternativa clara; la elección queda guardada en el navegador.
- Maquetación responsive, navegación accesible y respeto de `prefers-reduced-motion`.

# 🍕 Documentación - Página de Productos

## Estructura de Componentes

### 1. **ProductCard.tsx**
Tarjeta individual del producto con animaciones y modal integrado.

**Características:**
- ✨ Animaciones con Framer Motion (entrada, hover, tap)
- 🖼️ Imagen con `object-fit: cover`
- 🎯 Placeholder automático si no hay imagen
- 🟢 Título en MAYÚSCULAS con glow neón
- 💰 Mostrador de precio
- 🎬 Click para abrir modal

**Props:**
```typescript
interface ProductCardProps {
  producto: Producto;
  onProductUpdate?: (producto: Producto) => void;
}
```

**Uso:**
```tsx
<ProductCard 
  producto={producto} 
  onProductUpdate={handleProductUpdate}
/>
```

---

### 2. **ProductModal.tsx**
Modal para ver detalles del producto y editarlo.

**Características:**
- 📱 Modal responsive con animaciones de entrada/salida
- 👁️ Vista de producto con todos los detalles
- ✏️ Modo edición para nombre y precio
- 💾 Guardar cambios o cancelar

**Props:**
```typescript
interface ProductModalProps {
  producto: Producto | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (producto: Producto) => void;
}
```

**Uso:**
```tsx
const [isOpen, setIsOpen] = useState(false);
const [selectedProduct, setSelectedProduct] = useState<Producto | null>(null);

<ProductModal
  producto={selectedProduct}
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onSave={handleSave}
/>
```

---

### 3. **SkeletonLoader.tsx**
Cargador de esqueleto animado mientras se traen los datos.

**Características:**
- 📦 Simula estructura de tarjeta de producto
- ⏳ Animación pulse continua
- 🎨 Estilos consistentes con ProductCard

**Uso:**
```tsx
{loading ? (
  <div className="skeleton-grid">
    {Array.from({ length: 8 }).map((_, i) => (
      <SkeletonLoader key={i} />
    ))}
  </div>
) : (
  // Mostrar productos
)}
```

---

### 4. **ProductForm.tsx**
Formulario para crear o editar productos (completo).

**Características:**
- 📝 Campos para nombre, categoría, precio e imagen
- 🖼️ Preview de imagen en tiempo real
- ✅ Validación de campos
- 🔄 Modo crear/editar automático
- ♿ Estados disabled durante carga

**Props:**
```typescript
interface ProductFormProps {
  producto?: Producto | null;
  categorias: { id: number; nombre: string }[];
  onSave: (producto: Producto) => Promise<void>;
  onCancel: () => void;
}
```

---

### 5. **ProductsPage.tsx**
Página principal que agrupa productos por categoría.

**Características:**
- 📚 Agrupa productos por categoría automáticamente
- 🎬 Scroll horizontal estilo Netflix
- ⏳ Skeleton loaders mientras carga
- 🔄 Actualización de productos en tiempo real

**Estado:**
```tsx
const [productos, setProductos] = useState<Producto[]>([]);
const [categorias, setCategorias] = useState<Categoria[]>([]);
const [loading, setLoading] = useState(true);
```

---

## 📐 Interfaces TypeScript

### Producto
```typescript
export interface Producto {
  id: number;
  nombre: string;
  precio_venta: number;
  categoria_id: number;
  imagen?: string;
}
```

### Categoria
```typescript
export interface Categoria {
  id: number;
  nombre: string;
}
```

---

## 🎨 Estilos CSS

### Archivos CSS
- **product-card.css** - Estilos principales (grid, scroll, cards)
- **product-modal.css** - Modal y formulario de edición inline
- **product-form.css** - Formulario completo de crear/editar
- **skeleton.css** - Animaciones de carga

### Paleta de Colores
- 🔴 Rojo: `#ff3b3b` (color principal de acento)
- 🟢 Verde: `#6dff7a` (botones confirmación)
- ⚫ Dark: `#0d0d0d` - `#1e1e1e` (fondos)
- ⚪ Light: `#f5f5f5` (texto principal)

---

## 🎬 Animaciones

### Framer Motion
- **Entrada de tarjeta:** `opacity: 0 → 1, y: 20 → 0`
- **Hover:** `scale: 1 → 1.08, y: 0 → -8`
- **Modal:** `scale: 0.8 → 1, opacity: 0 → 1`
- **Skeleton:** Efecto shimmer infinito

---

## 📱 Responsividad

Todos los componentes tienen breakpoint en `768px`:
- Reducen padding y tamaños de fuente
- Grid se adapta a pantallas pequeñas
- Modal ocupa 90% del ancho en móvil

---

## 🔌 Integración Backend

### Endpoints esperados
```
GET  /productos          → Listar todos
GET  /categorias         → Listar categorías
POST /productos          → Crear producto
PUT  /productos/{id}     → Actualizar producto
DEL  /productos/{id}     → Eliminar producto
POST /productos/{id}/upload → Subir imagen
```

### URL Base
```typescript
const API_URL = "http://127.0.0.1:8000";
const IMAGEN_URL = `${API_URL}/{imagen_path}`;
```

---

## 🚀 Performance

- ✅ Lazy loading de imágenes
- ✅ Memoización opcional con `React.memo()`
- ✅ Scroll horizontal nativo (mejor performance)
- ✅ Animaciones con GPU (transform, opacity)
- ✅ Debounce en búsqueda/filtros (si se agrega)

---

## 📋 Checklist Implementación

- [x] Componentes React con TypeScript
- [x] Interfaces bien tipadas
- [x] Framer Motion para animaciones
- [x] CSS clásico y modular
- [x] Modal separado
- [x] Skeleton loader
- [x] Scroll horizontal estilo Netflix
- [x] Formulario completo
- [x] Responsive design
- [x] Dark mode theme
- [x] Manejo de errores
- [x] Estados de carga

---

## 💡 Mejoras Futuras

- [ ] Agregar búsqueda de productos
- [ ] Filtros por categoría/precio
- [ ] Paginación opcional
- [ ] Carrito de compras
- [ ] Favoritos/wishlist
- [ ] Calificaciones y comentarios
- [ ] Lazy load de imágenes
- [ ] Internacionalización (i18n)


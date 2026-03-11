# 🎨 Guía de UX/UI — Sistema de Colores (Dark + Light)

## 📋 Índice
1. [Filosofía de Color](#filosofía-de-color)
2. [Sistema de Temas](#sistema-de-temas)
3. [Paleta de Colores — Variables CSS](#paleta-de-colores--variables-css)
4. [Regla 60/30/10](#regla-603010)
5. [Uso de Colores por Contexto](#uso-de-colores-por-contexto)
6. [Mejores Prácticas](#mejores-prácticas)
7. [Casos de Uso Específicos](#casos-de-uso-específicos)
8. [Paleta de Gráficos (Charts)](#paleta-de-gráficos-charts)
9. [Migración Pendiente de Hardcodeados](#migración-pendiente-de-hardcodeados)

---

## 🎯 Filosofía de Color

### Principios Fundamentales

Los siguientes principios aplican **en ambos modos** (dark y light). El significado semántico de cada color se mantiene idéntico; solo cambian los valores concretos según el tema activo.

**VERDE** → Dinero, éxito y acciones positivas
- Totales monetarios
- Confirmaciones
- Estados completados
- Acciones de avance/búsqueda

**ROJO** → Acciones críticas y destructivas
- Eliminar registros
- Errores graves
- Alertas de peligro
- Limpiar/resetear datos

**NEUTRALES** → Legibilidad y jerarquía
- Textos principales y secundarios
- Bordes y separadores
- Fondos base y superficies
- Estados inactivos

> **Regla cardinal**: nunca usar valores hex directos. Siempre usar `var(--color-*)`, `var(--gradient-*)` o `var(--shadow-*)` para que ambos modos funcionen automáticamente.

---

## 🏗️ Sistema de Temas

### Arquitectura

El sistema de temas vive en un único archivo CSS:

```
frontend/src/styles/theme.css
```

Usa **CSS Custom Properties** con dos selectores:
- `:root` → **Dark Mode** (por defecto)
- `[data-theme="light"]` → **Light Mode** (override)

Los estilos globales en `index.css` importan `theme.css` y aplican las variables:

```css
/* index.css */
@import "./styles/theme.css";

body {
  font-family: var(--font-sans);
  background: var(--gradient-app);
  color: var(--color-text);
}
```

### Cómo funciona el toggle

El toggle se encuentra en el **footer del Sidebar** (componente `Sidebar.tsx`):

```tsx
// Estado persistido en localStorage con clave "ui-theme"
const [themeMode, setThemeMode] = usePersistentState<"light" | "dark">(
  "ui-theme",
  "dark"
);

// Aplica el tema al <html>
useEffect(() => {
  document.documentElement.dataset.theme = themeMode;
  document.documentElement.style.colorScheme = themeMode;
}, [themeMode]);
```

El toggle utiliza iconos **Sun** (claro) y **Moon** (oscuro) con un switch animado.

### Regla de desarrollo

```
✅  color: var(--color-text);
✅  background: var(--gradient-card);
✅  border: 2px solid var(--color-border-strong);

❌  color: #f5f5f5;
❌  background: #1a1a1a;
❌  border: 2px solid rgba(255, 255, 255, 0.2);
```

**Siempre** referenciar variables. El único momento en que se escriben valores hex/rgba es **dentro** de `theme.css` al definir las variables.

---

## 🎨 Paleta de Colores — Variables CSS

> **Fuente de verdad**: `frontend/src/styles/theme.css`

### Colores de Base

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-bg` | `#0d0d0d` | `#f7f8fa` | Fondo principal de la app |
| `--color-bg-2` | `#1a1a1a` | `#ffffff` | Fondo secundario / secciones |
| `--color-surface` | `#151515` | `#ffffff` | Tarjetas, contenedores base |
| `--color-surface-2` | `#1f1f1f` | `#f1f5f9` | Superficies elevadas |
| `--color-surface-3` | `#262626` | `#e2e8f0` | Superficies más elevadas |

### Textos

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-text` | `#f5f5f5` | `#111827` | Texto primario, títulos |
| `--color-text-muted` | `#9ca3af` | `#475569` | Texto secundario, labels |

### Bordes e Interacción

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-border` | `rgba(255,255,255, 0.08)` | `rgba(15,23,42, 0.12)` | Bordes sutiles |
| `--color-border-strong` | `rgba(255,255,255, 0.2)` | `rgba(15,23,42, 0.2)` | Bordes prominentes |
| `--color-hover` | `rgba(255,255,255, 0.08)` | `rgba(15,23,42, 0.06)` | Fondo en hover |

### Verde (Acento — Dinero/Éxito)

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-accent` | `#22c55e` | `#16a34a` | Verde principal, precios |
| `--color-accent-strong` | `#16a34a` | `#15803d` | Gradientes, estados activos |
| `--color-accent-soft` | `rgba(34,197,94, 0.15)` | `rgba(22,163,74, 0.12)` | Fondo verde sutil |

### Rojo (Danger — Solo acciones críticas)

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-danger` | `#ef4444` | `#dc2626` | Eliminar, errores |
| `--color-danger-bg` | `rgba(239,68,68, 0.15)` | `rgba(220,38,38, 0.12)` | Fondo danger sutil |

### Overlay

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--color-overlay` | `rgba(0,0,0, 0.45)` | `rgba(15,23,42, 0.18)` | Fondo de modales |

### Gradientes

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--gradient-app` | `135deg, #0d0d0d → #1a1a1a` | `135deg, #f7f8fa → #e9edf3` | Fondo de la aplicación |
| `--gradient-sidebar` | `180deg, #111111 → #0b0b0b` | `180deg, #ffffff → #eef2f7` | Fondo del sidebar |
| `--gradient-hero` | `radial, #1a1a1a → #0d0d0d` | `radial, #ffffff → #eef2f6` | Sección hero |
| `--gradient-card` | `180deg, #1f1f1f → #151515` | `180deg, #ffffff → #f1f5f9` | Tarjetas |
| `--gradient-card-hover` | `180deg, #262626 → #1b1b1b` | `180deg, #f8fafc → #e8edf4` | Tarjetas en hover |
| `--gradient-accent` | `135deg, #22c55e → #16a34a` | `135deg, #16a34a → #15803d` | Botones primarios |

### Sombras

| Variable | Dark Mode | Light Mode | Uso |
|---|---|---|---|
| `--shadow-card` | `0 10px 20px rgba(0,0,0, 0.4)` | `0 10px 20px rgba(15,23,42, 0.12)` | Sombra de tarjetas |
| `--shadow-card-hover` | `0 18px 35px rgba(0,0,0, 0.6)` | `0 18px 35px rgba(15,23,42, 0.18)` | Tarjetas en hover |
| `--shadow-inset` | `inset 0 1px 0 rgba(255,255,255, 0.05)` | `inset 0 1px 0 rgba(255,255,255, 0.7)` | Relieve interior sutil |
| `--shadow-inset-strong` | `inset 0 1px 0 rgba(255,255,255, 0.08)` | `inset 0 1px 0 rgba(255,255,255, 0.9)` | Relieve interior fuerte |
| `--shadow-sidebar` | `0 20px 40px rgba(0,0,0, 0.45)` | `0 20px 40px rgba(15,23,42, 0.2)` | Sombra del sidebar |
| `--shadow-accent` | `0 0 10px rgba(34,197,94, 0.35)` | `0 0 10px rgba(22,163,74, 0.25)` | Glow verde |

### Layout y Diseño

| Variable | Valor | Uso |
|---|---|---|
| `--font-sans` | `"Avenir", "Segoe UI", …` | Familia tipográfica |
| `--space-1` … `--space-6` | `4px` … `32px` | Sistema de espaciado |
| `--radius-sm / md / lg` | `8px / 12px / 16px` | Bordes redondeados |
| `--z-overlay` | `10` | Z-index del overlay |
| `--z-sidebar` | `20` | Z-index del sidebar |

---

## 📐 Regla 60/30/10

### Distribución Visual

**60% — Neutrales** (fondos y estructura)
- `var(--color-bg)`, `var(--color-bg-2)` — Fondos principales
- `var(--color-surface)`, `var(--color-surface-2)` — Contenedores
- `var(--gradient-card)` — Tarjetas

**30% — Textos y bordes** (legibilidad)
- `var(--color-text)` — Textos principales
- `var(--color-text-muted)` — Textos secundarios
- `var(--color-border)`, `var(--color-border-strong)` — Separadores

**10% — Acentos** (verde + rojo)
- ~8% `var(--color-accent)` — Dinero, éxito, acciones positivas
- ~2% `var(--color-danger)` — Solo acciones críticas

### Ejemplo Visual
```
┌───────────────────────────────────────────┐
│ [60%] Fondo: var(--color-bg)              │
│                                           │
│ [30%] Texto: var(--color-text)            │
│ [30%] Bordes: var(--color-border)         │
│                                           │
│ [8%]  Total: $1,234.56 (--color-accent)   │
│ [2%]  [Eliminar] (--color-danger)         │
└───────────────────────────────────────────┘
```

Este esquema se adapta automáticamente a ambos modos gracias a las variables CSS.

---

## 🎯 Uso de Colores por Contexto

### Tablas y Listados

#### Headers
```css
/* ✅ CORRECTO — Variables que funcionan en ambos modos */
.table-header {
  background: var(--color-bg-2);
  color: var(--color-accent);
  border-bottom: 2px solid var(--color-accent-soft);
}
```

```css
/* ❌ INCORRECTO — Hex hardcodeado, rompe light mode */
.table-header {
  background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
  color: #22c55e;
}
```

#### Filas
```css
/* ✅ CORRECTO */
.row:hover {
  background: var(--color-accent-soft);
  border-left: 3px solid var(--color-accent);
}
```

#### Bordes
```css
/* ✅ CORRECTO */
.table {
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-card);
}
```

---

### Botones y Acciones

#### Acción Positiva (Buscar, Guardar, Continuar)
```css
.btn-primary {
  background: var(--gradient-accent);
  color: #fff;
  box-shadow: var(--shadow-accent);
}

.btn-primary:hover {
  box-shadow: var(--shadow-card-hover);
  filter: brightness(1.1);
}
```

#### Acción Neutral (Cancelar, Cerrar)
```css
.btn-secondary {
  background: var(--gradient-card);
  border: 2px solid var(--color-border-strong);
  color: var(--color-text);
}
```

#### Acción Destructiva (Eliminar, Limpiar)
```css
.btn-danger {
  background: transparent;
  border: 2px solid var(--color-danger);
  color: var(--color-danger);
}

.btn-danger:hover {
  background: var(--color-danger-bg);
}
```

---

### Datos Monetarios

#### Totales y Montos
```css
.price,
.total,
.amount {
  color: var(--color-accent);
  font-weight: 700;
  text-shadow: var(--shadow-accent);
}
```

#### Secciones de Total
```css
.total-section {
  background: var(--color-accent-soft);
  border: 2px solid var(--color-accent);
}
```

---

### Formularios e Inputs

#### Estado Normal
```css
.input {
  background: var(--color-bg);
  border: 2px solid var(--color-border-strong);
  color: var(--color-text);
}
```

#### Estado Focus
```css
.input:focus {
  border-color: var(--color-accent);
  box-shadow: var(--shadow-accent);
}
```

#### Estado Error
```css
.input.error {
  border-color: var(--color-danger);
  box-shadow: 0 0 15px var(--color-danger-bg);
}
```

---

### Modales y Overlays

#### Overlay
```css
.modal-overlay {
  background: var(--color-overlay);
  backdrop-filter: blur(6px);
}
```

#### Container Modal
```css
.modal {
  background: var(--gradient-card);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-card-hover);
}
```

---

## ✅ Mejores Prácticas

### 1. Jerarquía Visual

```css
/* Títulos principales */
h1 {
  color: var(--color-text);
  text-shadow: var(--shadow-accent);
}

/* Subtítulos */
h2, h3 {
  color: var(--color-text);
}

/* Texto cuerpo */
p, span {
  color: var(--color-text);
}

/* Texto secundario */
.secondary {
  color: var(--color-text-muted);
}
```

---

### 2. Contraste y Legibilidad

#### Mínimos Recomendados
- Texto primario sobre fondo: ratio 7:1 (AAA)
- Elementos interactivos: ratio 4.5:1 (AA)
- Elementos grandes: ratio 3:1 (AA)

#### Testing dual-mode
```css
/* ✅ Bueno — Alto contraste en ambos modos */
color: var(--color-text);     /* #f5f5f5 sobre #0d0d0d | #111827 sobre #f7f8fa */
color: var(--color-accent);   /* #22c55e sobre #0d0d0d | #16a34a sobre #f7f8fa */

/* ⚠️ Evitar — Bajo contraste */
color: var(--color-border);   /* demasiado tenue para texto legible */
```

> **Tip**: Verificar contraste en **ambos modos** antes de hacer merge. Usar [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/).

---

### 3. Estados Interactivos

```css
/* Hover — Aumentar brillo + micro-animación */
.element:hover {
  background: var(--color-hover);
  box-shadow: var(--shadow-accent);
  transform: translateY(-2px);
}

/* Active */
.element:active {
  transform: translateY(0);
}

/* Focus — Visible para navegación por teclado */
.element:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* Disabled */
.element:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(50%);
}
```

---

### 4. Animaciones y Transiciones

```css
/* Suave y rápida (200-300ms) */
transition: all 0.2s ease;

/* Media (300-500ms) para hover */
transition: all 0.3s ease;

/* Lenta (500ms+) solo para grandes cambios */
transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
```

---

## 📦 Casos de Uso Específicos

### Página de Ventas

```css
.sales-header {
  border-bottom: 3px solid var(--color-accent-soft);
}

.sales-table {
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.sales-table-header {
  background: var(--color-bg-2);
  color: var(--color-accent);
  border-bottom: 2px solid var(--color-accent-soft);
}

.sales-row:hover {
  background: var(--color-accent-soft);
  border-left: 3px solid var(--color-accent);
}

.sales-total {
  color: var(--color-accent);
  text-shadow: var(--shadow-accent);
}

.btn-delete {
  color: var(--color-danger);
  border: 2px solid var(--color-danger-bg);
}
```

---

### Filtros de Búsqueda

```css
.filters {
  border: 2px solid var(--color-border);
  background: var(--color-surface);
}

.filter-input {
  background: var(--color-bg);
  border: 2px solid var(--color-border-strong);
  color: var(--color-text);
}

.filter-input:focus {
  border-color: var(--color-accent);
  box-shadow: var(--shadow-accent);
}

/* Botón buscar — acción positiva */
.btn-search {
  background: var(--gradient-accent);
}

/* Botón limpiar — acción destructiva menor */
.btn-clear {
  border: 2px solid var(--color-danger);
  color: var(--color-danger);
}
```

---

### Modal de Detalles

```css
.modal-overlay {
  background: var(--color-overlay);
  backdrop-filter: blur(6px);
}

.modal-content {
  background: var(--gradient-card);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-card-hover);
}

.modal-header {
  border-bottom: 2px solid var(--color-accent-soft);
}

.modal-title {
  color: var(--color-text);
  text-shadow: var(--shadow-accent);
}

/* Botón cerrar — neutral, hover rojo */
.modal-close {
  color: var(--color-text-muted);
}

.modal-close:hover {
  color: var(--color-danger);
  background: var(--color-danger-bg);
}

/* Scrollbar */
::-webkit-scrollbar-thumb {
  background: var(--color-accent);
}

/* Sección total */
.total-section {
  background: var(--color-accent-soft);
  border: 2px solid var(--color-accent);
}

.total-value {
  color: var(--color-accent);
  text-shadow: var(--shadow-accent);
}
```

---

## 📊 Paleta de Gráficos (Charts)

Los gráficos del Dashboard y Reports utilizan una paleta de 8 colores fijos. Estos valores se usan en componentes como `ExpenseByCategoryChart`, `SalesByCategoryChart`, `MonthlyBalanceBarChart`, y `NetMarginLineChart`.

| Índice | Color | Hex | Uso típico |
|---|---|---|---|
| 1 | 🔴 Rojo | `#ef4444` | Gastos, pérdidas |
| 2 | 🟡 Ámbar | `#f59e0b` | Advertencias, segunda categoría |
| 3 | 🟢 Verde | `#22c55e` | Ingresos, ganancias |
| 4 | 🔵 Azul | `#3b82f6` | Categoría neutra |
| 5 | 🟣 Violeta | `#8b5cf6` | Categoría adicional |
| 6 | 🩷 Rosa | `#ec4899` | Categoría adicional |
| 7 | 🩵 Cian | `#06b6d4` | Categoría adicional |
| 8 | 🌿 Teal | `#14b8a6` | Categoría adicional |

### Colores semánticos en charts

| Contexto | Color | Variable sugerida |
|---|---|---|
| Ganancias / superávit | `#16a34a` | `--color-accent-strong` |
| Pérdidas / déficit | `#ef4444` | `--color-danger` |

> **Nota**: Estos colores de charts actualmente están hardcodeados en los componentes. Ver sección [Migración Pendiente](#migración-pendiente-de-hardcodeados) para el plan de refactorización.

---

## 🚨 Errores Comunes a Evitar

### ❌ Hex hardcodeados en lugar de variables
```css
/* MAL — Solo funciona en dark mode */
.card { background: #1a1a1a; color: #f5f5f5; }

/* BIEN — Funciona en ambos modos */
.card { background: var(--color-bg-2); color: var(--color-text); }
```

### ❌ Rojo excesivo
```css
/* MAL — Rojo en elementos no críticos */
.table { border: 2px solid #ff3b3b; }
.header { background: linear-gradient(#ff3b3b, #cc2f2f); }

/* BIEN — Rojo solo para acciones destructivas */
.btn-delete { color: var(--color-danger); }
```

### ❌ Bajo contraste
```css
/* MAL — Difícil de leer en ambos modos */
.text { color: var(--color-border); }

/* BIEN — Usa text-muted para texto secundario */
.text { color: var(--color-text-muted); }
```

### ❌ Verde neón excesivo
```css
/* MAL — Demasiado brillante */
.text { color: #6dff7a; }
.background { background: #00ff00; }

/* BIEN — Usar la variable de acento */
.text { color: var(--color-accent); }
```

### ❌ No testear en ambos modos
```css
/* MAL — rgba con blanco, invisible en light mode */
.label { color: rgba(255, 255, 255, 0.6); }

/* BIEN — La variable se adapta automáticamente */
.label { color: var(--color-text-muted); }
```

### ❌ Falta de jerarquía
```css
/* MAL — Todo el mismo peso visual */
h1, h2, h3, p { color: var(--color-text); font-weight: 700; }
```

---

## 📱 Responsive y Accesibilidad

### Touch Targets
```css
.btn {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
}
```

### Focus Visible
```css
*:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

### Reducir Movimiento
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

---

## 🔄 Migración Pendiente de Hardcodeados

Los siguientes archivos contienen colores hex/rgba en línea que deberían migrarse a variables CSS para asegurar compatibilidad dual-theme.

### Variables nuevas propuestas

Agregar a `theme.css` antes de migrar:

```css
/* ── theme.css ── */

/* :root (dark) */
--color-warning: #ffc107;
--color-warning-bg: rgba(255, 193, 7, 0.15);

/* [data-theme="light"] */
--color-warning: #d97706;
--color-warning-bg: rgba(217, 119, 6, 0.12);
```

### Tabla de migración

| Archivo | Color actual | Reemplazar por |
|---|---|---|
| `ProductCard.tsx` | `#999` | `var(--color-text-muted)` |
| `ProductCard.tsx` | `#aaa` | `var(--color-text-muted)` |
| `ProductCard.tsx` | `#ffc107` | `var(--color-warning)` |
| `ProductCard.tsx` | `rgba(255,193,7, 0.15)` | `var(--color-warning-bg)` |
| `ProductCard.tsx` | `rgba(255,193,7, 0.4)` | `var(--color-warning)` (border) |
| `ProductCard.tsx` | `#ffffff` | `var(--color-text)` |
| `ProductosCategoryConfigModal.tsx` | `#aaa` | `var(--color-text-muted)` |
| `ProductosCategoryConfigModal.tsx` | `#ffc107` | `var(--color-warning)` |
| `ProductosCategoryConfigModal.tsx` | `rgba(255,193,7, 0.15)` | `var(--color-warning-bg)` |
| `ProductosCategoryConfigModal.tsx` | `rgba(255,193,7, 0.4)` | `var(--color-warning)` (border) |
| `SaleDetailModal.tsx` | `rgba(255,255,255, 0.6)` | `var(--color-text-muted)` |
| `SaleDetailModal.tsx` | `rgba(255,255,255, 0.75)` | `var(--color-text)` |
| `SaleEditModal.tsx` | `rgba(255,255,255, 0.6)` | `var(--color-text-muted)` |
| `SaleEditModal.tsx` | `rgba(255,255,255, 0.75)` | `var(--color-text)` |
| `UserManagementPage.tsx` | `#16a34a` | `var(--color-accent-strong)` |
| `UserManagementPage.tsx` | `#ef4444` | `var(--color-danger)` |
| `UserManagementPage.tsx` | `#ffffff` | `var(--color-text)` |
| `AuditPage.tsx` | `#ef4444` | `var(--color-danger)` |
| `CartDrawer.tsx` | `rgba(255,255,255, 0.3)` | `var(--color-text-muted)` |
| `ExpenseByCategoryChart.tsx` | Paleta 8 colores | Variables `--chart-color-1..8` |
| `SalesByCategoryChart.tsx` | Paleta 8 colores | Variables `--chart-color-1..8` |
| `MonthlyBalanceBarChart.tsx` | `#16a34a`, `#ef4444` | `--color-accent-strong`, `--color-danger` |
| `NetMarginLineChart.tsx` | `#16a34a` | `var(--color-accent-strong)` |

> **Nota**: La animación "Italian Flag" en `auth.css` y `home.css` usa colores hardcodeados intencionales (verde, blanco, rojo del tricolor italiano). Esos **no** necesitan migración.

---

## 🎓 Recursos Adicionales

### Herramientas
- **Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Color Palette Generator**: https://coolors.co/
- **Gradient Generator**: https://cssgradient.io/

### Referencias
- WCAG 2.1 Guidelines (AA/AAA)
- Material Design Dark Theme
- Apple Human Interface Guidelines

---

## 📝 Checklist de Revisión

Antes de implementar cambios de color:

- [ ] ¿Se usan **variables CSS** (`var(--color-*)`) en vez de hex hardcodeados?
- [ ] ¿El rojo (`--color-danger`) está solo en acciones críticas?
- [ ] ¿Los totales/dinero usan `--color-accent` (verde)?
- [ ] ¿El contraste cumple WCAG AA (mínimo) en **ambos modos**?
- [ ] ¿Los estados hover son claros?
- [ ] ¿Los estados focus son visibles (`:focus-visible`)?
- [ ] ¿La jerarquía visual es clara (text vs text-muted)?
- [ ] ¿Se aplicó la regla 60/30/10?
- [ ] ¿Los bordes son sutiles y no saturan?
- [ ] ¿Las animaciones son suaves (200-300ms)?
- [ ] ¿Se testeó en **Dark Mode** y **Light Mode**?
- [ ] ¿Los gráficos son legibles en ambos modos?
- [ ] ¿Funciona bien en móvil?

---

**Última actualización**: Marzo 2026
**Autor**: UX/UI Designer Senior — PizzaFiori Internal System

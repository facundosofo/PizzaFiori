# 🎨 Guía de UX/UI - Sistema de Colores Dark Mode

## 📋 Índice
1. [Filosofía de Color](#filosofía-de-color)
2. [Paleta de Colores](#paleta-de-colores)
3. [Regla 60/30/10](#regla-603010)
4. [Uso de Colores por Contexto](#uso-de-colores-por-contexto)
5. [Mejores Prácticas](#mejores-prácticas)
6. [Casos de Uso Específicos](#casos-de-uso-específicos)

---

## 🎯 Filosofía de Color

### Principios Fundamentales

**ROJO** → Acciones críticas y destructivas
- Eliminar registros
- Errores graves
- Alertas de peligro
- Limpiar/resetear datos

**VERDE** → Dinero, éxito y estados positivos
- Totales monetarios
- Confirmaciones
- Estados completados
- Acciones de avance/búsqueda

**BLANCO/GRIS** → Legibilidad y jerarquía
- Textos principales
- Bordes neutros
- Fondos base
- Estados inactivos

---

## 🎨 Paleta de Colores

### Verde (Primario - Dinero/Éxito)
```css
/* Verde principal */
#22c55e - Color base para dinero y estados positivos

/* Verde brillante */
#4ade80 - Hover states, highlights

/* Verde oscuro */
#16a34a - Gradientes, estados activos
```

### Rojo (Destructivo - Solo crítico)
```css
/* Rojo principal */
#ef4444 - Acciones destructivas

/* Rojo brillante */
#ff5252 - Estados de error severo

/* Rojo oscuro */
#dc2626 - Gradientes de advertencia
```

### Neutrales (Base - 60% del diseño)
```css
/* Fondos */
#0d0d0d - Fondo oscuro principal
#1a1a1a - Fondo secundario
#2a2a2a - Elementos elevados

/* Textos */
#ffffff - Títulos principales
#f5f5f5 - Textos importantes
#e8e8e8 - Textos secundarios
#888888 - Textos deshabilitados

/* Bordes */
rgba(255, 255, 255, 0.15) - Bordes principales
rgba(255, 255, 255, 0.1) - Bordes sutiles
rgba(255, 255, 255, 0.05) - Separadores
```

---

## 📐 Regla 60/30/10

### Distribución Visual

**60% - Neutrales**
- Fondos principales
- Contenedores
- Textos base
- Espaciado y estructura

**30% - Blanco/Gris claro**
- Textos principales
- Iconos
- Elementos de UI
- Bordes y separadores

**10% - Verde + Rojo (acentos)**
- Verde: 8% (dinero, éxito, acciones positivas)
- Rojo: 2% (solo acciones críticas)

### Ejemplo Visual
```
┌─────────────────────────────────────┐
│ [60%] Fondo oscuro #0d0d0d         │
│                                     │
│ [30%] Texto blanco #f5f5f5         │
│ [30%] Bordes grises rgba(...)      │
│                                     │
│ [8%] Total: $1,234.56 (verde)      │
│ [2%] [Eliminar] (rojo)             │
└─────────────────────────────────────┘
```

---

## 🎯 Uso de Colores por Contexto

### Tablas y Listados

#### Headers
```css
/* ✅ CORRECTO - Verde con fondo oscuro */
background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
color: #22c55e;
border-bottom: 2px solid rgba(74, 222, 128, 0.3);
```

```css
/* ❌ INCORRECTO - Fondo rojo saturado */
background: linear-gradient(135deg, #ff3b3b 0%, #cc2f2f 100%);
```

#### Filas
```css
/* ✅ CORRECTO - Hover verde sutil */
.row:hover {
  background: rgba(74, 222, 128, 0.08);
  border-left: 3px solid #22c55e;
}
```

```css
/* ❌ INCORRECTO - Hover rojo */
.row:hover {
  background: rgba(255, 59, 59, 0.1);
}
```

#### Bordes
```css
/* ✅ CORRECTO - Neutro con acento verde */
border: 2px solid rgba(255, 255, 255, 0.15);
box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.1);
```

```css
/* ❌ INCORRECTO - Borde rojo dominante */
border: 2px solid #ff3b3b;
```

---

### Botones y Acciones

#### Acción Positiva (Buscar, Guardar, Continuar)
```css
/* ✅ Verde para acciones positivas */
.btn-primary {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: 2px solid #4ade80;
  color: #fff;
}

.btn-primary:hover {
  box-shadow: 0 0 25px rgba(34, 197, 94, 0.5);
}
```

#### Acción Neutral (Cancelar, Cerrar)
```css
/* ✅ Gris para acciones neutrales */
.btn-secondary {
  background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 100%);
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: #f5f5f5;
}
```

#### Acción Destructiva (Eliminar, Limpiar)
```css
/* ✅ Rojo solo para acciones críticas */
.btn-danger {
  background: transparent;
  border: 2px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
}
```

---

### Datos Monetarios

#### Totales y Montos
```css
/* ✅ Siempre verde con sombra */
.price,
.total,
.amount {
  color: #22c55e;
  font-weight: 700;
  text-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}
```

#### Secciones de Total
```css
/* ✅ Container verde destacado */
.total-section {
  background: linear-gradient(180deg, 
    rgba(34, 197, 94, 0.1) 0%, 
    rgba(34, 197, 94, 0.05) 100%);
  border: 2px solid #22c55e;
}
```

---

### Formularios e Inputs

#### Estado Normal
```css
/* ✅ Bordes neutros */
.input {
  background: #0d0d0d;
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: #f5f5f5;
}
```

#### Estado Focus
```css
/* ✅ Focus verde para positivo */
.input:focus {
  border-color: #22c55e;
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
}
```

#### Estado Error
```css
/* ✅ Error rojo justificado */
.input.error {
  border-color: #ef4444;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
}
```

---

### Modales y Overlays

#### Overlay
```css
/* ✅ Negro puro con blur */
.modal-overlay {
  background: rgba(0, 0, 0, 0.92);
  backdrop-filter: blur(6px);
}
```

```css
/* ❌ Evitar overlay con tinte rojo */
background: rgba(0, 0, 0, 0.85);
backdrop-filter: blur(4px); /* con tinte rojo */
```

#### Container Modal
```css
/* ✅ Borde neutro con acento verde */
.modal {
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    0 10px 50px rgba(0, 0, 0, 0.8),
    0 0 0 1px rgba(74, 222, 128, 0.2);
}
```

---

## ✅ Mejores Prácticas

### 1. Jerarquía Visual

**Títulos Principales**
```css
h1 {
  color: #ffffff;
  text-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
}
```

**Subtítulos**
```css
h2, h3 {
  color: #f5f5f5;
}
```

**Texto Cuerpo**
```css
p, span {
  color: #e8e8e8;
}
```

**Texto Secundario**
```css
.secondary {
  color: rgba(255, 255, 255, 0.6);
}
```

---

### 2. Contraste y Legibilidad

#### Mínimos Recomendados
- Texto sobre fondo oscuro: ratio 7:1 (AAA)
- Elementos interactivos: ratio 4.5:1 (AA)
- Elementos grandes: ratio 3:1 (AA)

#### Testing
```css
/* Usar herramientas de contraste */
/* https://webaim.org/resources/contrastchecker/ */

/* ✅ Bueno */
color: #ffffff; /* sobre #0d0d0d */
color: #22c55e; /* sobre #0d0d0d */

/* ⚠️ Evitar */
color: rgba(255, 255, 255, 0.3); /* muy bajo contraste */
```

---

### 3. Estados Interactivos

#### Hover
```css
/* Aumentar brillo 10-20% */
/* Agregar sombra sutil */
/* Micro-animación (transform) */

.element:hover {
  filter: brightness(1.15);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
  transform: translateY(-2px);
}
```

#### Active
```css
/* Reducir desplazamiento */
.element:active {
  transform: translateY(0);
}
```

#### Focus
```css
/* Borde visible + outline */
.element:focus {
  outline: 2px solid #22c55e;
  outline-offset: 2px;
}
```

#### Disabled
```css
/* Reducir opacidad + cursor */
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

#### ✅ Implementación Correcta
```css
/* Header */
.sales-header {
  border-bottom: 3px solid rgba(74, 222, 128, 0.4);
}

/* Tabla */
.sales-table {
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.1);
}

/* Header tabla */
.sales-table-header {
  background: #1a1a1a;
  color: #22c55e;
  border-bottom: 2px solid rgba(74, 222, 128, 0.3);
}

/* Hover fila */
.sales-row:hover {
  background: rgba(74, 222, 128, 0.08);
  border-left: 3px solid #22c55e;
}

/* Total */
.sales-total {
  color: #22c55e;
  text-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}

/* Botón eliminar */
.btn-delete {
  color: #ef4444;
  border: 2px solid rgba(239, 68, 68, 0.3);
}
```

---

### Filtros de Búsqueda

```css
/* Container */
.filters {
  border: 2px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.1);
}

/* Inputs */
.filter-input {
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.filter-input:focus {
  border-color: #22c55e;
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
}

/* Botón buscar (verde - acción positiva) */
.btn-search {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

/* Botón limpiar (rojo - acción destructiva menor) */
.btn-clear {
  border: 2px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
}
```

---

### Modal de Detalles

```css
/* Overlay */
.modal-overlay {
  background: rgba(0, 0, 0, 0.92);
  backdrop-filter: blur(6px);
}

/* Container */
.modal-content {
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    0 10px 50px rgba(0, 0, 0, 0.8),
    0 0 0 1px rgba(74, 222, 128, 0.2);
}

/* Header */
.modal-header {
  border-bottom: 2px solid rgba(74, 222, 128, 0.3);
}

.modal-title {
  color: #ffffff;
  text-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
}

/* Botón cerrar (neutral, hover rojo) */
.modal-close {
  color: rgba(255, 255, 255, 0.7);
}

.modal-close:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.2);
}

/* Scrollbar */
::-webkit-scrollbar-thumb {
  background: #22c55e;
}

/* Sección total */
.total-section {
  background: linear-gradient(180deg, 
    rgba(34, 197, 94, 0.1) 0%, 
    rgba(34, 197, 94, 0.05) 100%);
  border: 2px solid #22c55e;
}

.total-value {
  color: #22c55e;
  text-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
}
```

---

## 🚨 Errores Comunes a Evitar

### ❌ Rojo Excesivo
```css
/* MAL - Rojo en elementos no críticos */
.table { border: 2px solid #ff3b3b; }
.header { background: linear-gradient(#ff3b3b, #cc2f2f); }
.row:hover { background: rgba(255, 59, 59, 0.1); }
```

### ❌ Bajo Contraste
```css
/* MAL - Difícil de leer */
.text { color: rgba(255, 255, 255, 0.3); }
.label { color: #666; }
```

### ❌ Verde Neón Excesivo
```css
/* MAL - Demasiado brillante */
.text { color: #6dff7a; } /* usar #22c55e */
.background { background: #00ff00; } /* demasiado saturado */
```

### ❌ Falta de Jerarquía
```css
/* MAL - Todo el mismo peso visual */
h1, h2, h3, p { color: #fff; font-weight: 700; }
```

---

## 📱 Responsive y Accesibilidad

### Touch Targets
```css
/* Mínimo 44x44px en móvil */
.btn {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
}
```

### Focus Visible
```css
/* Siempre visible para teclado */
*:focus-visible {
  outline: 2px solid #22c55e;
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

- [ ] ¿El rojo está solo en acciones críticas?
- [ ] ¿Los totales/dinero están en verde?
- [ ] ¿El contraste cumple WCAG AA (mínimo)?
- [ ] ¿Los estados hover son claros?
- [ ] ¿Los estados focus son visibles?
- [ ] ¿La jerarquía visual es clara?
- [ ] ¿Se aplicó la regla 60/30/10?
- [ ] ¿Los bordes son sutiles y no saturan?
- [ ] ¿Las animaciones son suaves (200-300ms)?
- [ ] ¿Funciona bien en móvil?

---

**Última actualización**: Enero 2026  
**Autor**: UX/UI Designer Senior - PizzaFiori Internal System

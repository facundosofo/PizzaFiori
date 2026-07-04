# Plan De Aislamiento CSS (Frontend)

Fecha: 2026-07-02

## Objetivo
Evitar regresiones visuales por colisiones de clases CSS entre pantallas cuando las rutas se cargan en forma lazy.

## Causa Raiz
Hay componentes que usan clases genericas compartidas (por ejemplo: action-buttons, btn-action, empty-state) con definiciones distintas en varias hojas CSS.

Con lazy loading de paginas, el orden y momento de carga del CSS cambia segun la ruta navegada. Eso expone dependencias ocultas entre estilos de distintos modulos.

## Hallazgos Relevantes
### Clases de mayor riesgo
- action-buttons
- btn-action
- empty-state
- modal-overlay
- modal-content
- modal-close

### Hotspots actuales (prioridad)
1. ExpenseCategoryConfigModal
- Componente: frontend/src/components/ExpenseCategoryConfigModal.tsx
- CSS asociado: frontend/src/styles/expense-category-config-modal.css
- Riesgo: usa btn-action y empty-state, nombres compartidos con otras pantallas.

2. UserManagement
- CSS: frontend/src/styles/user-management.css
- Riesgo: define action-buttons y btn-action en forma global.

3. Expenses y ExpenseCategories
- CSS: frontend/src/styles/expenses.css
- CSS: frontend/src/styles/expense-categories.css
- Riesgo: redefinen action-buttons, btn-action y empty-state.

4. OfferModal (riesgo medio)
- Componente: frontend/src/components/OfferModal.tsx
- CSS: frontend/src/styles/offer-modal.css
- Riesgo: usa modal-overlay/modal-content/modal-close (nombres muy genericos).

## Solucion Tecnica Recomendada
1. Prefijar clases por componente/feature.
- Ejemplos:
  - exp-cat-config-btn-action
  - exp-cat-config-empty-state
  - offer-modal-overlay

2. Evitar depender de clases definidas en otras pantallas.
- Cada componente debe tener sus propias clases y estilos.

3. Si se conserva CSS global, acotar selectores por contenedor de pagina.
- Ejemplo: .user-management-container .btn-action

## Plan De Trabajo (Fases)
### Fase 1 (alta prioridad)
- Aislar ExpenseCategoryConfigModal
- Verificar que no cambie el look actual
- Revisar iconos en botones de accion

### Fase 2
- Aislar UserManagement, Expenses y ExpenseCategories
- Eliminar uso transversal de action-buttons y btn-action

### Fase 3
- Revisar modales con nombres genericos (modal-overlay/modal-content/modal-close)
- Prefijar por componente

## Checklist De PR (obligatorio)
- No introducir clases genericas compartidas
- Prefijo por componente en clases nuevas
- No depender de estilos de otra ruta/pantalla
- Probar navegacion cruzada: abrir ruta A, luego B, volver a A
- Probar recarga dura del navegador

## Guardrail Recomendado
Agregar validacion automatica en CI o pre-commit para bloquear nuevas clases genericas.

Opciones:
- Regla simple por busqueda de patrones prohibidos
- Stylelint con convencion de naming (prefijos por dominio)

## Nota Operativa
En este entorno no estaba disponible rg en PowerShell. Para auditorias futuras, usar alternativa con Select-String o la busqueda integrada de VS Code.

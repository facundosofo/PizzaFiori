import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { createPortal } from "react-dom";
import { ArrowDownWideNarrow } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { formatLocalISO } from "../utils/formatters";
import { getProductos, reorderProductos } from "../services/productsService";
import { getProductosCategorias } from "../services/productosCategoriasService";
import ProductCard from "../components/ProductCard";
import ProductModal from "../components/ProductModal";
import ProductosCategoryConfigModal from "../components/ProductosCategoryConfigModal";
import BulkPriceUpdateModal from "../components/BulkPriceUpdateModal";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import "../styles/product-card.css";

const ProductosPage = () => {
  type ProductDragOverlay = {
    left: number;
    top: number;
    width: number;
    height: number;
    clone: HTMLDivElement;
  };

  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [productos, setProductos] = useState<Product[]>([]);
  const [categorias, setCategorias] = useState<ProductoCategoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [newProduct, setNewProduct] = useState<Product | null>(null);
  const [showCategoryConfig, setShowCategoryConfig] = useState(false);
  const [showBulkPriceModal, setShowBulkPriceModal] = useState(false);
  const [orderingCategoryId, setOrderingCategoryId] = useState<number | null>(null);
  const [draggedProductId, setDraggedProductId] = useState<number | null>(null);
  const [productDragOverlay, setProductDragOverlay] = useState<ProductDragOverlay | null>(null);
  const [isSavingOrder, setIsSavingOrder] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);
  const productOrderBeforeDrag = useRef<Product[] | null>(null);
  const productOrderPreview = useRef<Product[]>([]);
  const draggedProductIdRef = useRef<number | null>(null);
  const productDragOverlayRef = useRef<HTMLDivElement | null>(null);
  const productDragScrollContainerRef = useRef<HTMLDivElement | null>(null);
  const productDragPointerRef = useRef({ x: 0, y: 0 });
  const productDragStartPointerRef = useRef({ x: 0, y: 0 });
  const productDragGrabOffsetXRef = useRef(0);
  const productDragInsertionPointsRef = useRef<Map<number, number>>(new Map());
  const productDragSlotPositionsRef = useRef<Array<{ left: number; top: number }>>([]);
  const productDragPointerIdRef = useRef<number | null>(null);
  const productDragFrameRef = useRef<number | null>(null);
  const productDragListenersRef = useRef<{
    onMove: (event: PointerEvent) => void;
    onUp: (event: PointerEvent) => void;
    onCancel: (event: PointerEvent) => void;
  } | null>(null);
  const productDragScrollBehaviorRef = useRef("");

  useLayoutEffect(() => {
    if (!productDragOverlay || !productDragOverlayRef.current) return;
    productDragOverlayRef.current.replaceChildren(productDragOverlay.clone);
    return () => productDragOverlay.clone.remove();
  }, [productDragOverlay]);

  useEffect(() => () => {
    const listeners = productDragListenersRef.current;
    if (listeners) {
      window.removeEventListener("pointermove", listeners.onMove);
      window.removeEventListener("pointerup", listeners.onUp);
      window.removeEventListener("pointercancel", listeners.onCancel);
    }
    if (productDragFrameRef.current !== null) {
      cancelAnimationFrame(productDragFrameRef.current);
    }
    const scrollContainer = productDragScrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.style.scrollBehavior = productDragScrollBehaviorRef.current;
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [prods, cats] = await Promise.all([
          getProductos(),
          getProductosCategorias(true),
        ]);

        if (!prods || prods.length === 0) {
          setError("No se pudieron cargar los productos. Intenta recargar la página.");
        }
        if (!cats || cats.length === 0) {
          setError("No se pudieron cargar las categorías. Intenta recargar la página.");
        }

        setProductos(prods || []);
        setCategorias(cats || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido al cargar los datos";
        setError(`Error al cargar: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleProductUpdate = (updatedProducto: Product) => {
    setProductos((prevProductos) => {
      const updated = prevProductos.map((p) => (p.id === updatedProducto.id ? updatedProducto : p));
      return updated;
    });
  };

  const handleBulkPriceSuccess = (updatedProducts: Product[]) => {
    setProductos((prevProductos) => {
      let updated = [...prevProductos];
      for (const prod of updatedProducts) {
        updated = updated.map((p) => (p.id === prod.id ? prod : p));
      }
      return updated;
    });
  };

  const handleProductDelete = (productoId: number) => {
    setProductos((prevProductos) => {
      const filtered = prevProductos.filter((p) => p.id !== productoId);
      return filtered;
    });
  };

  const handleCreateClick = () => {
    setNewProduct({
      id: 0,
      sku: "",
      nombre: "",
      categoria_id: 0,
      orden: 0,
      imagen: undefined,
      activo: true,
      fecha_creacion: formatLocalISO(new Date()),
      fecha_actualizacion: formatLocalISO(new Date()),
      precios: [],
    });
    setIsCreating(true);
  };

  const handleCreateProduct = async (producto: Product) => {
    setProductos((prev) => {
      const updated = [...prev, producto];
      return updated;
    });
    
    setCollapsedCategories((prev) => {
      const newSet = new Set(prev);
      if (producto.categoria_id) {
        newSet.delete(producto.categoria_id);
      }
      return newSet;
    });
    
    setIsCreating(false);
    setNewProduct(null);
  };

  const toggleCategoryCollapse = (categoryId: number) => {
    setCollapsedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const applyCategoryProductOrder = (baseProducts: Product[], orderedCategoryProducts: Product[]) => {
    const orderById = new Map(
      orderedCategoryProducts.map((producto, orden) => [producto.id, orden]),
    );
    return baseProducts.map((producto) => {
      const orden = orderById.get(producto.id);
      return orden === undefined ? producto : { ...producto, orden };
    });
  };

  const previewProductPosition = (pointerX: number) => {
    const sourceProductId = draggedProductIdRef.current;
    const initialOrder = productOrderPreview.current;
    const scrollContainer = productDragScrollContainerRef.current;
    if (sourceProductId === null || initialOrder.length === 0 || !scrollContainer) return;

    const draggedProduct = initialOrder.find((producto) => producto.id === sourceProductId);
    if (!draggedProduct) return;
    const remainingProducts = initialOrder.filter((producto) => producto.id !== sourceProductId);
    const containerBounds = scrollContainer.getBoundingClientRect();
    const pointerContentX =
      pointerX +
      productDragGrabOffsetXRef.current -
      containerBounds.left +
      scrollContainer.scrollLeft;
    const insertionIndex = remainingProducts.findIndex((producto) => {
      const center = productDragInsertionPointsRef.current.get(producto.id);
      return center !== undefined && pointerContentX < center;
    });
    const targetIndex = insertionIndex === -1 ? remainingProducts.length : insertionIndex;
    const nextOrder = [...remainingProducts];
    nextOrder.splice(targetIndex, 0, draggedProduct);

    if (nextOrder.some((producto, index) => producto.id !== initialOrder[index]?.id)) {
      productOrderPreview.current = nextOrder;
      const previousProducts = productOrderBeforeDrag.current;
      if (previousProducts) {
        setProductos(applyCategoryProductOrder(previousProducts, nextOrder));
      }
    }
  };

  const updateProductDragPreview = (x: number, y: number) => {
    const overlay = productDragOverlayRef.current;
    if (overlay) {
      const { x: startX, y: startY } = productDragStartPointerRef.current;
      overlay.style.transform = `translate3d(${x - startX}px, ${y - startY}px, 0)`;
    }
    previewProductPosition(x);
  };

  const scheduleProductDragFrame = () => {
    if (productDragFrameRef.current !== null) return;
    productDragFrameRef.current = requestAnimationFrame(() => {
      productDragFrameRef.current = null;
      const { x, y } = productDragPointerRef.current;
      updateProductDragPreview(x, y);

      const scrollContainer = productDragScrollContainerRef.current;
      if (!scrollContainer) return;
      const bounds = scrollContainer.getBoundingClientRect();
      const edgeSize = 56;
      const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;
      let scrollDelta = 0;

      if (
        y >= bounds.top - edgeSize &&
        y <= bounds.bottom + edgeSize &&
        x >= bounds.left - edgeSize &&
        x < bounds.left + edgeSize &&
        scrollContainer.scrollLeft > 0
      ) {
        const strength = Math.min(1, (bounds.left + edgeSize - x) / edgeSize);
        scrollDelta = -Math.max(1, Math.ceil(strength * 8));
      } else if (
        y >= bounds.top - edgeSize &&
        y <= bounds.bottom + edgeSize &&
        x > bounds.right - edgeSize &&
        x <= bounds.right + edgeSize &&
        scrollContainer.scrollLeft < maxScrollLeft
      ) {
        const strength = Math.min(1, (x - (bounds.right - edgeSize)) / edgeSize);
        scrollDelta = Math.max(1, Math.ceil(strength * 8));
      }

      if (scrollDelta !== 0) {
        scrollContainer.scrollLeft = Math.max(
          0,
          Math.min(maxScrollLeft, scrollContainer.scrollLeft + scrollDelta),
        );
        updateProductDragPreview(x, y);
        scheduleProductDragFrame();
      }
    });
  };

  const handleProductPointerMove = (event: PointerEvent) => {
    if (
      event.pointerId !== productDragPointerIdRef.current ||
      !productDragOverlayRef.current ||
      draggedProductIdRef.current === null
    ) return;
    productDragPointerRef.current = { x: event.clientX, y: event.clientY };
    scheduleProductDragFrame();
  };

  const removeProductDragListeners = () => {
    const listeners = productDragListenersRef.current;
    if (!listeners) return;
    window.removeEventListener("pointermove", listeners.onMove);
    window.removeEventListener("pointerup", listeners.onUp);
    window.removeEventListener("pointercancel", listeners.onCancel);
    productDragListenersRef.current = null;
  };

  const stopProductDragFrame = () => {
    if (productDragFrameRef.current === null) return;
    cancelAnimationFrame(productDragFrameRef.current);
    productDragFrameRef.current = null;
  };

  const finishProductDrag = () => {
    const scrollContainer = productDragScrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.style.scrollBehavior = productDragScrollBehaviorRef.current;
    }
    draggedProductIdRef.current = null;
    productDragPointerIdRef.current = null;
    setDraggedProductId(null);
    setProductDragOverlay(null);
    productDragInsertionPointsRef.current.clear();
    productDragSlotPositionsRef.current = [];
    productOrderBeforeDrag.current = null;
    productOrderPreview.current = [];
  };

  const handleProductPointerCancel = (event: PointerEvent) => {
    if (event.pointerId !== productDragPointerIdRef.current) return;
    removeProductDragListeners();
    stopProductDragFrame();
    const previousProducts = productOrderBeforeDrag.current;
    if (previousProducts) setProductos(previousProducts);
    finishProductDrag();
  };

  const settleProductDragOverlay = (productId: number, nextOrder: Product[]) =>
    new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const overlay = productDragOverlayRef.current;
          const scrollContainer = productDragScrollContainerRef.current;
          const targetIndex = nextOrder.findIndex((producto) => producto.id === productId);
          const slot = productDragSlotPositionsRef.current[targetIndex];
          if (!overlay || !scrollContainer || !slot) {
            resolve();
            return;
          }

          const currentRect = overlay.getBoundingClientRect();
          const containerRect = scrollContainer.getBoundingClientRect();
          const targetLeft = containerRect.left + slot.left - scrollContainer.scrollLeft;
          const targetTop = containerRect.top + slot.top;
          overlay.style.transition = "none";
          overlay.style.left = `${currentRect.left}px`;
          overlay.style.top = `${currentRect.top}px`;
          overlay.style.transform = "none";
          void overlay.offsetWidth;
          overlay.style.transition = "left 180ms ease-out, top 180ms ease-out";
          overlay.style.left = `${targetLeft}px`;
          overlay.style.top = `${targetTop}px`;
          window.setTimeout(resolve, 200);
        });
      });
    });

  const handleProductPointerUp = async (event: PointerEvent) => {
    if (event.pointerId !== productDragPointerIdRef.current) return;
    removeProductDragListeners();
    stopProductDragFrame();
    updateProductDragPreview(event.clientX, event.clientY);

    const previousProducts = productOrderBeforeDrag.current;
    const categoryId = orderingCategoryId;
    const draggedProductId = draggedProductIdRef.current;
    const nextOrder = [...productOrderPreview.current];
    if (!previousProducts || categoryId === null || draggedProductId === null) {
      finishProductDrag();
      return;
    }

    const previousCategoryOrder = previousProducts
      .filter((producto) => producto.categoria_id === categoryId)
      .sort((a, b) => a.orden - b.orden || a.id - b.id);
    const hasOrderChanged = nextOrder.some(
      (producto, index) => producto.id !== previousCategoryOrder[index]?.id,
    );
    await settleProductDragOverlay(draggedProductId, nextOrder);
    finishProductDrag();
    if (!hasOrderChanged) return;

    setOrderError(null);
    setIsSavingOrder(true);
    try {
      await reorderProductos(
        categoryId,
        nextOrder.map((producto) => producto.id),
      );
    } catch (err) {
      setProductos(previousProducts);
      setOrderError(
        err instanceof Error ? err.message : "No se pudo guardar el orden de productos.",
      );
    } finally {
      setIsSavingOrder(false);
    }
  };

  const handleProductPointerDown = (
    event: ReactPointerEvent<HTMLSpanElement>,
    producto: Product,
    card: HTMLDivElement,
  ) => {
    const categoryId = orderingCategoryId;
    if (
      categoryId === null ||
      isSavingOrder ||
      draggedProductIdRef.current !== null ||
      event.button !== 0 ||
      !event.isPrimary
    ) return;
    const scrollContainer = productDragScrollContainerRef.current;
    if (!scrollContainer || producto.categoria_id !== categoryId) return;

    const categoryProducts = productos
      .filter((item) => item.categoria_id === categoryId)
      .sort((a, b) => a.orden - b.orden || a.id - b.id);
    const sourceIndex = categoryProducts.findIndex((item) => item.id === producto.id);
    const sourceRect = card.getBoundingClientRect();
    const containerBounds = scrollContainer.getBoundingClientRect();
    const wrappers = Array.from(
      scrollContainer.querySelectorAll<HTMLElement>(".product-card-drag-wrapper"),
    );
    const insertionPoints = new Map<number, number>();
    const slots: Array<{ left: number; top: number }> = [];
    for (const wrapper of wrappers) {
      const productId = Number(wrapper.dataset.productId);
      const bounds = wrapper.getBoundingClientRect();
      if (!Number.isFinite(productId)) continue;
      slots.push({
        left: bounds.left - containerBounds.left + scrollContainer.scrollLeft,
        top: bounds.top - containerBounds.top,
      });
      if (productId !== producto.id) {
        insertionPoints.set(
          productId,
          bounds.left + bounds.width / 2 - containerBounds.left + scrollContainer.scrollLeft,
        );
      }
    }
    if (sourceIndex < 0 || slots.length !== categoryProducts.length) return;

    event.preventDefault();
    const clone = card.cloneNode(true) as HTMLDivElement;
    clone.classList.add("product-card-drag-overlay-card");
    const scrollBehavior = scrollContainer.style.scrollBehavior;
    productDragScrollBehaviorRef.current = scrollBehavior;
    scrollContainer.style.scrollBehavior = "auto";
    productDragScrollContainerRef.current = scrollContainer;
    productOrderBeforeDrag.current = [...productos];
    productOrderPreview.current = categoryProducts;
    productDragInsertionPointsRef.current = insertionPoints;
    productDragSlotPositionsRef.current = slots;
    productDragGrabOffsetXRef.current = sourceRect.left + sourceRect.width / 2 - event.clientX;
    productDragPointerRef.current = { x: event.clientX, y: event.clientY };
    productDragStartPointerRef.current = { x: event.clientX, y: event.clientY };
    productDragPointerIdRef.current = event.pointerId;
    draggedProductIdRef.current = producto.id;
    productDragListenersRef.current = {
      onMove: handleProductPointerMove,
      onUp: (upEvent) => void handleProductPointerUp(upEvent),
      onCancel: handleProductPointerCancel,
    };
    window.addEventListener("pointermove", productDragListenersRef.current.onMove);
    window.addEventListener("pointerup", productDragListenersRef.current.onUp);
    window.addEventListener("pointercancel", productDragListenersRef.current.onCancel);
    setDraggedProductId(producto.id);
    setProductDragOverlay({
      left: sourceRect.left,
      top: sourceRect.top,
      width: sourceRect.width,
      height: sourceRect.height,
      clone,
    });
  };

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="productos-container">
      <div className="page-header">
        <h1 className="page-title">Productos</h1>
        <div className="page-header-actions">
          <button
            className="btn-create-product"
            onClick={handleCreateClick}
          >
            <Icons.PlusIcon size={16} /> Nuevo Producto
          </button>
          <button
            className="btn-config"
            onClick={() => setShowBulkPriceModal(true)}
          >
            <Icons.PesoIcon size={16} />
            Actualizar Precios
          </button>
          <button
            className="btn-config"
            onClick={() => setShowCategoryConfig(true)}
          >
            <Icons.FolderTreeIcon size={16} />
            Categorías
          </button>
        </div>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />
      <ErrorAlert message={orderError} onClose={() => setOrderError(null)} />

      <ProductosCategoryConfigModal
        isOpen={showCategoryConfig}
        onClose={() => setShowCategoryConfig(false)}
        categorias={categorias}
        onRefresh={async () => {
          const cats = await getProductosCategorias(true);
          setCategorias(cats || []);
        }}
      />

      <BulkPriceUpdateModal
        isOpen={showBulkPriceModal}
        onClose={() => setShowBulkPriceModal(false)}
        onSuccess={handleBulkPriceSuccess}
        categorias={categorias}
      />

      {newProduct && (
        <ProductModal
          producto={newProduct}
          isOpen={isCreating}
          onClose={() => {
            setIsCreating(false);
            setNewProduct(null);
          }}
          onSave={handleCreateProduct}
          categorias={categorias}
        />
      )}

      {loading ? (
        <div className="skeleton-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : productos.length === 0 ? (
        <div className="product-selector-empty product-selector-empty-box">
          <div className="product-selector-empty-icon"><Icons.PizzaIcon size={36} /></div>
          <p>No hay productos disponibles</p>
        </div>
      ) : categorias.length === 0 ? (
        <p className="product-empty-state">No hay categorías disponibles</p>
      ) : (
        categorias.map((cat) => {
          const productosDeCategoria = productos
            .filter((p) => p.categoria_id === cat.id)
            .sort((a, b) => a.orden - b.orden || a.id - b.id);

          if (productosDeCategoria.length === 0) return null;

          const isCollapsed = collapsedCategories.has(cat.id);
          const isOrdering = orderingCategoryId === cat.id;

          return (
            <section key={cat.id} className="categoria-section">
              <div className="categoria-header">
                <h2 className="categoria-title">{cat.nombre}</h2>
                <div className="categoria-actions">
                  <button
                    className={`categoria-order ${isOrdering ? "is-active" : ""}`}
                    onClick={() => {
                      if (isOrdering) {
                        setOrderingCategoryId(null);
                      } else {
                        setOrderingCategoryId(cat.id);
                        setCollapsedCategories((previous) => {
                          const expanded = new Set(previous);
                          expanded.delete(cat.id);
                          return expanded;
                        });
                      }
                      setOrderError(null);
                    }}
                    disabled={isSavingOrder || draggedProductId !== null || productosDeCategoria.length < 2}
                    title={
                      productosDeCategoria.length < 2
                        ? "Se necesitan al menos dos productos para ordenar"
                        : isOrdering
                          ? "Finalizar ordenamiento"
                          : "Ordenar productos de esta categoría"
                    }
                    aria-label={
                      isOrdering
                        ? `Finalizar ordenamiento de ${cat.nombre}`
                        : `Ordenar productos de ${cat.nombre}`
                    }
                    aria-pressed={isOrdering}
                  >
                    <ArrowDownWideNarrow size={18} />
                  </button>
                  <button
                    className={`categoria-toggle ${isCollapsed ? "collapsed" : ""}`}
                    onClick={() => toggleCategoryCollapse(cat.id)}
                    aria-label={isCollapsed ? "Expandir" : "Colapsar"}
                    disabled={isSavingOrder || isOrdering}
                  >
                    <Icons.ChevronDownIcon size={16} />
                  </button>
                </div>
              </div>

              {!isCollapsed && (
                <div
                  className="product-scroll-horizontal"
                  ref={isOrdering ? productDragScrollContainerRef : undefined}
                >
                  {isOrdering && isSavingOrder && (
                    <p className="product-order-hint">
                      Guardando orden...
                    </p>
                  )}
                  {productosDeCategoria.map((p) => (
                    <ProductCard
                      key={p.id}
                      producto={p}
                      onProductUpdate={handleProductUpdate}
                      onProductDelete={handleProductDelete}
                      categorias={categorias}
                      isReordering={isOrdering && !isSavingOrder}
                      isDragSource={draggedProductId === p.id}
                      onProductPointerDown={handleProductPointerDown}
                    />
                  ))}
                </div>
              )}
            </section>
          );
        })
      )}
    </div>
    {productDragOverlay && createPortal(
      <div
        ref={productDragOverlayRef}
        className="product-drag-overlay"
        style={{
          left: productDragOverlay.left,
          top: productDragOverlay.top,
          width: productDragOverlay.width,
          height: productDragOverlay.height,
          transform: "translate3d(0, 0, 0)",
        }}
      />,
      document.body,
    )}
    </>
  );
};

export default ProductosPage;

import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { GripVertical } from "lucide-react";
import * as Icons from "./shared/Icons";
import ProductosCategoryModal from "./ProductosCategoryModal";
import ConfirmDialog from "./shared/ConfirmDialog";
import type { ProductoCategoria } from "../types/product_category";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import {
  deactivateProductoCategoria,
  reorderProductoCategorias,
} from "../services/productosCategoriasService";
import { getProductos } from "../services/productsService";
import { getOfertas } from "../services/ofertasService";
import "../styles/productos-categorias-modal.css";

interface ProductosCategoryConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  categorias: ProductoCategoria[];
  onRefresh: () => void | Promise<void>;
}

const ProductosCategoryConfigModal = ({
  isOpen,
  onClose,
  categorias,
  onRefresh,
}: ProductosCategoryConfigModalProps) => {
  type CategoryDragOverlay = {
    left: number;
    top: number;
    width: number;
    height: number;
    nombre: string;
  };

  const [orderedCategories, setOrderedCategories] = useState(categorias);
  const [draggedCategoryId, setDraggedCategoryId] = useState<number | null>(null);
  const [categoryDragOverlay, setCategoryDragOverlay] = useState<CategoryDragOverlay | null>(null);
  const [isSavingOrder, setIsSavingOrder] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState<ProductoCategoria | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [categoriaToDelete, setCategoriaToDelete] = useState<ProductoCategoria | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [affectedProducts, setAffectedProducts] = useState<Product[]>([]);
  const [affectedOffers, setAffectedOffers] = useState<Offer[]>([]);
  const [loadingAffected, setLoadingAffected] = useState(false);
  const categoryOrderBeforeDrag = useRef<ProductoCategoria[] | null>(null);
  const categoryOrderPreview = useRef<ProductoCategoria[]>(categorias);
  const categoryDragOverlayRef = useRef<HTMLDivElement | null>(null);
  const categoryDragFrameRef = useRef<number | null>(null);
  const categoryDragPointerRef = useRef({ x: 0, y: 0 });
  const categoryDragStartPointerRef = useRef({ x: 0, y: 0 });
  const categoryDragGrabOffsetYRef = useRef(0);
  const draggedCategoryIdRef = useRef<number | null>(null);
  const categoryDragScrollContainerRef = useRef<HTMLDivElement | null>(null);
  const categoryDragInsertionPointsRef = useRef<Map<number, number>>(new Map());
  const categoryDragSlotPositionsRef = useRef<Array<{ left: number; top: number }>>([]);
  const categoryDragPointerIdRef = useRef<number | null>(null);
  const categoryDragListenersRef = useRef<{
    onMove: (event: PointerEvent) => void;
    onUp: (event: PointerEvent) => void;
    onCancel: (event: PointerEvent) => void;
  } | null>(null);
  const pendingCategoriesSyncRef = useRef<ProductoCategoria[] | null>(null);

  useEffect(() => {
    if (!isOpen) {
      pendingCategoriesSyncRef.current = null;
      return;
    }

    if (
      categoryDragPointerIdRef.current !== null ||
      draggedCategoryIdRef.current !== null
    ) {
      pendingCategoriesSyncRef.current = categorias;
      return;
    }

    pendingCategoriesSyncRef.current = null;
    setOrderedCategories(categorias);
    categoryOrderPreview.current = categorias;
  }, [categorias, isOpen]);

  useEffect(() => () => {
    const listeners = categoryDragListenersRef.current;
    if (listeners) {
      window.removeEventListener("pointermove", listeners.onMove);
      window.removeEventListener("pointerup", listeners.onUp);
      window.removeEventListener("pointercancel", listeners.onCancel);
    }
    if (categoryDragFrameRef.current !== null) {
      cancelAnimationFrame(categoryDragFrameRef.current);
    }
  }, []);

  const handleCreateCategory = () => {
    setSelectedCategoria({ id: 0, nombre: "" });
    setIsCategoryModalOpen(true);
  };

  const handleEditCategory = (cat: ProductoCategoria) => {
    setSelectedCategoria(cat);
    setIsCategoryModalOpen(true);
  };

  const loadAffectedData = async (categoriaId: number) => {
    setLoadingAffected(true);
    try {
      const products = await getProductos(categoriaId);
      setAffectedProducts(products);

      if (products.length > 0) {
        const allOffers = await getOfertas(true);
        const productIds = products.map((p) => p.id);
        const affected = allOffers.filter((offer) =>
          offer.productos?.some((item) =>
            item.productos?.some((prod) => productIds.includes(prod.id))
          )
        );
        setAffectedOffers(affected);
      } else {
        setAffectedOffers([]);
      }
    } catch {
      setAffectedProducts([]);
      setAffectedOffers([]);
    } finally {
      setLoadingAffected(false);
    }
  };

  const handleDeleteCategoryClick = async (cat: ProductoCategoria) => {
    setCategoriaToDelete(cat);
    setShowDeleteConfirm(true);
    await loadAffectedData(cat.id);
  };

  const handleConfirmDelete = async () => {
    if (!categoriaToDelete) return;

    setIsDeleting(true);
    try {
      await deactivateProductoCategoria(categoriaToDelete.id);
      onRefresh();
      setShowDeleteConfirm(false);
      setCategoriaToDelete(null);
      setAffectedProducts([]);
      setAffectedOffers([]);
    } catch (err) {
      console.error("Error al desactivar categoría:", err);
      alert("Error al desactivar la categoría");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCategorySaved = () => {
    onRefresh();
  };

  const previewCategoryPosition = (pointerY: number) => {
    const sourceCategoryId = draggedCategoryIdRef.current;
    if (sourceCategoryId === null) return;

    const initialOrder = categoryOrderBeforeDrag.current;
    if (!initialOrder) return;
    const draggedCategory = initialOrder.find((category) => category.id === sourceCategoryId);
    if (!draggedCategory) return;

    const remainingCategories = initialOrder.filter(
      (category) => category.id !== sourceCategoryId,
    );
    const scrollContainer = categoryDragScrollContainerRef.current;
    if (!scrollContainer) return;
    const containerBounds = scrollContainer.getBoundingClientRect();
    const pointerContentY =
      pointerY +
      categoryDragGrabOffsetYRef.current -
      containerBounds.top +
      scrollContainer.scrollTop;
    const insertionIndex = remainingCategories.findIndex((category) => {
      const center = categoryDragInsertionPointsRef.current.get(category.id);
      return center !== undefined && pointerContentY < center;
    });
    const targetIndex = insertionIndex === -1 ? remainingCategories.length : insertionIndex;
    const nextOrder = [...remainingCategories];
    nextOrder.splice(targetIndex, 0, draggedCategory);

    if (nextOrder.some((category, index) => category.id !== categoryOrderPreview.current[index]?.id)) {
      categoryOrderPreview.current = nextOrder;
      setOrderedCategories(nextOrder);
    }
  };

  const handleCategoryPointerDown = (
    event: ReactPointerEvent<HTMLSpanElement>,
    category: ProductoCategoria,
  ) => {
    if (isSavingOrder || categoryDragPointerIdRef.current !== null || event.button !== 0) return;
    const row = event.currentTarget.closest("tr");
    const scrollContainer = categoryDragScrollContainerRef.current;
    if (!row || !scrollContainer) return;

    event.preventDefault();
    const rect = row.getBoundingClientRect();
    const containerBounds = scrollContainer.getBoundingClientRect();
    const initialRowRects = orderedCategories.map((item) => {
      const itemRow = document.querySelector<HTMLElement>(
        `[data-category-id="${item.id}"]`,
      );
      return itemRow?.getBoundingClientRect() ?? null;
    });
    categoryDragInsertionPointsRef.current = new Map(
      orderedCategories.flatMap((item, index) => {
        const itemBounds = initialRowRects[index];
        if (!itemBounds || item.id === category.id) return [];
        return [[
          item.id,
          itemBounds.top + itemBounds.height / 2 - containerBounds.top + scrollContainer.scrollTop,
        ] as const];
      }),
    );
    categoryDragSlotPositionsRef.current = initialRowRects.flatMap((itemBounds) =>
      itemBounds
        ? [{
            left: itemBounds.left - containerBounds.left,
            top: itemBounds.top - containerBounds.top + scrollContainer.scrollTop,
          }]
        : [],
    );
    categoryDragGrabOffsetYRef.current = rect.top + rect.height / 2 - event.clientY;
    categoryOrderBeforeDrag.current = [...orderedCategories];
    categoryOrderPreview.current = [...orderedCategories];
    draggedCategoryIdRef.current = category.id;
    categoryDragPointerRef.current = { x: event.clientX, y: event.clientY };
    categoryDragStartPointerRef.current = { x: event.clientX, y: event.clientY };
    categoryDragPointerIdRef.current = event.pointerId;
    const listeners = {
      onMove: (moveEvent: PointerEvent) => handleCategoryPointerMove(moveEvent),
      onUp: (upEvent: PointerEvent) => void handleCategoryPointerUp(upEvent),
      onCancel: (cancelEvent: PointerEvent) => handleCategoryPointerCancel(cancelEvent),
    };
    categoryDragListenersRef.current = listeners;
    window.addEventListener("pointermove", listeners.onMove);
    window.addEventListener("pointerup", listeners.onUp);
    window.addEventListener("pointercancel", listeners.onCancel);
    setDraggedCategoryId(category.id);
    setCategoryDragOverlay({
      left: rect.left,
      top: rect.top,
      width: rect.width,
      height: rect.height,
      nombre: category.nombre,
    });
  };

  const updateCategoryDragPreview = (x: number, y: number) => {
    const overlay = categoryDragOverlayRef.current;
    if (overlay) {
      const { x: startX, y: startY } = categoryDragStartPointerRef.current;
      overlay.style.transform = `translate3d(${x - startX}px, ${y - startY}px, 0)`;
    }

    previewCategoryPosition(y);
  };

  const scheduleCategoryDragFrame = () => {
    if (categoryDragFrameRef.current !== null) return;

    categoryDragFrameRef.current = requestAnimationFrame(() => {
      categoryDragFrameRef.current = null;
      const { x, y } = categoryDragPointerRef.current;
      updateCategoryDragPreview(x, y);

      const scrollContainer = categoryDragScrollContainerRef.current;
      if (!scrollContainer) return;
      const bounds = scrollContainer.getBoundingClientRect();
      const edgeSize = 56;
      let scrollDelta = 0;

      if (
        y >= bounds.top - edgeSize &&
        y < bounds.top + edgeSize &&
        scrollContainer.scrollTop > 0
      ) {
        const strength = Math.min(1, (bounds.top + edgeSize - y) / edgeSize);
        scrollDelta = -Math.max(1, Math.ceil(strength * 8));
      } else if (
        y > bounds.bottom - edgeSize &&
        y <= bounds.bottom + edgeSize &&
        scrollContainer.scrollTop + scrollContainer.clientHeight < scrollContainer.scrollHeight
      ) {
        const strength = Math.min(1, (y - (bounds.bottom - edgeSize)) / edgeSize);
        scrollDelta = Math.max(1, Math.ceil(strength * 8));
      }

      if (scrollDelta !== 0) {
        scrollContainer.scrollTop += scrollDelta;
        updateCategoryDragPreview(x, y);
        scheduleCategoryDragFrame();
      }
    });
  };

  const handleCategoryPointerMove = (event: PointerEvent) => {
    if (
      event.pointerId !== categoryDragPointerIdRef.current ||
      !categoryDragOverlayRef.current ||
      draggedCategoryIdRef.current === null
    ) return;
    categoryDragPointerRef.current = { x: event.clientX, y: event.clientY };
    scheduleCategoryDragFrame();
  };

  const handleCategoryPointerCancel = (event: PointerEvent) => {
    if (event.pointerId !== categoryDragPointerIdRef.current) return;
    const listeners = categoryDragListenersRef.current;
    if (listeners) {
      window.removeEventListener("pointermove", listeners.onMove);
      window.removeEventListener("pointerup", listeners.onUp);
      window.removeEventListener("pointercancel", listeners.onCancel);
      categoryDragListenersRef.current = null;
    }
    if (categoryDragFrameRef.current !== null) {
      cancelAnimationFrame(categoryDragFrameRef.current);
      categoryDragFrameRef.current = null;
    }
    const categoriesToRestore =
      pendingCategoriesSyncRef.current ?? categoryOrderBeforeDrag.current;
    if (categoriesToRestore) {
      setOrderedCategories(categoriesToRestore);
      categoryOrderPreview.current = categoriesToRestore;
    }
    pendingCategoriesSyncRef.current = null;
    draggedCategoryIdRef.current = null;
    setDraggedCategoryId(null);
    setCategoryDragOverlay(null);
    categoryOrderBeforeDrag.current = null;
    categoryDragInsertionPointsRef.current.clear();
    categoryDragSlotPositionsRef.current = [];
    categoryDragPointerIdRef.current = null;
  };

  const settleCategoryDragOverlay = (categoryId: number, nextOrder: ProductoCategoria[]) =>
    new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const overlay = categoryDragOverlayRef.current;
          const scrollContainer = categoryDragScrollContainerRef.current;
          const targetIndex = nextOrder.findIndex((category) => category.id === categoryId);
          const slot = categoryDragSlotPositionsRef.current[targetIndex];
          if (!overlay || !scrollContainer || !slot) {
            resolve();
            return;
          }

          const currentRect = overlay.getBoundingClientRect();
          const containerRect = scrollContainer.getBoundingClientRect();
          const targetTop = containerRect.top + slot.top - scrollContainer.scrollTop;
          const targetLeft = containerRect.left + slot.left;
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

  const handleCategoryPointerUp = async (event: PointerEvent) => {
    if (event.pointerId !== categoryDragPointerIdRef.current) return;
    const listeners = categoryDragListenersRef.current;
    if (listeners) {
      window.removeEventListener("pointermove", listeners.onMove);
      window.removeEventListener("pointerup", listeners.onUp);
      window.removeEventListener("pointercancel", listeners.onCancel);
      categoryDragListenersRef.current = null;
    }
    if (categoryDragFrameRef.current !== null) {
      cancelAnimationFrame(categoryDragFrameRef.current);
      categoryDragFrameRef.current = null;
    }
    updateCategoryDragPreview(event.clientX, event.clientY);
    const previousOrder = categoryOrderBeforeDrag.current;
    const draggedCategoryId = draggedCategoryIdRef.current;
    if (!previousOrder || draggedCategoryId === null) {
      categoryDragPointerIdRef.current = null;
      draggedCategoryIdRef.current = null;
      setDraggedCategoryId(null);
      setCategoryDragOverlay(null);
      categoryDragInsertionPointsRef.current.clear();
      categoryDragSlotPositionsRef.current = [];
      categoryOrderBeforeDrag.current = null;
      return;
    }
    const nextOrder = categoryOrderPreview.current;
    categoryDragPointerIdRef.current = null;
    const hasOrderChanged = nextOrder.some(
      (category, index) => category.id !== previousOrder[index]?.id,
    );
    if (hasOrderChanged) {
      setOrderError(null);
      setIsSavingOrder(true);
    }

    await settleCategoryDragOverlay(draggedCategoryId, nextOrder);
    draggedCategoryIdRef.current = null;
    setDraggedCategoryId(null);
    setCategoryDragOverlay(null);
    categoryDragInsertionPointsRef.current.clear();
    categoryDragSlotPositionsRef.current = [];
    if (!hasOrderChanged) {
      const categoriesToSync = pendingCategoriesSyncRef.current;
      if (categoriesToSync) {
        setOrderedCategories(categoriesToSync);
        categoryOrderPreview.current = categoriesToSync;
      }
      pendingCategoriesSyncRef.current = null;
      categoryOrderBeforeDrag.current = null;
      return;
    }

    try {
      await reorderProductoCategorias({
        categoria_ids: nextOrder.map((category) => category.id),
      });
    } catch (err) {
      const categoriesToRestore = pendingCategoriesSyncRef.current ?? previousOrder;
      setOrderedCategories(categoriesToRestore);
      categoryOrderPreview.current = categoriesToRestore;
      pendingCategoriesSyncRef.current = null;
      setOrderError(
        err instanceof Error ? err.message : "No se pudo guardar el orden.",
      );
      setIsSavingOrder(false);
      categoryOrderBeforeDrag.current = null;
      return;
    }

    pendingCategoriesSyncRef.current = null;
    try {
      await onRefresh();
    } catch (err) {
      setOrderError(
        err instanceof Error
          ? `El orden se guardó, pero no se pudo actualizar la lista: ${err.message}`
          : "El orden se guardó, pero no se pudo actualizar la lista.",
      );
    } finally {
      setIsSavingOrder(false);
      categoryOrderBeforeDrag.current = null;
    }
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="prod-cat-config-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          >
            <motion.div
              className={`prod-cat-config-modal${draggedCategoryId === null ? "" : " is-category-dragging"}`}
              initial={{ scale: 0.92, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.92, y: 20 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="prod-cat-config-header">
                <div>
                  <h2 className="prod-cat-config-title">Categorías de Productos</h2>
                </div>
                <button className="prod-cat-config-close" onClick={onClose}>
                  <Icons.XIcon size={20} />
                </button>
              </div>

              <motion.div
                className="prod-cat-config-body"
                ref={categoryDragScrollContainerRef}
                layoutScroll
              >
                <div className="prod-cat-config-actions-bar">
                  <button
                    className="btn-new-prod-category"
                    onClick={handleCreateCategory}
                    disabled={isSavingOrder}
                  >
                    <Icons.PlusIcon size={14} /> Nueva Categoría
                  </button>
                </div>
                {orderError && (
                  <p className="prod-cat-order-error" role="alert">{orderError}</p>
                )}

                {orderedCategories.length === 0 ? (
                  <div className="prod-cat-empty-state">
                    <Icons.LayersIcon size={48} />
                    <p>No hay categorías de productos</p>
                    <span>Crea categorías para comenzar a organizar tus productos.</span>
                  </div>
                ) : (
                  <table className="prod-cat-table">
                    <thead>
                      <tr>
                        <th aria-label="Orden"></th>
                        <th>Nombre</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orderedCategories.map((cat) => (
                        <motion.tr
                          key={cat.id}
                          data-category-id={cat.id}
                          layout="position"
                          transition={{ type: "spring", stiffness: 360, damping: 32, mass: 0.7 }}
                          className={draggedCategoryId === cat.id ? "prod-cat-row-pointer-source" : ""}
                        >
                          <td className="prod-cat-drag-cell">
                            <span
                              className="prod-cat-drag-handle"
                              title="Mover categoría"
                              aria-label={`Mover ${cat.nombre}`}
                              onPointerDown={(event) => handleCategoryPointerDown(event, cat)}
                            >
                              <GripVertical size={18} />
                            </span>
                          </td>
                          <td className="prod-cat-nombre">{cat.nombre}</td>
                          <td>
                            <div className="prod-cat-action-buttons">
                              <button
                                className="prod-cat-btn-action prod-cat-btn-edit"
                                onClick={() => handleEditCategory(cat)}
                                disabled={isSavingOrder}
                                title="Editar categoría"
                              >
                                <Icons.EditIcon size={16} />
                              </button>
                              <button
                                className="prod-cat-btn-action prod-cat-btn-delete"
                                onClick={() => handleDeleteCategoryClick(cat)}
                                disabled={isDeleting || isSavingOrder}
                                title="Desactivar categoría"
                              >
                                <Icons.TrashIcon size={16} />
                              </button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {isSavingOrder && (
                  <p className="prod-cat-order-saving" role="status">Guardando orden...</p>
                )}
              </motion.div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {categoryDragOverlay && createPortal(
        <div
          ref={categoryDragOverlayRef}
          className="prod-cat-drag-overlay"
          style={{
            left: categoryDragOverlay.left,
            top: categoryDragOverlay.top,
            width: categoryDragOverlay.width,
            height: categoryDragOverlay.height,
            transform: "translate3d(0, 0, 0)",
          }}
        >
          <span className="prod-cat-drag-cell"><GripVertical size={18} /></span>
          <span className="prod-cat-nombre">{categoryDragOverlay.nombre}</span>
          <span className="prod-cat-action-buttons" aria-hidden="true">
            <span className="prod-cat-btn-action prod-cat-btn-edit"><Icons.EditIcon size={16} /></span>
            <span className="prod-cat-btn-action prod-cat-btn-delete"><Icons.TrashIcon size={16} /></span>
          </span>
        </div>,
        document.body,
      )}

      {/* Sub-modals rendered outside the transformed container to avoid CSS fixed-position clipping */}
      <ProductosCategoryModal
        categoria={selectedCategoria}
        isOpen={isCategoryModalOpen}
        onClose={() => {
          setIsCategoryModalOpen(false);
          setSelectedCategoria(null);
        }}
        onSave={handleCategorySaved}
      />

          {/* Dialog de confirmación de eliminación */}
          <ConfirmDialog
            isOpen={showDeleteConfirm}
            title={<><Icons.WarningIcon size={18} /> Desactivar Categoría</>}
            message={
              <>
                ¿Está seguro que desea desactivar{" "}
                <strong style={{ color: "#ffffff" }}>{categoriaToDelete?.nombre}</strong>?
                {loadingAffected && (
                  <div style={{ marginTop: "10px", fontSize: "14px", color: "#aaa" }}>
                    Cargando elementos relacionados...
                  </div>
                )}
                {!loadingAffected && affectedProducts.length > 0 && (
                  <div
                    style={{
                      marginTop: "15px",
                      padding: "15px",
                      backgroundColor: "rgba(255, 193, 7, 0.15)",
                      borderRadius: "10px",
                      border: "1px solid rgba(255, 193, 7, 0.4)",
                      textAlign: "left",
                    }}
                  >
                    <div
                      style={{
                        color: "#ffc107",
                        fontWeight: 600,
                        marginBottom: "12px",
                        fontSize: "15px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <Icons.WarningIcon size={16} color="#ffc107" />
                      También se desactivarán {affectedProducts.length}{" "}
                      {affectedProducts.length === 1 ? "producto" : "productos"}:
                    </div>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: "28px",
                        fontSize: "14px",
                        color: "#ffffff",
                        listStyleType: "disc",
                        maxHeight: "120px",
                        overflowY: "auto",
                      }}
                    >
                      {affectedProducts.map((product) => (
                        <li key={product.id} style={{ marginBottom: "6px", lineHeight: "1.5" }}>
                          {product.nombre}
                        </li>
                      ))}
                    </ul>

                    {affectedOffers.length > 0 && (
                      <>
                        <div
                          style={{
                            color: "#ffc107",
                            fontWeight: 600,
                            marginTop: "16px",
                            marginBottom: "12px",
                            fontSize: "15px",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <Icons.WarningIcon size={16} color="#ffc107" />
                          Y {affectedOffers.length}{" "}
                          {affectedOffers.length === 1 ? "oferta" : "ofertas"}:
                        </div>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: "28px",
                            fontSize: "14px",
                            color: "#ffffff",
                            listStyleType: "disc",
                            maxHeight: "100px",
                            overflowY: "auto",
                          }}
                        >
                          {affectedOffers.map((offer) => (
                            <li key={offer.id} style={{ marginBottom: "6px", lineHeight: "1.5" }}>
                              {offer.nombre}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </>
            }
            confirmText="Desactivar"
            cancelText="Cancelar"
            onConfirm={handleConfirmDelete}
            onCancel={() => {
              setShowDeleteConfirm(false);
              setCategoriaToDelete(null);
              setAffectedProducts([]);
              setAffectedOffers([]);
            }}
            confirmDanger
            confirmDisabled={isDeleting}
            cancelDisabled={isDeleting}
          />
    </>
  );
};

export default ProductosCategoryConfigModal;

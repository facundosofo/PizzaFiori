import { useEffect, useState } from "react";
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
  const [orderedCategories, setOrderedCategories] = useState(categorias);
  const [draggedCategoryId, setDraggedCategoryId] = useState<number | null>(null);
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

  useEffect(() => {
    if (isOpen) setOrderedCategories(categorias);
  }, [categorias, isOpen]);

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

  const handleCategoryDrop = async (targetCategoryId: number) => {
    if (draggedCategoryId === null || draggedCategoryId === targetCategoryId) return;

    const previousOrder = orderedCategories;
    const nextOrder = [...previousOrder];
    const sourceIndex = nextOrder.findIndex(
      (category) => category.id === draggedCategoryId,
    );
    const targetIndex = nextOrder.findIndex(
      (category) => category.id === targetCategoryId,
    );
    if (sourceIndex < 0 || targetIndex < 0) return;

    const [movedCategory] = nextOrder.splice(sourceIndex, 1);
    nextOrder.splice(targetIndex, 0, movedCategory);
    setOrderedCategories(nextOrder);
    setDraggedCategoryId(null);
    setOrderError(null);
    setIsSavingOrder(true);

    try {
      await reorderProductoCategorias({
        categoria_ids: nextOrder.map((category) => category.id),
      });
    } catch (err) {
      setOrderedCategories(previousOrder);
      setOrderError(
        err instanceof Error ? err.message : "No se pudo guardar el orden.",
      );
      setIsSavingOrder(false);
      return;
    }

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
              className="prod-cat-config-modal"
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

              <div className="prod-cat-config-body">
                <div className="prod-cat-config-actions-bar">
                  <button
                    className="btn-new-prod-category"
                    onClick={handleCreateCategory}
                    disabled={isSavingOrder}
                  >
                    <Icons.PlusIcon size={14} /> Nueva Categoría
                  </button>
                </div>
                <p className="prod-cat-order-hint">
                  Arrastrá las categorías para cambiar su orden. Para reflejarlo en la
                  web de pedidos, publicá nuevamente el catálogo desde Configuración.
                </p>
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
                        <tr
                          key={cat.id}
                          draggable={!isSavingOrder}
                          className={draggedCategoryId === cat.id ? "prod-cat-row-dragging" : ""}
                          onDragStart={(event) => {
                            setDraggedCategoryId(cat.id);
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData("text/plain", String(cat.id));
                          }}
                          onDragOver={(event) => event.preventDefault()}
                          onDrop={(event) => {
                            event.preventDefault();
                            void handleCategoryDrop(cat.id);
                          }}
                          onDragEnd={() => setDraggedCategoryId(null)}
                        >
                          <td className="prod-cat-drag-cell">
                            <span
                              className="prod-cat-drag-handle"
                              title="Arrastrar para reordenar"
                              aria-label={`Arrastrar ${cat.nombre} para reordenar`}
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
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {isSavingOrder && (
                  <p className="prod-cat-order-saving" role="status">Guardando orden...</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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

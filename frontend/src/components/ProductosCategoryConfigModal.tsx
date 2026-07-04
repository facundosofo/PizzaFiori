import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import ProductosCategoryModal from "./ProductosCategoryModal";
import ConfirmDialog from "./shared/ConfirmDialog";
import type { ProductoCategoria } from "../types/product_category";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import { deactivateProductoCategoria } from "../services/productosCategoriasService";
import { getProductos } from "../services/productsService";
import { getOfertas } from "../services/ofertasService";
import "../styles/productos-categorias-modal.css";

interface ProductosCategoryConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  categorias: ProductoCategoria[];
  onRefresh: () => void;
}

const ProductosCategoryConfigModal = ({
  isOpen,
  onClose,
  categorias,
  onRefresh,
}: ProductosCategoryConfigModalProps) => {
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState<ProductoCategoria | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [categoriaToDelete, setCategoriaToDelete] = useState<ProductoCategoria | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [affectedProducts, setAffectedProducts] = useState<Product[]>([]);
  const [affectedOffers, setAffectedOffers] = useState<Offer[]>([]);
  const [loadingAffected, setLoadingAffected] = useState(false);

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
                  <button className="btn-new-prod-category" onClick={handleCreateCategory}>
                    <Icons.PlusIcon size={14} /> Nueva Categoría
                  </button>
                </div>

                {categorias.length === 0 ? (
                  <div className="prod-cat-empty-state">
                    <Icons.LayersIcon size={48} />
                    <p>No hay categorías de productos</p>
                    <span>Crea categorías para comenzar a organizar tus productos.</span>
                  </div>
                ) : (
                  <table className="prod-cat-table">
                    <thead>
                      <tr>
                        <th>Nombre</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categorias.map((cat) => (
                        <tr key={cat.id}>
                          <td className="prod-cat-nombre">{cat.nombre}</td>
                          <td>
                            <div className="prod-cat-action-buttons">
                              <button
                                className="prod-cat-btn-action prod-cat-btn-edit"
                                onClick={() => handleEditCategory(cat)}
                                title="Editar categoría"
                              >
                                <Icons.EditIcon size={16} />
                              </button>
                              <button
                                className="prod-cat-btn-action prod-cat-btn-delete"
                                onClick={() => handleDeleteCategoryClick(cat)}
                                disabled={isDeleting}
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

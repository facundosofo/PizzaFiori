import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import ProductModal from "./ProductModal";
import ErrorAlert from "./ErrorAlert";
import { deleteProducto } from "../services/productsService";
import "../styles/product-card.css";
import env from "../config/env";



interface ProductCardProps {
  producto: Product;
  onProductUpdate?: (producto: Product) => void;
  onProductDelete?: (productoId: number) => void;
  categorias?: Category[];
}

const ProductCard = ({
  producto,
  onProductUpdate,
  onProductDelete,
  categorias = [],
}: ProductCardProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const imageUrl = producto.imagen ? `${env.API_BASE_URL}/${producto.imagen}` : "/placeholder.png";

  const formatPrecio = (value: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatCantidad = (cantidad: number): string => {
    switch (cantidad) {
      case 1:
        return "Unidad";
      case 6:
        return "1/2 Docena";
      case 12:
        return "Docena";
      default:
        return `${cantidad} unid.`;
    }
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleSaveProduct = (updatedProducto: Product) => {
    if (onProductUpdate) {
      onProductUpdate(updatedProducto);
    }
    setIsModalOpen(false);
  };

  const handleDeleteProduct = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteProducto(producto.id);
      if (onProductDelete) {
        onProductDelete(producto.id);
      }
      setShowDeleteConfirm(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido al eliminar producto";
      setDeleteError(`No se pudo eliminar: ${errorMessage}`);
      console.error("Error eliminando producto:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <motion.div
        className="product-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        whileHover={{ scale: 1.05, y: -5 }}
        whileTap={{ scale: 0.97 }}
        onClick={handleOpenModal}
      >
        <button
          className="product-card-delete"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteConfirm(true);
          }}
          title="Eliminar producto"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>

        <div className="product-card-image">
          <img src={imageUrl} alt={producto.nombre} />
        </div>

        <div className="product-card-body">
          <h3 className="product-card-title">{producto.nombre.toUpperCase()}</h3>

          <div className="product-card-prices">
            {producto.precios && producto.precios.length > 0 ? (
              producto.precios.map((precio_item) => (
                <div key={precio_item.id} className="price-item">
                  <span className="price-cantidad">{formatCantidad(precio_item.cantidad)}</span>
                  <span className="price-amount">{formatPrecio(precio_item.precio)}</span>
                </div>
              ))
            ) : (
              <div className="price-item no-price">Sin precios</div>
            )}
          </div>

          <button
            className="product-card-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenModal();
            }}
          >
            Editar
          </button>
        </div>
      </motion.div>

      <ProductModal
        producto={producto}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveProduct}
        categorias={categorias}
      />

      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !isDeleting && setShowDeleteConfirm(false)}
          >
            <motion.div
              className="confirm-dialog"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="confirm-title">⚠️ Eliminar Producto</h3>
              <p className="confirm-message">
                ¿Está seguro que desea eliminar{" "}
                <strong>{producto.nombre}</strong>?
              </p>
              <p className="confirm-warning">Esta acción no se puede deshacer.</p>

              <div className="confirm-actions">
                <button
                  className="confirm-cancel-btn"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                >
                  Cancelar
                </button>
                <button
                  className="confirm-delete-btn"
                  onClick={handleDeleteProduct}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Eliminando..." : "Eliminar"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ErrorAlert message={deleteError} onClose={() => setDeleteError(null)} />
    </>
  );
};

export default ProductCard;

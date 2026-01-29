import { motion } from "framer-motion";
import { useState } from "react";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import ProductModal from "./ProductModal";
import ErrorAlert from "./shared/ErrorAlert";
import ConfirmDialog from "./shared/ConfirmDialog";
import { TrashIcon } from "./shared/Icons";
import { deactivateProducto } from "../services/productsService";
import { formatCurrency } from "../utils/formatters";
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

  const handleDeactivateProduct = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deactivateProducto(producto.id);
      if (onProductDelete) {
        onProductDelete(producto.id);
      }
      setShowDeleteConfirm(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido al desactivar producto";
      setDeleteError(`No se pudo desactivar: ${errorMessage}`);
      console.error("Error desactivando producto:", error);
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
          className="product-card-deactivate"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteConfirm(true);
          }}
          title="Desactivar producto"
        >
          <TrashIcon />
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
                  <span className="price-amount">{formatCurrency(precio_item.precio)}</span>
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

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="⚠️ Desactivar Producto"
        message={
          <>
            ¿Está seguro que desea desactivar <strong>{producto.nombre}</strong>?
          </>
        }
        confirmText={isDeleting ? "Desactivando..." : "Desactivar"}
        cancelText="Cancelar"
        onConfirm={handleDeactivateProduct}
        onCancel={() => setShowDeleteConfirm(false)}
        confirmDanger
        confirmDisabled={isDeleting}
        cancelDisabled={isDeleting}
      />

      <ErrorAlert message={deleteError} onClose={() => setDeleteError(null)} />
    </>
  );
};

export default ProductCard;

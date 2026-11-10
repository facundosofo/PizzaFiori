import { motion } from "framer-motion";
import { useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { GripVertical } from "lucide-react";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import type { Offer } from "../types/offer";
import ProductModal from "./ProductModal";
import ErrorAlert from "./shared/ErrorAlert";
import ConfirmDialog from "./shared/ConfirmDialog";
import * as Icons from './shared/Icons';
import { deactivateProducto } from "../services/productsService";
import { getOfertas } from "../services/ofertasService";
import { formatCurrency } from "../utils/formatters";
import { getProductImageUrl } from "../utils/productImage";
import "../styles/product-card.css";



interface ProductCardProps {
  producto: Product;
  onProductUpdate?: (producto: Product) => void;
  onProductDelete?: (productoId: number) => void;
  categorias?: ProductoCategoria[];
  isReordering?: boolean;
  isDragSource?: boolean;
  onProductPointerDown?: (
    event: ReactPointerEvent<HTMLSpanElement>,
    producto: Product,
    card: HTMLDivElement,
  ) => void;
}

const ProductCard = ({
  producto,
  onProductUpdate,
  onProductDelete,
  categorias = [],
  isReordering = false,
  isDragSource = false,
  onProductPointerDown,
}: ProductCardProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [affectedOffers, setAffectedOffers] = useState<Offer[]>([]);
  const [loadingOffers, setLoadingOffers] = useState(false);

  const imageUrl = getProductImageUrl(producto);

  const isSameCantidad = (a: number, b: number) => Math.abs(a - b) < 1e-9;
  const formatCantidad = (cantidad: number): string => {
    if (isSameCantidad(cantidad, 1)) return "Unidad";
    if (isSameCantidad(cantidad, 0.5)) return "Porción 1/2";
    if (isSameCantidad(cantidad, 0.25)) return "Porción 1/4";
    if (isSameCantidad(cantidad, 0.125)) return "Porción 1/8";
    if (isSameCantidad(cantidad, 6)) return "1/2 Docena";
    if (isSameCantidad(cantidad, 12)) return "Docena";
    return `${cantidad} unid.`;
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

  const loadAffectedOffers = async () => {
    setLoadingOffers(true);
    try {
      const allOffers = await getOfertas(true); // Solo ofertas activas
      
      // Filtrar ofertas que contienen este producto
      const affected = allOffers.filter(offer => 
        offer.productos?.some(item => 
          item.productos?.some(prod => prod.id === producto.id)
        )
      );
      
      setAffectedOffers(affected);
    } catch {
      setAffectedOffers([]);
    } finally {
      setLoadingOffers(false);
    }
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
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div
        className={`product-card-drag-wrapper${isReordering ? " is-reordering" : ""}`}
        data-product-id={producto.id}
      >
        <motion.div
          className={`product-card${isReordering ? " is-reordering" : ""}${isDragSource ? " is-drag-source" : ""}`}
          layout={isReordering ? "position" : true}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ layout: { type: "spring", stiffness: 420, damping: 34 }, opacity: { duration: 0.4 }, y: { duration: 0.4 } }}
          whileHover={isReordering ? undefined : { scale: 1.05, y: -5 }}
          whileTap={isReordering ? undefined : { scale: 0.97 }}
          onClick={isReordering ? undefined : handleOpenModal}
        >
          {isReordering && (
            <span
              className="product-order-grip"
              title={`Mover ${producto.nombre}`}
              aria-label={`Mover ${producto.nombre}`}
              onPointerDown={(event) => {
                const card = event.currentTarget.closest(".product-card");
                if (card instanceof HTMLDivElement) {
                  onProductPointerDown?.(event, producto, card);
                }
              }}
            >
              <GripVertical size={20} />
            </span>
          )}
        <button
          className="product-card-deactivate"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteConfirm(true);
            loadAffectedOffers();
          }}
          title="Desactivar producto"
        >
          <Icons.TrashIcon />
        </button>

        <div className="product-card-image">
          <img
            src={imageUrl}
            alt={producto.nombre}
            loading="lazy"
            decoding="async"
            draggable={false}
          />
        </div>

        <div className="product-card-body">
          {producto.sku && (
            <div className="product-card-sku" style={{ 
              fontSize: "10px", 
              color: "#999", 
              textAlign: "right",
              marginBottom: "2px",
              fontFamily: "monospace"
            }}>
              SKU: {producto.sku}
            </div>
          )}
          <h3 className="product-card-title">
            <span className="product-card-title-text">{producto.nombre.toUpperCase()}</span>
          </h3>

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
      </div>

      <ProductModal
        producto={producto}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveProduct}
        categorias={categorias}
      />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={<><Icons.WarningIcon size={18} /> Desactivar Producto</>}
        message={
          <>
            ¿Está seguro que desea desactivar <strong style={{ color: "#ffffff" }}>{producto.nombre}</strong>?
            {loadingOffers && (
              <div style={{ marginTop: "10px", fontSize: "14px", color: "#aaa" }}>
                Cargando ofertas relacionadas...
              </div>
            )}
            {!loadingOffers && affectedOffers.length > 0 && (
              <div style={{ 
                marginTop: "15px", 
                padding: "15px", 
                backgroundColor: "rgba(255, 193, 7, 0.15)", 
                borderRadius: "10px", 
                border: "1px solid rgba(255, 193, 7, 0.4)",
                textAlign: "left"
              }}>
                <div style={{ 
                  color: "#ffc107", 
                  fontWeight: 600, 
                  marginBottom: "12px", 
                  fontSize: "15px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px"
                }}>
                  <Icons.WarningIcon size={16} color="#ffc107" />
                  También se desactivarán {affectedOffers.length} {affectedOffers.length === 1 ? "oferta" : "ofertas"}:
                </div>
                <ul style={{ 
                  margin: 0, 
                  paddingLeft: "28px", 
                  fontSize: "14px", 
                  color: "#ffffff",
                  listStyleType: "disc"
                }}>
                  {affectedOffers.map(offer => (
                    <li key={offer.id} style={{ 
                      marginBottom: "6px",
                      lineHeight: "1.5"
                    }}>
                      {offer.nombre}
                    </li>
                  ))}
                </ul>
              </div>
            )}
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

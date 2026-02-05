import { motion } from "framer-motion";
import { useState } from "react";
import type { Offer, OfferItem } from "../types/offer";
import type { Product } from "../types/product";
import * as Icons from './shared/Icons';
import Badge from "./shared/Badge";
import ConfirmDialog from "./shared/ConfirmDialog";
import ErrorAlert from "./shared/ErrorAlert";
import { deactivateOffer } from "../services/ofertasService";
import { formatCurrency } from "../utils/formatters";
import "../styles/offer-card.css";

interface OfferCardProps {
  oferta: Offer;
  productos: Product[];
  onEdit?: (oferta: Offer) => void;
  onOfferUpdate?: (oferta: Offer) => void;
  onOfferDelete?: (ofertaId: number) => void;
}

const OfferCard = ({
  oferta,
  productos,
  onEdit,

  onOfferDelete,
}: OfferCardProps) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleEdit = () => {
    if (onEdit) {
      onEdit(oferta);
    }
  };

  const handleDeactivate = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deactivateOffer(oferta.id);
      if (onOfferDelete) {
        onOfferDelete(oferta.id);
      }
      setShowDeleteConfirm(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido al desactivar oferta";
      setDeleteError(`No se pudo desactivar: ${errorMessage}`);
      console.error("Error desactivando oferta:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  const getItemBadgeVariant = (item: OfferItem) => {
    if (!item) return "neutral";
    if (item.productos && item.productos.length > 1) return "warning"; // Opciones múltiples
    if (item.categoria_id) return "info"; // Categoría
    return "neutral"; // Producto específico
  };

  const getItemTypeLabel = (item: OfferItem) => {
    if (!item) return "Producto";
    if (item.productos && item.productos.length > 1) return "Opciones";
    if (item.categoria_id) return "Categoría";
    return "Específico";
  };

  const getItemDetail = (item: OfferItem): { cantidad: number; detalle: string } => {
    if (!item) return { cantidad: 0, detalle: "" };
    
    let detalle = "";
    
    // Opciones múltiples
    if (item.productos && item.productos.length > 1) {
      detalle = item.productos.map((p) => p.nombre).join(", ");
    }
    // Categoría
    else if (item.categoria_id) {
      detalle = item.categoria_nombre || "Categoría";
    }
    // Producto específico
    else if (item.productos && item.productos.length === 1) {
      detalle = item.productos[0].nombre;
    }
    else {
      detalle = "Producto";
    }
    
    return { cantidad: item.cantidad, detalle };
  };

  return (
    <>
      <motion.div
        className="offer-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        whileHover={{ scale: 1.02, y: -4 }}
      >
        {/* Contenido principal */}
        <div className="offer-card-body">
          <div className="offer-card-header">
            <h3 className="offer-card-title">{oferta.nombre}</h3>
          </div>

          {oferta.descripcion && (
            <p className="offer-description">{oferta.descripcion}</p>
          )}

          {/* Items incluidos */}
          {oferta.productos && oferta.productos.length > 0 && (
            <div className="offer-items">
              <span className="offer-items-label">Incluye:</span>
              <ul className="offer-items-list">
                {oferta.productos.map((item) => {
                  const { cantidad, detalle } = getItemDetail(item);
                  return (
                    <li key={item.id} className="offer-item">
                      <span className="offer-qty">{cantidad}x</span>
                      <span className="offer-item-detail">{detalle}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>

        {/* Acciones - Abajo con precio y botones */}
        <div className="offer-card-actions">
          <div className="offer-price">{formatCurrency(oferta.precio)}</div>
          <div className="offer-action-buttons">
            <button
              className="offer-action-btn offer-action-edit"
              onClick={handleEdit}
              title="Editar oferta"
            >
              <Icons.EditIcon />
            </button>
            <button
              className="offer-action-btn offer-action-delete"
              onClick={() => setShowDeleteConfirm(true)}
              title="Desactivar oferta"
            >
              <Icons.TrashIcon />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={<><Icons.WarningIcon size={18} /> Desactivar Oferta</>}
        message={
          <>
            ¿Está seguro que desea desactivar <strong style={{ color: "#ffffff" }}>{oferta.nombre}</strong>?
          </>
        }
        confirmText={isDeleting ? "Desactivando..." : "Desactivar"}
        cancelText="Cancelar"
        onConfirm={handleDeactivate}
        onCancel={() => setShowDeleteConfirm(false)}
        confirmDanger
        confirmDisabled={isDeleting}
        cancelDisabled={isDeleting}
      />

      <ErrorAlert message={deleteError} onClose={() => setDeleteError(null)} />
    </>
  );
};

export default OfferCard;

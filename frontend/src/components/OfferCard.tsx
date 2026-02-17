import { motion } from "framer-motion";
import { useState } from "react";
import type { Offer, OfferItem } from "../types/offer";
import type { Product } from "../types/product";
import * as Icons from "./shared/Icons";
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

/* -------------------- Helpers -------------------- */

const getItemDetail = (
  item: OfferItem
): { cantidad: number; detalle: string } => {
  let detalle = "Producto";

  if (item.productos && item.productos.length > 1) {
    detalle = item.productos.map((p) => p.nombre).join(", ");
  } else if (item.categoria_id) {
    detalle = item.categoria_nombre || "Categoría";
  } else if (item.productos && item.productos.length === 1) {
    detalle = item.productos[0].nombre;
  }

  return { cantidad: item.cantidad, detalle };
};

/* -------------------- Component -------------------- */

const OfferCard = ({
  oferta,
  productos,
  onEdit,
  onOfferDelete,
}: OfferCardProps) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [expanded, setExpanded] = useState(false);

  const shouldTruncate =
    oferta.descripcion && oferta.descripcion.length > 52;

  const handleEdit = () => {
    onEdit?.(oferta);
  };

  const handleDeactivate = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deactivateOffer(oferta.id);
      onOfferDelete?.(oferta.id);
      setShowDeleteConfirm(false);
    } catch (error) {
      const msg =
        error instanceof Error
          ? error.message
          : "Error desconocido al desactivar oferta";
      setDeleteError(`No se pudo desactivar: ${msg}`);
    } finally {
      setIsDeleting(false);
    }
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
        {/* Cuerpo */}
        <div className="offer-card-body">
          <div className="offer-card-header">
            <h3 className="offer-card-title">{oferta.nombre}</h3>
          </div>

          <div className="offer-description-container">
          {oferta.descripcion ? (
            <>
              <p
                className={
                  expanded
                    ? "offer-description offer-description-expanded"
                    : "offer-description"
                }
              >
                {expanded || !shouldTruncate ? (
                  oferta.descripcion
                ) : (
                  <>
                    {oferta.descripcion.slice(0, 52)}
                    <span className="offer-description-ellipsis">…</span>
                    <button
                      className="offer-description-see-more"
                      onClick={() => setExpanded(true)}
                    >
                      Ver más
                    </button>
                  </>
                )}
              </p>

              {expanded && (
                <button
                  className="offer-description-see-more"
                  onClick={() => setExpanded(false)}
                >
                  Ver menos
                </button>
              )}
            </>
          ) : (
            <div className="offer-description-placeholder" />
          )}
        </div>

          <div className="offer-card-separator" />

          {/* Items */}
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

        <div className="offer-card-separator" />

        {/* Footer */}
        <div className="offer-card-actions">
          <div className="offer-price">
            {formatCurrency(oferta.precio)}
          </div>

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

      {/* Confirmación */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={
          <>
            <Icons.WarningIcon size={18} /> Desactivar Oferta
          </>
        }
        message={
          <>
            ¿Está seguro que desea desactivar{" "}
            <strong style={{ color: "#ffffff" }}>
              {oferta.nombre}
            </strong>
            ?
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

      <ErrorAlert
        message={deleteError}
        onClose={() => setDeleteError(null)}
      />
    </>
  );
};

export default OfferCard;

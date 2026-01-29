import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Sale } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import { getSaleById, updateSale } from "../services/salesService";
import { formatCurrency, formatDateDisplay } from "../utils/formatters";
import { XIcon } from "./Icons";
import "../styles/sale-modal.css";

type SaleWithDetails = Omit<Sale, 'items'> & {
  items: SaleItemWithDetails[];
};

interface SaleEditModalProps {
  saleId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (sale: Sale) => void;
  allProducts: Product[];
  allOffers: Offer[];
}

const SaleEditModal = ({
  saleId,
  isOpen,
  onClose,
  onSave,
  allProducts,
  allOffers,
}: SaleEditModalProps) => {
  const [sale, setSale] = useState<SaleWithDetails | null>(null);
  const [editedItems, setEditedItems] = useState<SaleItemWithDetails[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Add item state
  const [itemType, setItemType] = useState<"producto" | "oferta">("producto");
  const [selectedProductId, setSelectedProductId] = useState<number>(0);
  const [selectedOfferId, setSelectedOfferId] = useState<number>(0);
  const [newItemQuantity, setNewItemQuantity] = useState<number>(1);

  useEffect(() => {
    if (saleId && isOpen) {
      const fetchSale = async () => {
        try {
          setLoading(true);
          setError("");
          const data = await getSaleById(saleId, allProducts, allOffers);
          setSale(data);
          setEditedItems(data.items);
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "Error desconocido";
          setError(errorMessage);
          console.error("Error fetching sale details:", err);
        } finally {
          setLoading(false);
        }
      };

      fetchSale();
    }
  }, [saleId, isOpen, allProducts, allOffers]);

  const handleQuantityChange = (itemId: number, newQuantity: number) => {
    if (newQuantity < 1 || newQuantity > 1000) return;

    setEditedItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const subtotal = item.precio_unitario * newQuantity;
          return { ...item, cantidad: newQuantity, subtotal };
        }
        return item;
      })
    );
  };

  const handlePriceChange = (itemId: number, newPrice: number) => {
    if (newPrice < 0) return;

    setEditedItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const subtotal = newPrice * item.cantidad;
          return { ...item, precio_unitario: newPrice, subtotal };
        }
        return item;
      })
    );
  };

  const handleRemoveItem = (itemId: number) => {
    setEditedItems((prev) => prev.filter((item) => item.id !== itemId));
  };

  const handleAddItem = () => {
    if (itemType === "producto" && selectedProductId === 0) {
      setError("Selecciona un producto");
      return;
    }
    if (itemType === "oferta" && selectedOfferId === 0) {
      setError("Selecciona una oferta");
      return;
    }
    if (newItemQuantity < 1 || newItemQuantity > 1000) {
      setError("Cantidad debe ser entre 1 y 1000");
      return;
    }

    setError("");

    // TODO: Reemplazar con componente compartido cuando pantalla Registrar Ventas esté lista
    let itemName = "";
    let precio = 0;

    if (itemType === "producto") {
      const product = allProducts.find((p) => p.id === selectedProductId);
      if (product) {
        itemName = product.nombre;
        // Get price for quantity 1 (default price)
        const defaultPrice = product.precios?.find((p) => p.cantidad === 1);
        precio = defaultPrice?.precio || 0;
      }
    } else {
      const offer = allOffers.find((o) => o.id === selectedOfferId);
      if (offer) {
        itemName = offer.nombre;
        precio = offer.precio;
      }
    }

    const newItem: SaleItemWithDetails = {
      id: Date.now(), // Temporary ID for new items
      producto_id: itemType === "producto" ? selectedProductId : null,
      oferta_id: itemType === "oferta" ? selectedOfferId : null,
      cantidad: newItemQuantity,
      precio_unitario: precio,
      subtotal: precio * newItemQuantity,
      producto_nombre: itemType === "producto" ? itemName : undefined,
      oferta_nombre: itemType === "oferta" ? itemName : undefined,
    };

    setEditedItems((prev) => [...prev, newItem]);

    // Reset form
    setSelectedProductId(0);
    setSelectedOfferId(0);
    setNewItemQuantity(1);
  };

  const calculateTotal = (): number => {
    return editedItems.reduce((sum, item) => sum + item.subtotal, 0);
  };

  const handleSave = async () => {
    if (editedItems.length === 0) {
      setError("La venta debe tener al menos un item");
      return;
    }

    try {
      setSaving(true);
      setError("");

      // Call update service with precio_unitario
      await updateSale(saleId!, {
        items: editedItems.map((item) => ({
          producto_id: item.producto_id || undefined,
          oferta_id: item.oferta_id || undefined,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario, // Incluir precio_unitario
        })),
      });

      // Create updated sale object for parent component
      const updatedSale: Sale = {
        ...sale!,
        items: editedItems,
        total: calculateTotal(),
        fecha_actualizacion: new Date().toISOString(),
      };

      onSave(updatedSale);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="sale-modal-overlay"
          onClick={handleOverlayClick}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div
            className="sale-modal-content sale-edit-modal"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="sale-modal-header">
              <h2>Editar Venta</h2>
              <button
                className="sale-modal-close-btn"
                onClick={onClose}
                aria-label="Cerrar modal"
              >
                ✕
              </button>
            </div>

            <div className="sale-modal-body">
              {loading ? (
                <div className="sale-detail-loading">
                  <motion.div
                    className="loading-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    ⟳
                  </motion.div>
                  <p>Cargando detalles...</p>
                </div>
              ) : error ? (
                <div className="sale-detail-error">
                  <p>❌ {error}</p>
                </div>
              ) : sale ? (
                <>
                  <div className="sale-info">
                    <div className="sale-info-row">
                      <span className="sale-info-label">N° Orden:</span>
                      <span className="sale-info-value">
                        {sale.numero_orden || `#${sale.id}`}
                      </span>
                    </div>
                    <div className="sale-info-row">
                      <span className="sale-info-label">Fecha:</span>
                      <span className="sale-info-value">
                        {formatDateDisplay(sale.fecha_creacion)}
                      </span>
                    </div>
                  </div>

                  <div className="sale-items-section">
                    <h3>Editar Items</h3>
                    <div className="sale-items-table">
                      <div className="sale-items-header">
                        <div className="sale-item-col-name">Nombre</div>
                        <div className="sale-item-col-qty">Cant.</div>
                        <div className="sale-item-col-price">P. Unit.</div>
                        <div className="sale-item-col-subtotal">Subtotal</div>
                        <div className="sale-item-col-actions">Acción</div>
                      </div>

                      {editedItems.map((item) => (
                        <div key={item.id} className="sale-items-row">
                          <div className="sale-item-col-name">
                            {item.producto_nombre || item.oferta_nombre || "Item"}
                            {item.producto_id && (
                              <span className="sale-item-type"> (Producto)</span>
                            )}
                            {item.oferta_id && (
                              <span className="sale-item-type"> (Oferta)</span>
                            )}
                          </div>
                          <div className="sale-item-col-qty">
                            <input
                              type="number"
                              className="quantity-input"
                              min="1"
                              max="1000"
                              value={item.cantidad}
                              onChange={(e) =>
                                handleQuantityChange(item.id, parseInt(e.target.value) || 1)
                              }
                            />
                          </div>
                          <div className="sale-item-col-price">
                            <input
                              type="number"
                              className="price-input"
                              min="0"
                              step="0.01"
                              value={item.precio_unitario}
                              onChange={(e) =>
                                handlePriceChange(item.id, parseFloat(e.target.value) || 0)
                              }
                            />
                          </div>
                          <div className="sale-item-col-subtotal">
                            {formatCurrency(item.subtotal)}
                          </div>
                          <div className="sale-item-col-actions">
                            <button
                              className="item-remove-btn"
                              onClick={() => handleRemoveItem(item.id)}
                              title="Eliminar item"
                            >
                              <XIcon size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="add-item-section">
                    <h3>Agregar Item</h3>
                    <div className="add-item-form">
                      <div className="form-row">
                        <div className="form-group">
                          <label>Tipo</label>
                          <select
                            className="form-select"
                            value={itemType}
                            onChange={(e) => setItemType(e.target.value as "producto" | "oferta")}
                          >
                            <option value="producto">Producto</option>
                            <option value="oferta">Oferta</option>
                          </select>
                        </div>

                        <div className="form-group">
                          <label>
                            {itemType === "producto" ? "Producto" : "Oferta"}
                          </label>
                          {/* TODO: Agregar búsqueda/filtrado en selector cuando se optimice UX */}
                          {itemType === "producto" ? (
                            <select
                              className="form-select"
                              value={selectedProductId}
                              onChange={(e) => setSelectedProductId(parseInt(e.target.value))}
                            >
                              <option value={0}>Seleccionar producto...</option>
                              {allProducts.map((product) => (
                                <option key={product.id} value={product.id}>
                                  {product.nombre} - {formatCurrency(product.precios?.[0]?.precio || 0)}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <select
                              className="form-select"
                              value={selectedOfferId}
                              onChange={(e) => setSelectedOfferId(parseInt(e.target.value))}
                            >
                              <option value={0}>Seleccionar oferta...</option>
                              {allOffers.map((offer) => (
                                <option key={offer.id} value={offer.id}>
                                  {offer.nombre} - {formatCurrency(offer.precio)}
                                </option>
                              ))}
                            </select>
                          )}
                        </div>

                        <div className="form-group">
                          <label>Cantidad</label>
                          <input
                            type="number"
                            className="form-input"
                            min="1"
                            max="1000"
                            value={newItemQuantity}
                            onChange={(e) => setNewItemQuantity(parseInt(e.target.value) || 1)}
                          />
                        </div>

                        <div className="form-group">
                          <label>&nbsp;</label>
                          <button className="btn-add-item" onClick={handleAddItem}>
                            + Agregar
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="sale-total-section">
                    <div className="sale-total-row">
                      <span className="sale-total-label">TOTAL:</span>
                      <span className="sale-total-value">
                        {formatCurrency(calculateTotal())}
                      </span>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            <div className="modal-footer">
              <button className="btn-cancel" onClick={onClose} disabled={saving}>
                Cancelar
              </button>
              <button className="btn-save" onClick={handleSave} disabled={saving || loading}>
                {saving ? "Guardando..." : "Guardar Cambios"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SaleEditModal;

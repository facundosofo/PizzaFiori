import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { XIcon, TrashIcon, PlusIcon, MinusIcon } from "./shared/Icons";
import Badge from "./shared/Badge";
import OfferItemForm from "./OfferItemForm";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import type { OfferItemRequest } from "../types/offer_item";
import { createOffer, updateOffer } from "../services/ofertasService";
import { formatCurrency, parseCurrencyInput } from "../utils/formatters";
import "../styles/shared/add-button.css";
import "../styles/shared/quantity-controls.css";
import "../styles/sale-modal.css";
import "../styles/offer-modal.css";

interface OfferModalProps {
  oferta: Offer | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (oferta: Offer) => void;
  productos: Product[];
  categorias: Category[];
}

const OfferModal = ({
  oferta,
  isOpen,
  onClose,
  onSave,
  productos,
  categorias,
}: OfferModalProps) => {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [precio, setPrecio] = useState<number>(0);
  const [precioInput, setPrecioInput] = useState<string>("");
  const [items, setItems] = useState<OfferItemRequest[]>([]);
  const [showItemForm, setShowItemForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (oferta && isOpen) {
      setNombre(oferta.nombre || "");
      setDescripcion(oferta.descripcion || "");
      setPrecio(oferta.precio);
      setPrecioInput(formatCurrency(oferta.precio));
      
      // Map oferta.productos to OfferItemRequest[]
      const mappedItems: OfferItemRequest[] = oferta.productos?.map(item => {
        const request: OfferItemRequest = {
          cantidad: item.cantidad,
        };

        if (item.categoria_id) {
          request.categoria_id = item.categoria_id;
        } else if (item.productos && item.productos.length > 1) {
          request.producto_opciones = item.productos.map(p => p.id);
        } else if (item.productos && item.productos.length === 1) {
          request.producto_id = item.productos[0].id;
        }

        return request;
      }) || [];
      
      setItems(mappedItems);
      setShowItemForm(false);
      setError("");
    } else if (!oferta && isOpen) {
      // Nueva oferta
      setNombre("");
      setDescripcion("");
      setPrecio(0);
      setPrecioInput("");
      setItems([]);
      setShowItemForm(false);
      setError("");
    }
  }, [oferta, isOpen]);

  const handleAddItem = (item: OfferItemRequest) => {
    // Validar si ya existe un item con el mismo producto/categoria/opciones (sin importar cantidad)
    const isDuplicate = items.some((existingItem) => {
      // Comparar producto_id
      if (item.producto_id && existingItem.producto_id) {
        return item.producto_id === existingItem.producto_id;
      }
      
      // Comparar categoria_id
      if (item.categoria_id && existingItem.categoria_id) {
        return item.categoria_id === existingItem.categoria_id;
      }
      
      // Comparar producto_opciones
      if (item.producto_opciones && existingItem.producto_opciones) {
        const sameLength = item.producto_opciones.length === existingItem.producto_opciones.length;
        const sameIds = sameLength && item.producto_opciones.every(id => existingItem.producto_opciones?.includes(id));
        return sameIds;
      }
      
      return false;
    });

    if (isDuplicate) {
      setError("Este item ya existe en la oferta. No se pueden agregar items duplicados.");
      return;
    }

    setItems([...items, item]);
    setShowItemForm(false);
    setError(""); // Limpiar error si había
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleQuantityChange = (index: number, newQuantity: number) => {
    if (newQuantity < 1) return;
    setItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, cantidad: newQuantity } : item))
    );
  };

  const handleSave = async () => {
    setError("");

    // Validaciones
    if (!nombre.trim()) {
      return setError("El nombre es requerido");
    }
    if (nombre.trim().length > 255) {
      return setError("El nombre no puede superar los 255 caracteres");
    }
    if (!precio || precio <= 0) {
      return setError("El precio debe ser mayor a 0");
    }
    if (items.length === 0) {
      return setError("Debes agregar al menos un item a la oferta");
    }

    // Validar que cada item tenga exactamente uno de: producto_id, categoria_id, o producto_opciones
    for (const item of items) {
      const hasProducto = item.producto_id !== undefined && item.producto_id > 0;
      const hasCategoria = item.categoria_id !== undefined && item.categoria_id > 0;
      const hasOpciones = item.producto_opciones !== undefined && item.producto_opciones.length >= 2;
      
      const count = [hasProducto, hasCategoria, hasOpciones].filter(Boolean).length;
      
      if (count !== 1) {
        return setError("Cada item debe tener exactamente un tipo: producto, categoría, o opciones múltiples");
      }
    }

    setLoading(true);
    try {
      const ofertaData = {
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || undefined,
        precio: precio,
        productos: items,
      };

      let savedOferta: Offer;

      if (oferta?.id && oferta.id > 0) {
        savedOferta = await updateOffer(oferta.id, ofertaData);
      } else {
        savedOferta = await createOffer(ofertaData);
      }

      if (onSave) {
        onSave(savedOferta);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar la oferta");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const isEditing = oferta && oferta.id > 0;

  return (
    <AnimatePresence>
      <motion.div
        className="modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="modal-content offer-modal-content"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sale-modal-header">
            <h2>
              {isEditing ? "Editar Oferta" : "Nueva Oferta"}
            </h2>
            <button
              className="sale-modal-close-btn"
              onClick={onClose}
              aria-label="Cerrar"
              disabled={loading}
            >
              <XIcon size={18} />
            </button>
          </div>

          {/* Body */}
          <div className="modal-body">
            {error && <div className="form-error">{error}</div>}

            <div className="offer-form">
              {/* Nombre */}
              <div className="form-group">
                <label htmlFor="offer-nombre">Nombre de la Oferta:</label>
                <input
                  id="offer-nombre"
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="form-input"
                  placeholder="Ej: Promo Pizza Grande"
                  maxLength={255}
                  disabled={loading}
                  autoComplete="off"
                />
                <span className="form-hint">
                  {nombre.length}/255 caracteres
                </span>
              </div>

              {/* Descripción */}
              <div className="form-group">
                <label htmlFor="offer-descripcion">Descripción:</label>
                <textarea
                  id="offer-descripcion"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  className="form-input form-textarea"
                  placeholder="Descripción opcional de la oferta"
                  maxLength={1000}
                  rows={3}
                  disabled={loading}
                  autoComplete="off"
                />
                <span className="form-hint">
                  {descripcion.length}/1000 caracteres
                </span>
              </div>

              {/* Precio */}
              <div className="form-group">
                <label htmlFor="offer-precio">Precio Total:</label>
                <input
                  id="offer-precio"
                  type="text"
                  inputMode="decimal"
                  value={precioInput}
                  onFocus={(e) => {
                    setPrecioInput(precio > 0 ? precio.toString().replace(".", ",") : "");
                    setTimeout(() => e.target.select(), 0);
                  }}
                  onChange={(e) => {
                    let value = e.target.value.replace(".", ",");
                    if (!/^\d*(,\d{0,2})?$/.test(value)) return;

                    setPrecioInput(value);

                    const numeric = parseCurrencyInput(value);
                    if (!isNaN(numeric)) {
                      setPrecio(numeric);
                    }
                  }}
                  onBlur={() => {
                    if (precio > 0) {
                      setPrecioInput(formatCurrency(precio));
                    } else {
                      setPrecioInput("");
                    }
                  }}
                  className="form-input"
                  placeholder="$ 0,00"
                  disabled={loading}
                  autoComplete="off"
                />
              </div>

              {/* Items */}
              <div className="form-group">
                <div className="items-header">
                  <label>Items de la Oferta:</label>
                  {!showItemForm && (
                    <button
                      type="button"
                      className="btn-add-item-header"
                      onClick={() => setShowItemForm(true)}
                      disabled={loading}
                    >
                      <PlusIcon size={16} /> Agregar Item
                    </button>
                  )}
                </div>

                {/* Formulario de nuevo item */}
                {showItemForm && (
                  <OfferItemForm
                    productos={productos}
                    categorias={categorias}
                    onAdd={handleAddItem}
                    onCancel={() => setShowItemForm(false)}
                  />
                )}

                {/* Tabla de items agregados */}
                {items.length > 0 && (
                  <div className="offer-items-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Tipo</th>
                          <th>Detalle</th>
                          <th>Cantidad</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item, index) => {
                          let tipo = "";
                          let detalle = "";
                          
                          if (item.producto_id) {
                            tipo = "Producto";
                            const producto = productos.find(p => p.id === item.producto_id);
                            detalle = producto?.nombre || `ID: ${item.producto_id}`;
                          } else if (item.categoria_id) {
                            tipo = "Categoría";
                            const categoria = categorias.find(c => c.id === item.categoria_id);
                            detalle = categoria?.nombre || `ID: ${item.categoria_id}`;
                          } else if (item.producto_opciones && item.producto_opciones.length > 0) {
                            tipo = "Opciones";
                            const nombres = item.producto_opciones
                              .map(id => productos.find(p => p.id === id)?.nombre || `ID: ${id}`)
                              .join(", ");
                            detalle = `${item.producto_opciones.length} Opciones: ${nombres}`;
                          }

                          return (
                            <tr key={index}>
                              <td>
                                <Badge variant="neutral">
                                  {tipo}
                                </Badge>
                              </td>
                              <td className="item-detail">{detalle}</td>
                              <td className="item-cantidad">
                                <div className="quantity-control" style={{ display: 'inline-flex' }}>
                                  <button
                                    type="button"
                                    className="qty-btn qty-btn-minus"
                                    onClick={() => handleQuantityChange(index, item.cantidad - 1)}
                                    disabled={item.cantidad <= 1 || loading}
                                    aria-label="Disminuir cantidad"
                                  >
                                    <MinusIcon size={14} />
                                  </button>
                                  <input
                                    type="number"
                                    min="1"
                                    max="1000"
                                    className="qty-input"
                                    value={item.cantidad}
                                    onInput={(e) => {
                                      const value = parseInt((e.target as HTMLInputElement).value);
                                      if (!isNaN(value)) {
                                        handleQuantityChange(index, Math.max(1, value));
                                      }
                                    }}
                                    onBlur={(e) => {
                                      const value = parseInt(e.target.value);
                                      if (isNaN(value) || value < 1) {
                                        handleQuantityChange(index, 1);
                                      }
                                    }}
                                    disabled={loading}
                                    aria-label="Cantidad"
                                  />
                                  <button
                                    type="button"
                                    className="qty-btn qty-btn-plus"
                                    onClick={() => handleQuantityChange(index, item.cantidad + 1)}
                                    disabled={item.cantidad >= 1000 || loading}
                                    aria-label="Aumentar cantidad"
                                  >
                                    <PlusIcon size={14} />
                                  </button>
                                </div>
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="item-remove-btn"
                                  onClick={() => handleRemoveItem(index)}
                                  disabled={loading}
                                  title="Eliminar item"
                                >
                                  <TrashIcon />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {items.length === 0 && !showItemForm && (
                  <div className="empty-items-state">
                    <p>No hay items agregados</p>
                    <span className="form-hint">
                      Haz clic en "Agregar Item" para comenzar
                    </span>
                  </div>
                )}
              </div>

              {/* Acciones */}
              <div className="form-actions">
                <button
                  className="form-save-btn"
                  onClick={handleSave}
                  disabled={loading}
                >
                  {loading
                    ? "Guardando..."
                    : isEditing
                    ? "Actualizar Oferta"
                    : "Crear Oferta"}
                </button>
                <button
                  className="form-cancel-btn"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default OfferModal;

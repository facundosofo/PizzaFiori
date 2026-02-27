import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Sale } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import { getSaleById, updateSale } from "../services/salesService";
import { formatCurrency, formatDateTimeDisplay, formatLocalISO } from "../utils/formatters";
import { OfferConfigModal } from "./OfferConfigModal";
import RadioGroup, { type RadioOption } from "./shared/RadioGroup";
import SearchableSelect from "./shared/SearchableSelect";
import "../styles/shared/quantity-controls.css";
import "../styles/shared/add-button.css";
import "../styles/sale-modal.css";
import ErrorAlert from './shared/ErrorAlert';
import * as Icons from './shared/Icons';

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

interface AddProductFormProps {
  selectedProductId: number;
  onSelectProduct: (productId: number) => void;
  products: Product[];
  quantity: number;
  onQuantityChange: (nextValue: number) => void;
  onIncrement: () => void;
  onDecrement: () => void;
}

const AddProductForm = ({
  selectedProductId,
  onSelectProduct,
  products,
  quantity,
  onQuantityChange,
  onIncrement,
  onDecrement,
}: AddProductFormProps) => (
  <>
    <div className="form-group">
      <label>Producto</label>
      <SearchableSelect
        value={selectedProductId}
        onChange={onSelectProduct}
        options={[
          { value: 0, label: "Seleccionar producto..." },
          ...products.map((product) => ({
            value: product.id,
            label: `${product.nombre} - ${formatCurrency(product.precios?.[0]?.precio || 0)}`,
          })),
        ]}
        placeholder="Seleccionar producto..."
        searchPlaceholder="Buscar producto..."
      />
    </div>

    <div className="form-group">
      <label>Cantidad</label>
      <div className="quantity-control">
        <button
          type="button"
          className="qty-btn qty-btn-minus"
          aria-label="Disminuir cantidad"
          onClick={onDecrement}
        >
          <Icons.MinusIcon size={14} />
        </button>
        <input
          type="number"
          min="1"
          max="1000"
          className="qty-input"
          value={quantity}
          onFocus={(e) => e.target.select()}
          onChange={(e) => onQuantityChange(parseInt(e.target.value) || 1)}
        />
        <button
          type="button"
          className="qty-btn qty-btn-plus"
          aria-label="Aumentar cantidad"
          onClick={onIncrement}
        >
          <Icons.PlusIcon size={14} />
        </button>
      </div>
    </div>
  </>
);

interface AddOfferFormProps {
  selectedOfferId: number;
  onSelectOffer: (offerId: number) => void;
  offers: Offer[];
}

const AddOfferForm = ({ selectedOfferId, onSelectOffer, offers }: AddOfferFormProps) => (
  <div className="form-group">
    <label>Oferta</label>
    <SearchableSelect
      value={selectedOfferId}
      onChange={onSelectOffer}
      options={[
        { value: 0, label: "Seleccionar oferta..." },
        ...offers.map((offer) => ({
          value: offer.id,
          label: `${offer.nombre} - ${formatCurrency(offer.precio)}`,
        })),
      ]}
      placeholder="Seleccionar oferta..."
      searchable={false}
    />
  </div>
);

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
  const [editingPriceId, setEditingPriceId] = useState<number | null>(null);

  const toNumber = (value: unknown): number => {
    if (typeof value === "number") return Number.isFinite(value) ? value : 0;
    if (typeof value === "string") {
      const parsed = parseFloat(value);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    if (typeof value === "bigint") return Number(value);
    return 0;
  };

  // Detect if an offer is configurable (has categories or options, not just fixed products)
  const isOfferConfigurable = (offer: Offer): boolean => {
    if (!offer.productos || offer.productos.length === 0) return false;
    
    // An offer is configurable if it has:
    // - At least one item with categoria_id (category-based)
    // - Or at least one item with multiple products (options)
    return offer.productos.some(
      (item) =>
        item.categoria_id !== null && item.categoria_id !== undefined ||
        (item.productos && item.productos.length > 1)
    );
  };

  // Handle offer selection - if configurable, open modal; otherwise mark for direct add
  const handleOfferSelect = (offerId: number) => {
    setSelectedOfferId(offerId);
    setConfiguredProducts([]);
    const offer = activeOffers.find((o) => o.id === offerId);
    if (offer && isOfferConfigurable(offer)) {
      setSelectedOfferForConfig(offer);
      setIsConfigModalOpen(true);
    }
  };

  // Handle confirmation from OfferConfigModal
  const handleConfirmOfferConfig = (
    selectedProducts: { producto_id: number; producto_nombre: string; cantidad: number }[]
  ) => {
    setConfiguredProducts(selectedProducts);
    setIsConfigModalOpen(false);
    setSelectedOfferForConfig(null);
  };

  // Add item state
  const [itemType, setItemType] = useState<"" | "producto" | "oferta">("");
  const [selectedProductId, setSelectedProductId] = useState<number>(0);
  const [selectedOfferId, setSelectedOfferId] = useState<number>(0);
  const [newItemQuantity, setNewItemQuantity] = useState<number>(1);

  const addItemTypeOptions: RadioOption[] = [
    { value: "producto", label: "Producto" },
    { value: "oferta", label: "Oferta" },
  ];

  const activeProducts = allProducts.filter((product) => product.activo);
  const activeOffers = allOffers.filter((offer) => offer.activo);

  // Offer configuration state
  const [selectedOfferForConfig, setSelectedOfferForConfig] = useState<Offer | null>(null);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [configuredProducts, setConfiguredProducts] = useState<
    { producto_id: number; producto_nombre: string; cantidad: number }[]
  >([]);

  useEffect(() => {
    if (saleId && isOpen) {
      const fetchSale = async () => {
        try {
          setLoading(true);
          setError("");
          const data = await getSaleById(saleId);
          setSale(data);
          const normalizedItems =
            (data.items || []).map((item) => {
              const precio_unitario = toNumber((item as any).precio_unitario);
              const cantidad = toNumber((item as any).cantidad) || 0;
              const subtotal = toNumber((item as any).subtotal);
              return {
                ...item,
                precio_unitario,
                cantidad,
                subtotal: subtotal || precio_unitario * cantidad,
              };
            });
          setEditedItems(normalizedItems);
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "Error desconocido";
          setError(errorMessage);
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
          const precio = toNumber((item as any).precio_unitario);
          const subtotal = precio * newQuantity;
          return { ...item, cantidad: newQuantity, precio_unitario: precio, subtotal };
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
          const cantidad = toNumber((item as any).cantidad);
          const subtotal = newPrice * cantidad;
          return { ...item, cantidad, precio_unitario: newPrice, subtotal };
        }
        return item;
      })
    );
  };

  const handleRemoveItem = (itemId: number) => {
    setEditedItems((prev) => prev.filter((item) => item.id !== itemId));
  };

  const handleNewItemQuantityChange = (change: number) => {
    const newQuantity = newItemQuantity + change;
    if (newQuantity >= 1 && newQuantity <= 1000) {
      setNewItemQuantity(newQuantity);
    }
  };

  useEffect(() => {
    setSelectedProductId(0);
    setSelectedOfferId(0);
    setNewItemQuantity(1);
    setConfiguredProducts([]);
  }, [itemType]);

  const isAddDisabled =
    !itemType ||
    (itemType === "producto" && selectedProductId === 0) ||
    (itemType === "oferta" && (
      selectedOfferId === 0 ||
      (selectedOfferId > 0 &&
        isOfferConfigurable(activeOffers.find((o) => o.id === selectedOfferId)!) &&
        configuredProducts.length === 0)
    ));

  const handleAddItem = () => {
    if (!itemType) {
      setError("Selecciona si es producto u oferta");
      return;
    }
    if (itemType === "producto" && selectedProductId === 0) {
      setError("Selecciona un producto");
      return;
    }
    if (itemType === "oferta" && selectedOfferId === 0) {
      setError("Selecciona una oferta");
      return;
    }

    const quantityToUse = itemType === "producto" ? newItemQuantity : 1;
    if (itemType === "producto" && (quantityToUse < 1 || quantityToUse > 1000)) {
      setError("Cantidad debe ser entre 1 y 1000");
      return;
    }

    setError("");

    let itemName = "";
    let precio = 0;
    let itemCategoria = "";
    let itemDescripcion: string | undefined;
    let productosSeleccionados: { producto_id: number; cantidad: number }[] = [];

    if (itemType === "producto") {
      const product = activeProducts.find((p) => p.id === selectedProductId);
      if (product) {
        itemName = product.nombre;
        itemCategoria = product.categoria?.nombre || "Sin categoría";
        // Get price for quantity 1 (default price)
        const defaultPrice = product.precios?.find((p) => p.cantidad === 1);
        precio = defaultPrice?.precio || 0;
      }
    } else {
      const offer = activeOffers.find((o) => o.id === selectedOfferId);
      if (offer) {
        itemName = offer.nombre;
        itemCategoria = "Ofertas";
        itemDescripcion = offer.descripcion || undefined;
        precio = offer.precio;

        // Handle product selection for configurable offers
        if (isOfferConfigurable(offer)) {
          // For configurable offers, use the configured products
          if (configuredProducts.length === 0) {
            setError("Completa la configuración de la oferta");
            return;
          }
          productosSeleccionados = configuredProducts.map((p) => ({
            producto_id: p.producto_id,
            cantidad: p.cantidad,
          }));
        } else {
          // For fixed offers, extract fixed products
          productosSeleccionados = offer.productos?.flatMap((item) => {
            if (item.productos && item.productos.length === 1) {
              // Fixed product
              return [{
                producto_id: item.productos[0].id,
                cantidad: item.cantidad,
              }];
            }
            return [];
          }) || [];
        }
      }
    }

    const newItem: SaleItemWithDetails = {
      id: Date.now(), // Temporary ID for new items
      producto_id: itemType === "producto" ? selectedProductId : null,
      oferta_id: itemType === "oferta" ? selectedOfferId : null,
      cantidad: quantityToUse,
      precio_unitario: precio,
      subtotal: precio * quantityToUse,
      item_nombre: itemName,
      item_categoria: itemCategoria,
      item_descripcion: itemDescripcion,
      producto_nombre: itemType === "producto" ? itemName : undefined, // Deprecated
      oferta_nombre: itemType === "oferta" ? itemName : undefined, // Deprecated
      oferta_productos_snapshot: productosSeleccionados.map((p) => ({
        id: p.producto_id,
        producto_id: p.producto_id,
        producto_nombre: allProducts.find((prod) => prod.id === p.producto_id)?.nombre || "",
        cantidad: p.cantidad,
      })),
    };

    setEditedItems((prev) => [...prev, newItem]);

    // Reset form
    setSelectedProductId(0);
    setSelectedOfferId(0);
    setNewItemQuantity(1);
    setConfiguredProducts([]);
  };

  const calculateTotal = (): number => {
    return editedItems.reduce((sum, item) => sum + toNumber((item as any).subtotal), 0);
  };

  const handleSave = async () => {
    if (editedItems.length === 0) {
      setError("La venta debe tener al menos un item");
      return;
    }

    try {
      setSaving(true);
      setError("");

      // Call update service with precio_unitario and productos_seleccionados for offers
      await updateSale(saleId!, {
        items: editedItems.map((item) => ({
          producto_id: item.producto_id || undefined,
          oferta_id: item.oferta_id || undefined,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario, // Incluir precio_unitario
          productos_seleccionados: item.oferta_productos_snapshot?.map((p) => ({
            producto_id: p.producto_id || p.id,
            cantidad: p.cantidad,
          })) || undefined,
        })),
      });

      // Create updated sale object for parent component
      const updatedSale: Sale = {
        ...sale!,
        items: editedItems,
        total: calculateTotal(),
        fecha_actualizacion: formatLocalISO(new Date()),
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
                <Icons.XIcon size={18} />
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
                    <Icons.SpinnerIcon size={36} />
                  </motion.div>
                  <p>Cargando detalles...</p>
                </div>
              ) : error ? (
                <div className="sale-detail-error">
                  <ErrorAlert message={error} onClose={() => setError("")} />
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
                        {formatDateTimeDisplay(sale.fecha_creacion)}
                      </span>
                    </div>
                  </div>

                  <div className="sale-items-section">
                    <h3>Editar Items</h3>
                    <div className="sale-items-table">
                      <div className="sale-items-header">
                        <div className="sale-item-col-name">Nombre</div>
                        <div className="sale-item-col-qty">Cantidad</div>
                        <div className="sale-item-col-price">Precio unitario</div>
                        <div className="sale-item-col-subtotal">Subtotal</div>
                        <div className="sale-item-col-actions">Acción</div>
                      </div>

                      {editedItems.map((item) => (
                        <div key={item.id} className="sale-items-row">
                          <div className="sale-item-col-name">
                            {item.item_nombre}
                            {item.item_descripcion && (
                              <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: "0.85rem", marginTop: 2 }}>
                                {item.item_descripcion}
                              </div>
                            )}

                            {item.oferta_id && item.oferta_productos_snapshot?.length ? (
                              <div style={{ marginTop: 6, paddingLeft: 14 }}>
                                {item.oferta_productos_snapshot.map((p) => (
                                  <div key={p.id} style={{ color: "rgba(255, 255, 255, 0.75)", fontSize: "0.9rem", fontWeight: 600 }}>
                                    - {p.cantidad * item.cantidad} {p.producto_nombre}
                                  </div>
                                ))}
                              </div>
                            ) : null}
                          </div>
                          <div className="sale-item-col-qty">
                            <div className="quantity-control">
                              <button
                                type="button"
                                className="qty-btn qty-btn-minus"
                                aria-label="Disminuir cantidad"
                                onClick={() => handleQuantityChange(item.id, item.cantidad - 1)}
                                disabled={saving || loading}
                              >
                                <Icons.MinusIcon size={14} />
                              </button>
                              <input
                                type="number"
                                min="1"
                                max="1000"
                                className="qty-input"
                                value={item.cantidad}
                                onFocus={(e) => e.target.select()}
                                onChange={(e) =>
                                  handleQuantityChange(item.id, parseInt(e.target.value) || 1)
                                }
                                disabled={saving || loading}
                              />
                              <button
                                type="button"
                                className="qty-btn qty-btn-plus"
                                aria-label="Aumentar cantidad"
                                onClick={() => handleQuantityChange(item.id, item.cantidad + 1)}
                                disabled={saving || loading}
                              >
                                <Icons.PlusIcon size={14} />
                              </button>
                            </div>
                          </div>
                          <div className="sale-item-col-price">
                            <input
                              type="text"
                              className="qty-input price-input"
                              value={
                                editingPriceId === item.id
                                  ? item.precio_unitario
                                  : formatCurrency(item.precio_unitario)
                              }
                              onFocus={(e) => {
                                setEditingPriceId(item.id);
                                e.target.select();
                              }}
                              onChange={(e) => {
                                const value = parseFloat(e.target.value) || 0;
                                handlePriceChange(item.id, value);
                              }}
                              onBlur={() => {
                                setEditingPriceId(null);
                              }}
                              disabled={saving || loading}
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
                              <Icons.TrashIcon size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="add-item-section-wrapper">
                    <h3>Agregar Item</h3>
                    <div className="add-item-section">
                      <div className="add-item-form">
                        <div className="add-item-type-section">
                          <RadioGroup
                            name="sale-add-item-type"
                            options={addItemTypeOptions}
                            value={itemType}
                            onChange={(value) => setItemType(value as "" | "producto" | "oferta")}
                          />
                        </div>

                        <AnimatePresence mode="wait" initial={false}>
                          {itemType && (
                            <motion.div
                              key={`add-${itemType}`}
                              className={`add-item-fields-section ${itemType === "producto" ? "product-fields" : "offer-fields"}`}
                              initial={{ opacity: 0, y: 6 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -6 }}
                              transition={{ duration: 0.18 }}
                            >
                              {itemType === "producto" ? (
                                <AddProductForm
                                  selectedProductId={selectedProductId}
                                  onSelectProduct={setSelectedProductId}
                                  products={activeProducts}
                                  quantity={newItemQuantity}
                                  onQuantityChange={setNewItemQuantity}
                                  onIncrement={() => handleNewItemQuantityChange(1)}
                                  onDecrement={() => handleNewItemQuantityChange(-1)}
                                />
                              ) : (
                                <AddOfferForm
                                  selectedOfferId={selectedOfferId}
                                  onSelectOffer={handleOfferSelect}
                                  offers={activeOffers}
                                />
                              )}

                              <div className="form-group add-item-action-group">
                                <label>&nbsp;</label>
                                <button
                                  className="btn-add-item"
                                  onClick={handleAddItem}
                                  disabled={isAddDisabled}
                                >
                                  <Icons.PlusIcon size={16} /> Agregar
                                </button>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
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

            <div className="sales-modal-footer">
              <button className="sales-btn-cancel" onClick={onClose} disabled={saving}>
                Cancelar
              </button>
              <button className="sales-btn-save" onClick={handleSave} disabled={saving || loading || editedItems.length === 0}>
                {saving ? "Guardando..." : "Guardar Cambios"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Offer Configuration Modal */}
      {selectedOfferForConfig && (
        <OfferConfigModal
          isOpen={isConfigModalOpen}
          offer={selectedOfferForConfig}
          products={activeProducts}
          onConfirm={handleConfirmOfferConfig}
          onClose={() => {
            setIsConfigModalOpen(false);
            setSelectedOfferForConfig(null);
            setSelectedOfferId(0);
          }}
        />
      )}
    </AnimatePresence>
  );
};

export default SaleEditModal;

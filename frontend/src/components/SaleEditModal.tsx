import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Sale } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import { getSaleById, updateSale } from "../services/salesService";
import { getRecargoConfig } from "../services/configService";
import { formatCurrency, formatDateTimeDisplay } from "../utils/formatters";
import { OfferConfigModal } from "./OfferConfigModal";
import RadioGroup, { type RadioOption } from "./shared/RadioGroup";
import SearchableSelect, { type SelectOption } from "./shared/SearchableSelect";
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
  selectedPriceOptionId: number;
  onSelectPriceOption: (priceOptionId: number) => void;
  priceOptions: SelectOption[];
  quantityMax: number;
  quantityHint?: string;
  quantity: number;
  onQuantityChange: (nextValue: number) => void;
  onIncrement: () => void;
  onDecrement: () => void;
}

const AddProductForm = ({
  selectedProductId,
  onSelectProduct,
  products,
  selectedPriceOptionId,
  onSelectPriceOption,
  priceOptions,
  quantityMax,
  quantityHint,
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

      {selectedProductId > 0 && priceOptions.length > 0 && (
        <div className="add-item-price-selector">
          <label>Tipo de Precio</label>
          <SearchableSelect
            value={selectedPriceOptionId}
            onChange={onSelectPriceOption}
            options={priceOptions}
            placeholder="Seleccionar tipo de precio..."
            searchable={false}
          />
        </div>
      )}
    </div>

    <div className="form-group add-item-qty-group">
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
          max={quantityMax}
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
      {quantityHint && <span className="add-item-quantity-hint">{quantityHint}</span>}
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
  const [applyRecargo, setApplyRecargo] = useState(false);
  const [recargoPercent, setRecargoPercent] = useState(10);
  const [recargoAmount, setRecargoAmount] = useState(0);

  const toNumber = (value: unknown): number => {
    if (typeof value === "number") return Number.isFinite(value) ? value : 0;
    if (typeof value === "string") {
      const parsed = parseFloat(value);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    if (typeof value === "bigint") return Number(value);
    return 0;
  };

  const isSameQuantity = (a: number, b: number): boolean => Math.abs(a - b) < 1e-9;

  const getPortionLabel = (baseQuantity?: number | null): string => {
    const value = toNumber(baseQuantity);
    if (isSameQuantity(value, 0.5)) return "1/2";
    if (isSameQuantity(value, 0.25)) return "1/4";
    if (isSameQuantity(value, 0.125)) return "1/8";
    return "";
  };

  const isPortionItem = (item: SaleItemWithDetails): boolean => {
    const baseQuantity = toNumber((item as any).precio_cantidad);
    return baseQuantity > 0 && baseQuantity < 1;
  };

  const getQuantityStep = (item: SaleItemWithDetails): number => {
    if (isPortionItem(item)) {
      return toNumber((item as any).precio_cantidad);
    }
    return 1;
  };

  const getDisplayQuantity = (item: SaleItemWithDetails): number => {
    const quantity = toNumber((item as any).cantidad);
    const step = getQuantityStep(item);
    if (isPortionItem(item)) {
      return Math.max(1, Math.round(quantity / step));
    }
    return Math.round(quantity);
  };

  const getFractionLabel = (cantidad: number): string => {
    if (isSameQuantity(cantidad, 0.5)) return "1/2";
    if (isSameQuantity(cantidad, 0.25)) return "1/4";
    if (isSameQuantity(cantidad, 0.125)) return "1/8";
    return `${cantidad}`;
  };

  const getMaxQuantityForPortionPrice = (priceCantidad?: number): number | null => {
    if (!priceCantidad || priceCantidad >= 1) return null;
    const maxQuantity = Math.round(1 / priceCantidad) - 1;
    return Number.isFinite(maxQuantity) && maxQuantity > 0 ? maxQuantity : null;
  };

  const getMaxPortionActualQuantity = (priceCantidad?: number): number | null => {
    const maxPortionCount = getMaxQuantityForPortionPrice(priceCantidad);
    if (!priceCantidad || priceCantidad >= 1 || maxPortionCount === null) return null;
    return Number((maxPortionCount * priceCantidad).toFixed(3));
  };

  const getSelectableProductPriceRows = (product: Product) => {
    if (!product.precios || product.precios.length === 0) return [];
    return [...product.precios]
      .filter((price) => Number(price.cantidad) <= 1)
      .sort((a, b) => Number(b.cantidad) - Number(a.cantidad));
  };

  const getDefaultProductPriceRow = (product: Product) => {
    const rows = getSelectableProductPriceRows(product);
    return rows.find((row) => isSameQuantity(Number(row.cantidad), 1)) ?? rows[0];
  };

  const buildProductPriceOptions = (product: Product): SelectOption[] => {
    return getSelectableProductPriceRows(product).map((row) => {
      const amount = formatCurrency(Number(row.precio));
      if (Number(row.cantidad) < 1) {
        return {
          value: row.id,
          label: `Porción ${getFractionLabel(Number(row.cantidad))} - ${amount}`,
        };
      }

      return {
        value: row.id,
        label: `Unidad entera - ${amount}`,
      };
    });
  };

  const getDisplayPrice = (item: SaleItemWithDetails): number => {
    const unitPrice = toNumber((item as any).precio_unitario);
    if (!isPortionItem(item)) return unitPrice;

    const baseQuantity = getQuantityStep(item);
    if (baseQuantity <= 0) return unitPrice;

    return unitPrice * baseQuantity;
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
  const [selectedProductPriceId, setSelectedProductPriceId] = useState<number>(0);
  const [selectedOfferId, setSelectedOfferId] = useState<number>(0);
  const [newItemQuantity, setNewItemQuantity] = useState<number>(1);

  const addItemTypeOptions: RadioOption[] = [
    { value: "producto", label: "Producto" },
    { value: "oferta", label: "Oferta" },
  ];

  const activeProducts = allProducts.filter((product) => product.activo);
  const activeOffers = allOffers.filter((offer) => offer.activo);
  const selectedProduct = activeProducts.find((p) => p.id === selectedProductId);
  const selectedProductPriceOptions = selectedProduct ? buildProductPriceOptions(selectedProduct) : [];
  const selectedProductPriceRow = selectedProduct
    ? getSelectableProductPriceRows(selectedProduct).find((price) => price.id === selectedProductPriceId)
      ?? getDefaultProductPriceRow(selectedProduct)
    : undefined;
  const selectedProductPortionLabel = selectedProductPriceRow && Number(selectedProductPriceRow.cantidad) < 1
    ? getFractionLabel(Number(selectedProductPriceRow.cantidad))
    : undefined;
  const addProductMaxQuantity = selectedProductPriceRow
    ? getMaxQuantityForPortionPrice(Number(selectedProductPriceRow.cantidad)) ?? 1000
    : 1000;

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
          let configPercent = 10;

          try {
            const recargoConfig = await getRecargoConfig();
            if (recargoConfig?.porcentaje_recargo !== undefined) {
              configPercent = recargoConfig.porcentaje_recargo;
            }
          } catch (configError) {
            configPercent = Number(data.porcentaje_recargo ?? 10);
          }

          setSale(data);
          setApplyRecargo(Boolean(data.porcentaje_recargo));
          setRecargoPercent(configPercent);

          const normalizedItems =
            (data.items || []).map((item) => {
              const precio_unitario = toNumber((item as any).precio_unitario);
              const cantidad = toNumber((item as any).cantidad) || 0;
              const subtotal = toNumber((item as any).subtotal);
              return {
                ...item,
                precio_unitario,
                cantidad,
                precio_cantidad: (item as any).precio_cantidad !== undefined && (item as any).precio_cantidad !== null
                  ? toNumber((item as any).precio_cantidad)
                  : undefined,
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
    const targetItem = editedItems.find((item) => item.id === itemId);
    if (!targetItem) return;

    const step = getQuantityStep(targetItem);
    const minQuantity = step;
    const maxQuantity = isPortionItem(targetItem)
      ? getMaxPortionActualQuantity(step) ?? 1000
      : 1000;
    const boundedQuantity = Math.max(minQuantity, Math.min(newQuantity, maxQuantity));

    if (boundedQuantity < minQuantity || boundedQuantity > 1000) return;

    setEditedItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const precio = toNumber((item as any).precio_unitario);
          const subtotal = precio * boundedQuantity;
          return { ...item, cantidad: boundedQuantity, precio_unitario: precio, subtotal };
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
          const effectiveUnitPrice = isPortionItem(item)
            ? newPrice / Math.max(getQuantityStep(item), 0.000001)
            : newPrice;
          const subtotal = effectiveUnitPrice * cantidad;
          return { ...item, cantidad, precio_unitario: effectiveUnitPrice, subtotal };
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
    const boundedQuantity = Math.max(1, Math.min(newQuantity, addProductMaxQuantity));
    setNewItemQuantity(boundedQuantity);
  };

  const handleNewItemQuantityInput = (nextValue: number) => {
    const parsed = Number.isFinite(nextValue) ? Math.floor(nextValue) : 1;
    const boundedQuantity = Math.max(1, Math.min(parsed || 1, addProductMaxQuantity));
    setNewItemQuantity(boundedQuantity);
  };

  useEffect(() => {
    setSelectedProductId(0);
    setSelectedProductPriceId(0);
    setSelectedOfferId(0);
    setNewItemQuantity(1);
    setConfiguredProducts([]);
  }, [itemType]);

  useEffect(() => {
    if (itemType !== "producto") return;

    if (!selectedProduct) {
      setSelectedProductPriceId(0);
      return;
    }

    const availableRows = getSelectableProductPriceRows(selectedProduct);
    if (!availableRows.length) {
      setSelectedProductPriceId(0);
      return;
    }

    if (!availableRows.some((row) => row.id === selectedProductPriceId)) {
      setSelectedProductPriceId(availableRows[0].id);
      setNewItemQuantity(1);
    }
  }, [itemType, selectedProductId, selectedProduct, selectedProductPriceId]);

  useEffect(() => {
    setNewItemQuantity((prev) => Math.max(1, Math.min(prev, addProductMaxQuantity)));
  }, [addProductMaxQuantity]);

  const isAddDisabled =
    !itemType ||
    (itemType === "producto" && (selectedProductId === 0 || !selectedProductPriceRow)) ||
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

    let quantityToUse = itemType === "producto" ? newItemQuantity : 1;
    let priceQuantityToUse: number | null = itemType === "producto" ? 1 : null;

    if (itemType === "producto" && (quantityToUse < 1 || quantityToUse > addProductMaxQuantity * Number(priceQuantityToUse ?? 1))) {
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

        const selectedPrice = getSelectableProductPriceRows(product).find((p) => p.id === selectedProductPriceId)
          ?? getDefaultProductPriceRow(product);

        const selectedCantidad = Number(selectedPrice?.cantidad ?? 1);
        const selectedPrecio = Number(selectedPrice?.precio ?? 0);

        priceQuantityToUse = selectedCantidad;
        quantityToUse = Number((selectedCantidad * newItemQuantity).toFixed(3));

        precio = selectedCantidad > 0
          ? Number((selectedPrecio / selectedCantidad).toFixed(3))
          : selectedPrecio;
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
      precio_cantidad: itemType === "producto" ? priceQuantityToUse ?? 1 : null,
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

    if (itemType === "producto" && newItem.producto_id !== null && newItem.precio_cantidad) {
      const duplicateItem = editedItems.find((item) =>
        item.producto_id === newItem.producto_id &&
        toNumber((item as any).precio_cantidad) > 0 &&
        isSameQuantity(toNumber((item as any).precio_cantidad), toNumber(newItem.precio_cantidad))
      );

      if (duplicateItem) {
        const maxActualQuantity = getMaxPortionActualQuantity(toNumber(newItem.precio_cantidad));
        const currentQuantity = toNumber((duplicateItem as any).cantidad);
        const nextQuantity = Number((currentQuantity + newItem.cantidad).toFixed(3));

        if (maxActualQuantity !== null && nextQuantity > maxActualQuantity + 1e-9) {
          setError(`No puedes superar ${getMaxQuantityForPortionPrice(toNumber(newItem.precio_cantidad))} porciones de ${getPortionLabel(toNumber(newItem.precio_cantidad))}`);
          return;
        }
      }
    }

    setEditedItems((prev) => {
      if (itemType === "producto" && newItem.producto_id !== null) {
        const duplicateIndex = prev.findIndex((item) =>
          item.producto_id === newItem.producto_id &&
          toNumber((item as any).precio_cantidad) > 0 &&
          isSameQuantity(toNumber((item as any).precio_cantidad), toNumber(newItem.precio_cantidad))
        );

        if (duplicateIndex >= 0) {
          const currentQuantity = toNumber((prev[duplicateIndex] as any).cantidad);
          const nextQuantity = Number((currentQuantity + newItem.cantidad).toFixed(3));

          return prev.map((item, index) => {
            if (index !== duplicateIndex) return item;

            const currentSubtotal = toNumber((item as any).subtotal);

            return {
              ...item,
              cantidad: nextQuantity,
              subtotal: Number((currentSubtotal + newItem.subtotal).toFixed(2)),
            };
          });
        }
      }

      return [...prev, newItem];
    });

    // Reset form
    setSelectedProductId(0);
    setSelectedOfferId(0);
    setNewItemQuantity(1);
    setConfiguredProducts([]);
  };

  const calculateTotal = (): number => {
    return editedItems.reduce((sum, item) => sum + toNumber((item as any).subtotal), 0);
  };

  useEffect(() => {
    const subtotal = calculateTotal();
    const surcharge = applyRecargo ? parseFloat(((subtotal * recargoPercent) / 100).toFixed(2)) : 0;
    setRecargoAmount(surcharge);
  }, [editedItems, applyRecargo, recargoPercent]);

  const handleSave = async () => {
    if (editedItems.length === 0) {
      setError("La venta debe tener al menos un item");
      return;
    }

    try {
      setSaving(true);
      setError("");

      // Call update service with precio_unitario and productos_seleccionados for offers
      const updatedSale = await updateSale(saleId!, {
        items: editedItems.map((item) => ({
          producto_id: item.producto_id || undefined,
          oferta_id: item.oferta_id || undefined,
          cantidad: item.cantidad,
          precio_cantidad: item.precio_cantidad ?? undefined,
          precio_unitario: item.precio_unitario, // Incluir precio_unitario
          productos_seleccionados: item.oferta_productos_snapshot?.map((p) => ({
            producto_id: p.producto_id || p.id,
            cantidad: p.cantidad,
          })) || undefined,
        })),
        aplicar_recargo: applyRecargo,
      });

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
                        <div className="sale-item-col-price">Precio</div>
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
                            {(() => {
                              const portionItem = isPortionItem(item);
                              const step = getQuantityStep(item);
                              const displayQuantity = getDisplayQuantity(item);
                              const minDisplayQuantity = 1;

                              return (
                            <div className="quantity-control">
                              <button
                                type="button"
                                className="qty-btn qty-btn-minus"
                                aria-label="Disminuir cantidad"
                                onClick={() =>
                                  handleQuantityChange(
                                    item.id,
                                    portionItem ? Math.max(step, (displayQuantity - 1) * step) : item.cantidad - 1
                                  )
                                }
                                disabled={saving || loading || displayQuantity <= minDisplayQuantity}
                              >
                                <Icons.MinusIcon size={14} />
                              </button>
                              <input
                                type="number"
                                min="1"
                                max={portionItem ? Math.floor(1000 / step).toString() : "1000"}
                                className="qty-input"
                                value={portionItem ? displayQuantity : item.cantidad}
                                onFocus={(e) => e.target.select()}
                                onChange={(e) =>
                                  handleQuantityChange(
                                    item.id,
                                    portionItem
                                      ? Math.max(1, parseInt(e.target.value, 10) || 1) * step
                                      : parseInt(e.target.value, 10) || 1
                                  )
                                }
                                disabled={saving || loading}
                              />
                              <button
                                type="button"
                                className="qty-btn qty-btn-plus"
                                aria-label="Aumentar cantidad"
                                onClick={() =>
                                  handleQuantityChange(
                                    item.id,
                                    portionItem ? (displayQuantity + 1) * step : item.cantidad + 1
                                  )
                                }
                                disabled={saving || loading}
                              >
                                <Icons.PlusIcon size={14} />
                              </button>
                            </div>
                              );
                            })()}
                            {isPortionItem(item) && (
                              <span className="sale-item-fraction-label">
                                Porciones de {getPortionLabel((item as any).precio_cantidad)}
                              </span>
                            )}
                          </div>
                          <div className="sale-item-col-price">
                            <input
                              type="text"
                              className="qty-input price-input"
                              value={
                                editingPriceId === item.id
                                  ? getDisplayPrice(item)
                                  : formatCurrency(getDisplayPrice(item))
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

                  <div className="sale-recargo-and-total-section">
                    <div className="sale-recargo-controls">
                      <label className="sale-recargo-checkbox">
                        <input
                          type="checkbox"
                          checked={applyRecargo}
                          onChange={() => setApplyRecargo((prev) => !prev)}
                          disabled={saving || loading}
                        />
                        Aplicar recargo por transferencia/débito
                      </label>
                      {!applyRecargo && (
                        <span className="recargo-status-off">Sin recargo</span>
                      )}
                    </div>
                    {applyRecargo && (
                      <div className="sale-recargo-summary">
                        <span className="recargo-label">Recargo ({recargoPercent}%):</span>
                        <span className="recargo-amount">{formatCurrency(recargoAmount)}</span>
                      </div>
                    )}
                    <div className="sale-total-row">
                      <span className="sale-total-label">TOTAL:</span>
                      <span className="sale-total-value">
                        {formatCurrency(calculateTotal() + recargoAmount)}
                      </span>
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
                                  selectedPriceOptionId={selectedProductPriceId}
                                  onSelectPriceOption={setSelectedProductPriceId}
                                  priceOptions={selectedProductPriceOptions}
                                  quantityMax={addProductMaxQuantity}
                                  quantityHint={selectedProductPortionLabel ? `Porciones de ${selectedProductPortionLabel}` : undefined}
                                  quantity={newItemQuantity}
                                  onQuantityChange={handleNewItemQuantityInput}
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
                                <label className="add-item-action-label">Accion</label>
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

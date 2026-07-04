import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ProductQuickSelector } from '../components/ProductQuickSelector';
import { OfferQuickSelector } from '../components/OfferQuickSelector';
import { OfferConfigModal } from '../components/OfferConfigModal';
import { PizzaMitadMitadModal } from '../components/PizzaMitadMitadModal';
import { CartDrawer } from '../components/CartDrawer';
import ErrorAlert from '../components/shared/ErrorAlert';
import SkeletonLoader from '../components/shared/SkeletonLoader';
import * as Icons from '../components/shared/Icons';
import { getProductos } from '../services/productsService';
import { getProductosCategorias } from '../services/productosCategoriasService';
import { getOfertas } from '../services/ofertasService';
import { createSale } from '../services/salesService';
import { getRecargoConfig } from '../services/configService';
import type { Product } from '../types/product';
import type { ProductoCategoria } from '../types/product_category';
import type { Offer } from '../types/offer';
import type { CartItem, CartProductItem, CartOfferItem, CartPizzaMitadMitadItem } from '../types/cart';
import type { SaleItemRequest } from '../types/sale_item';
import '../styles/sales-create.css';

const STALE_MS = 60_000; // 1 minute: don't refetch on window focus if data is fresh

export const SalesCreatePage: React.FC = () => {
  // Data states
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<ProductoCategoria[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cart state
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartTotal, setCartTotal] = useState(0);
  const [recargoPercent, setRecargoPercent] = useState(10);
  const [recargoAmount, setRecargoAmount] = useState(0);

  // UI states
  const [isConfirming, setIsConfirming] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [aplicarRecargo, setAplicarRecargo] = useState(false);
  const [activeTab, setActiveTab] = useState<'productos' | 'ofertas'>('productos');
  const [addedItemToast, setAddedItemToast] = useState<string | null>(null);

  // Modal states for configurable offers
  const [selectedOfferForConfig, setSelectedOfferForConfig] = useState<Offer | null>(null);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  // Modal states for pizza mitad-mitad
  const [isPizzaMitadMitadModalOpen, setIsPizzaMitadMitadModalOpen] = useState(false);

  // Timestamp of last successful fetch (used to skip redundant focus refetches)
  const lastFetchRef = useRef<number>(0);

  // Load products and categories
  const fetchData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);

      const [productsData, categoriesData, offersData, recargoConfig] = await Promise.all([
        getProductos(),
        getProductosCategorias(true),
        getOfertas(),
        getRecargoConfig(),
      ]);

      // Filter only active products and offers
      const activeProducts = productsData.filter((p) => p.activo);
      const activeOffers = offersData.filter((o) => o.activo);
      setProducts(activeProducts);
      setCategories(categoriesData);
      setOffers(activeOffers);
      setRecargoPercent(recargoConfig?.porcentaje_recargo ?? 10);
      lastFetchRef.current = Date.now();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al cargar datos';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refetch data when window gains focus (handles updates from other tabs)
  // Throttled: only fetches if data is older than STALE_MS to avoid redundant requests
  useEffect(() => {
    const handleFocus = () => {
      if (!loading && Date.now() - lastFetchRef.current > STALE_MS) {
        fetchData();
      }
    };

    window.addEventListener('focus', handleFocus);

    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchData, loading]);

  // Calculate cart total whenever items or surcharge settings change
  useEffect(() => {
    const subtotal = cartItems.reduce((sum, item) => sum + item.subtotal, 0);
    const surcharge = aplicarRecargo ? parseFloat(((subtotal * recargoPercent) / 100).toFixed(2)) : 0;
    setRecargoAmount(surcharge);
    setCartTotal(parseFloat((subtotal + surcharge).toFixed(2)));
  }, [cartItems, aplicarRecargo, recargoPercent]);

  // Get product price based on quantity (using range system like backend)
  // Example: 7 empanadas with prices:
  // - 1 unit: $1200
  // - 6 units: $6000
  // - 12 units: $10800
  // Calculation for 7:
  // - First 6 at 6-unit price: $6000
  // - 7th at 1-unit price: $1200
  // - Total: $7200
  // - Average unit price: $7200/7 ≈ $1028.57
  const getProductPrice = (product: Product, quantity: number = 1): number => {
    if (!product.precios || product.precios.length === 0) return 0;

    // Sort prices by cantidad descending
    const sortedPrices = [...product.precios].sort((a, b) => b.cantidad - a.cantidad);

    let remainingQty = quantity;
    let totalPrice = 0;

    // Apply ranges from largest to smallest
    for (const priceRange of sortedPrices) {
      if (remainingQty >= priceRange.cantidad) {
        // How many complete ranges fit
        const times = Math.floor(remainingQty / priceRange.cantidad);
        totalPrice += Number(priceRange.precio) * times;
        remainingQty = remainingQty % priceRange.cantidad;

        if (remainingQty === 0) break;
      }
    }

    // If units remain, apply the smallest range price
    if (remainingQty > 0) {
      const minPriceRange = sortedPrices[sortedPrices.length - 1];
      const unitPrice = Number(minPriceRange.precio) / minPriceRange.cantidad;
      totalPrice += unitPrice * remainingQty;
    }

    // Return average unit price (for compatibility with cart logic)
    return totalPrice / quantity;
  };

  // Get cart quantities map for ProductQuickSelector (memoized).
  // If a product has both whole and portion entries, sum them so the badge shows total.
  const cartQuantities = useMemo(() => {
    const quantities = new Map<number, number>();
    cartItems.forEach((item) => {
      if (item.tipo === 'producto') {
        quantities.set(
          item.producto_id,
          (quantities.get(item.producto_id) || 0) + item.cantidad,
        );
      }
    });
    return quantities;
  }, [cartItems]);

  const isSameCantidad = (a: number, b: number) => Math.abs(a - b) < 1e-9;

  const getMaxQuantityForPortionPrice = (priceCantidad?: number) => {
    if (!priceCantidad || priceCantidad >= 1) return null;

    const maxQuantity = Math.round(1 / priceCantidad) - 1;
    return Number.isFinite(maxQuantity) && maxQuantity > 0 ? maxQuantity : null;
  };

  const getWholeProductPriceRow = (product: Product) => {
    if (!product.precios || product.precios.length === 0) return undefined;
    return (
      product.precios.find((price) => isSameCantidad(price.cantidad, 1))
      ?? product.precios.find((price) => price.cantidad > 1)
      ?? product.precios[0]
    );
  };

  const getPortionProductPriceRow = (product: Product) => {
    return product.precios
      ?.filter((price) => price.cantidad < 1)
      .sort((a, b) => a.cantidad - b.cantidad)[0];
  };

  const addProductPriceItem = useCallback((product: Product, priceRow: NonNullable<Product['precios']>[number]) => {
    const maxQuantity = getMaxQuantityForPortionPrice(Number(priceRow.cantidad));
    let didChangeCart = false;

    setCartItems((prev) => {
      const existingItemIndex = prev.findIndex((item) =>
        item.tipo === 'producto' &&
        item.producto_id === product.id &&
        item.product_price_id === priceRow.id
      );

      if (existingItemIndex >= 0) {
        return prev.map((item, index) => {
          if (index !== existingItemIndex) return item;
          if (maxQuantity !== null && item.cantidad >= maxQuantity) {
            return item;
          }

          const nextQuantity = maxQuantity !== null
            ? Math.min(item.cantidad + 1, maxQuantity)
            : item.cantidad + 1;

          didChangeCart = true;

          return {
            ...item,
            cantidad: nextQuantity,
            subtotal: Number(priceRow.precio) * nextQuantity,
          };
        });
      }

      const category = categories.find((c) => c.id === product.categoria_id);
      const priceUnit = Number(priceRow.precio);

      const newItem: CartProductItem = {
        id: `producto-${product.id}-${priceRow.id}-${Date.now()}`,
        tipo: 'producto',
        producto_id: product.id,
        producto_nombre: product.nombre,
        categoria_nombre: category?.nombre || 'Sin categoría',
        imagen: product.imagen,
        cantidad: 1,
        precio_unitario: priceUnit,
        subtotal: priceUnit,
        product_price_id: priceRow.id,
        precio_cantidad: priceRow.cantidad,
      };

      didChangeCart = true;

      return [...prev, newItem];
    });

    if (didChangeCart) {
      setAddedItemToast(product.nombre);
      setTimeout(() => setAddedItemToast(null), 2000);
    }

    return didChangeCart;
  }, [categories]);

  const handleAddProduct = useCallback((product: Product) => {
    const priceRow = getWholeProductPriceRow(product);
    if (priceRow) {
      addProductPriceItem(product, priceRow);
    }
  }, [addProductPriceItem]);

  const handleAddWholeProduct = useCallback((product: Product) => {
    const priceRow = getWholeProductPriceRow(product);
    if (priceRow) {
      addProductPriceItem(product, priceRow);
    }
  }, [addProductPriceItem]);

  const handleAddPortionProduct = useCallback((product: Product) => {
    const priceRow = getPortionProductPriceRow(product);
    if (priceRow) {
      addProductPriceItem(product, priceRow);
    }
  }, [addProductPriceItem]);

  // Add pizza mitad-mitad to cart
  const handleAddPizzaMitadMitad = useCallback((pizzaMitadMitad: {
    producto_id_izquierda: number;
    producto_id_derecha: number;
    cantidad: number;
    nombre_completo: string;
    precio_unitario: number;
  }) => {
    const newItem: CartPizzaMitadMitadItem = {
      id: `pizza-mitad-${pizzaMitadMitad.producto_id_izquierda}-${pizzaMitadMitad.producto_id_derecha}-${Date.now()}`,
      tipo: 'pizza_mitad_mitad',
      producto_id_izquierda: pizzaMitadMitad.producto_id_izquierda,
      producto_id_derecha: pizzaMitadMitad.producto_id_derecha,
      nombre_completo: pizzaMitadMitad.nombre_completo,
      cantidad: pizzaMitadMitad.cantidad,
      precio_unitario: pizzaMitadMitad.precio_unitario,
      subtotal: pizzaMitadMitad.precio_unitario * pizzaMitadMitad.cantidad,
    };

    setCartItems((prev) => [...prev, newItem]);
    setAddedItemToast(pizzaMitadMitad.nombre_completo);
    setTimeout(() => setAddedItemToast(null), 2000);
  }, []);

  // Add offer to cart (for fixed offers only in Phase 2)
  const handleAddOffer = (offer: Offer) => {
    // Build productos_seleccionados from offer's fixed products
    const productosSeleccionados = offer.productos?.flatMap((item) => {
      if (item.productos && item.productos.length === 1) {
        // Fixed product
        return [{
          producto_id: item.productos[0].id,
          producto_nombre: item.productos[0].nombre,
          cantidad: Number(item.cantidad),
        }];
      }
      return [];
    }) || [];

    const newItem: CartOfferItem = {
      id: `oferta-${offer.id}-${Date.now()}`,
      tipo: 'oferta',
      oferta_id: offer.id,
      oferta_nombre: offer.nombre,
      oferta_descripcion: offer.descripcion,
      cantidad: 1,
      precio_unitario: Number(offer.precio),
      subtotal: Number(offer.precio),
      productos_seleccionados: productosSeleccionados,
    };

    setCartItems((prev) => [...prev, newItem]);
    
    // Show toast feedback
    setAddedItemToast(offer.nombre);
    setTimeout(() => setAddedItemToast(null), 2000);
  };

  // Configure offer (for category/options offers in Phase 3)
  const handleConfigureOffer = (offer: Offer) => {
    setSelectedOfferForConfig(offer);
    setIsConfigModalOpen(true);
  };

  // Handle confirmation from OfferConfigModal
  const handleConfirmOfferConfig = (
    selectedProducts: { producto_id: number; producto_nombre: string; cantidad: number }[]
  ) => {
    if (!selectedOfferForConfig) return;

    // Create cart offer item with configured products
    const newItem: CartOfferItem = {
      id: `offer-${selectedOfferForConfig.id}-${Date.now()}`,
      tipo: 'oferta',
      oferta_id: selectedOfferForConfig.id,
      oferta_nombre: selectedOfferForConfig.nombre,
      cantidad: 1,
      precio_unitario: Number(selectedOfferForConfig.precio),
      subtotal: Number(selectedOfferForConfig.precio),
      productos_seleccionados: selectedProducts,
    };

    setCartItems((prev) => [...prev, newItem]);
    setIsConfigModalOpen(false);
    setSelectedOfferForConfig(null);
    
    // Show toast feedback
    setAddedItemToast(selectedOfferForConfig.nombre);
    setTimeout(() => setAddedItemToast(null), 2000);
  };

  // Get cart quantities for offers (memoized)
  const offerCartQuantities = useMemo(() => {
    const quantities = new Map<number, number>();
    cartItems.forEach((item) => {
      if (item.tipo === 'oferta') {
        const currentQty = quantities.get(item.oferta_id) || 0;
        quantities.set(item.oferta_id, currentQty + item.cantidad);
      }
    });
    return quantities;
  }, [cartItems]);

  // Update product quantity in cart
  const handleUpdateProductQuantity = useCallback((productId: number, newQuantity: number) => {
    if (newQuantity <= 0) {
      // Remove item
      setCartItems((prev) => prev.filter((item) => 
        !(item.tipo === 'producto' && item.producto_id === productId)
      ));
      return;
    }

    // Update quantity and recalculate price
    setCartItems((prev) =>
      prev.map((item) => {
        if (item.tipo === 'producto' && item.producto_id === productId) {
          const product = products.find((p) => p.id === productId);
          if (!product) return item;

          const newPrice = getProductPrice(product, newQuantity);
          return {
            ...item,
            cantidad: newQuantity,
            precio_unitario: newPrice,
            subtotal: newPrice * newQuantity,
          };
        }
        return item;
      })
    );
  }, [products]);

  // Update cart item quantity (generic)
  const handleUpdateCartItemQuantity = (itemId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      handleRemoveCartItem(itemId);
      return;
    }

    setCartItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const maxQuantity = item.tipo === 'producto'
            ? getMaxQuantityForPortionPrice(item.precio_cantidad)
            : null;

          const boundedQuantity = maxQuantity !== null
            ? Math.min(newQuantity, maxQuantity)
            : newQuantity;

          // For products, recalculate price based on quantity
          if (item.tipo === 'producto') {
            return {
              ...item,
              cantidad: boundedQuantity,
              subtotal: Number(item.precio_unitario) * boundedQuantity,
            };
          }

          // For offers, just update quantity
          return {
            ...item,
            cantidad: boundedQuantity,
            subtotal: Number(item.precio_unitario) * boundedQuantity,
          };
        }
        return item;
      })
    );
  };

  // Remove item from cart
  const handleRemoveCartItem = (itemId: string) => {
    setCartItems((prev) => prev.filter((item) => item.id !== itemId));
  };

  // Clear cart with confirmation
  const handleClearCart = () => {
    setShowConfirmModal(true);
  };

  const confirmClearCart = () => {
    setCartItems([]);
    setShowConfirmModal(false);
  };

  const buildSaleItemsPayload = (items: CartItem[]): SaleItemRequest[] => {
    const saleItems: SaleItemRequest[] = [];

    for (const item of items) {
      if (item.tipo === 'producto') {
        saleItems.push({
          producto_id: item.producto_id,
          cantidad: Number(((item.precio_cantidad ?? 1) * item.cantidad).toFixed(3)),
          precio_cantidad: item.precio_cantidad ?? 1,
        });
        continue;
      }

      if (item.tipo === 'oferta') {
        saleItems.push({
          oferta_id: item.oferta_id,
          cantidad: item.cantidad,
          productos_seleccionados: item.productos_seleccionados.map((p) => ({
            producto_id: p.producto_id,
            cantidad: Number(p.cantidad),
          })),
        });
        continue;
      }

      saleItems.push({
        pizza_mitad_mitad: {
          producto_id_izquierda: item.producto_id_izquierda,
          producto_id_derecha: item.producto_id_derecha,
          cantidad: item.cantidad,
        },
        cantidad: item.cantidad,
      });
    }

    return saleItems;
  };

  // Confirm sale
  const handleConfirmSale = async () => {
    if (cartItems.length === 0) return;

    try {
      setIsConfirming(true);
      setError(null);

      // Build sale items payload
      const saleItems: SaleItemRequest[] = buildSaleItemsPayload(cartItems);

      // Create sale
      await createSale({
        items: saleItems,
        aplicar_recargo: aplicarRecargo,
      });

      const saleEventKey = 'pizza_fiori:sale_created_at';
      const timestamp = Date.now().toString();
      window.dispatchEvent(new CustomEvent('sale:created'));
      localStorage.setItem(saleEventKey, timestamp);

      // Show success feedback
      setShowSuccess(true);
      setCartItems([]);
      setAplicarRecargo(false);

      // Hide success message after 1.5 seconds
      setTimeout(() => {
        setShowSuccess(false);
      }, 1500);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al crear la venta';
      setError(errorMessage);
    } finally {
      setIsConfirming(false);
    }
  };

  // Render page header immediately; show skeletons inside content while loading

  

  return (
    <>
      <div className="sales-create-page">
        <div className="sales-create-container">
          {/* Header */}
          <div className="page-header">
            <h1 className="page-title">Registrar Ventas</h1>
          </div>

          {/* Error Alert */}
          {error && (
            <ErrorAlert message={error} onClose={() => setError(null)} />
          )}

          {/* Tabs */}
          <div className="sales-tabs">
            <button
              className={`sales-tab ${activeTab === 'productos' ? 'active' : ''}`}
              onClick={() => setActiveTab('productos')}
            >
              Productos
            </button>
            <button
              className={`sales-tab ${activeTab === 'ofertas' ? 'active' : ''}`}
              onClick={() => setActiveTab('ofertas')}
            >
              Ofertas
            </button>
          </div>

          {/* Content */}
          <div className="sales-create-content">
            {loading ? (
              <div className="sales-create-loading-grid">
                <SkeletonLoader />
                <SkeletonLoader />
                <SkeletonLoader />
              </div>
            ) : activeTab === 'productos' ? (
              <ProductQuickSelector
                products={products}
                categories={categories}
                cartQuantities={cartQuantities}
                onAddProduct={handleAddProduct}
                onAddWholeProduct={handleAddWholeProduct}
                onAddPortionProduct={handleAddPortionProduct}
                onUpdateProductQuantity={handleUpdateProductQuantity}
                onOpenPizzaMitadMitad={() => setIsPizzaMitadMitadModalOpen(true)}
              />
            ) : (
              <OfferQuickSelector
                offers={offers}
                cartQuantities={offerCartQuantities}
                onAddOffer={handleAddOffer}
                onConfigureOffer={handleConfigureOffer}
              />
            )}
          </div>
        </div>
      </div>

      {/* Cart Drawer */}
      <CartDrawer
        items={cartItems}
        total={cartTotal}
        aplicarRecargo={aplicarRecargo}
        recargoPercent={recargoPercent}
        recargoAmount={recargoAmount}
        onToggleRecargo={() => setAplicarRecargo((prev) => !prev)}
        onUpdateQuantity={handleUpdateCartItemQuantity}
        onRemoveItem={handleRemoveCartItem}
        onClearCart={handleClearCart}
        onConfirmSale={handleConfirmSale}
        isConfirming={isConfirming}
      />

      {/* Clear Cart Confirmation Modal */}
      <AnimatePresence>
        {showConfirmModal && (
          <motion.div
            className="confirmation-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowConfirmModal(false)}
          >
            <motion.div
              className="confirmation-modal"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="confirmation-modal-title">¿Vaciar carrito?</h2>
              <p className="confirmation-modal-message">
                Se eliminarán todos los items del carrito. Esta acción no se puede deshacer.
              </p>
              <div className="confirmation-modal-actions">
                <button
                  className="confirmation-modal-btn confirmation-modal-btn-cancel"
                  onClick={() => setShowConfirmModal(false)}
                >
                  Cancelar
                </button>
                <button
                  className="confirmation-modal-btn confirmation-modal-btn-confirm"
                  onClick={confirmClearCart}
                >
                  Vaciar Carrito
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Offer Configuration Modal */}
      {selectedOfferForConfig && (
        <OfferConfigModal
          isOpen={isConfigModalOpen}
          offer={selectedOfferForConfig}
          products={products}
          onConfirm={handleConfirmOfferConfig}
          onClose={() => {
            setIsConfigModalOpen(false);
            setSelectedOfferForConfig(null);
          }}
        />
      )}

      {/* Pizza Mitad-Mitad Modal */}
      <PizzaMitadMitadModal
        isOpen={isPizzaMitadMitadModalOpen}
        onClose={() => setIsPizzaMitadMitadModalOpen(false)}
        products={products}
        categories={categories}
        onConfirm={handleAddPizzaMitadMitad}
      />

      {/* Success Message (portal without AnimatePresence for reliability) */}
      {showSuccess && createPortal(
        <motion.div
          className="confirmation-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShowSuccess(false)}
          style={{ cursor: 'pointer' }}
        >
          <motion.div
            className="sales-create-success"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Icons.CheckIcon size={56} className="sales-create-success-icon" />
            <h2 className="sales-create-success-title">¡Venta Registrada!</h2>
            <p className="sales-create-success-message">
              La venta se registró exitosamente
            </p>
          </motion.div>
        </motion.div>,
        document.body
      )}

      {/* Add to Cart Toast */}
      <AnimatePresence>
        {addedItemToast && (
          <motion.div
            className="add-to-cart-toast"
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
          >
            <Icons.CheckIcon size={16} color="currentColor" className="toast-icon" />
            <span className="toast-text">{addedItemToast}</span>
            <span className="toast-label">agregado al carrito</span>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default SalesCreatePage;

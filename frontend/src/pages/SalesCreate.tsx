import { useState, useEffect, useMemo, useCallback } from 'react';
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
import type { Product } from '../types/product';
import type { ProductoCategoria } from '../types/product_category';
import type { Offer } from '../types/offer';
import type { CartItem, CartProductItem, CartOfferItem, CartPizzaMitadMitadItem } from '../types/cart';
import type { SaleItemRequest } from '../types/sale_item';
import '../styles/sales-create.css';

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

  // UI states
  const [isConfirming, setIsConfirming] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState<'productos' | 'ofertas'>('productos');
  const [addedItemToast, setAddedItemToast] = useState<string | null>(null);

  // Modal states for configurable offers
  const [selectedOfferForConfig, setSelectedOfferForConfig] = useState<Offer | null>(null);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  // Modal states for pizza mitad-mitad
  const [isPizzaMitadMitadModalOpen, setIsPizzaMitadMitadModalOpen] = useState(false);

  // Load products and categories
  const fetchData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);

      const [productsData, categoriesData, offersData] = await Promise.all([
        getProductos(),
        getProductosCategorias(true),
        getOfertas(),
      ]);

      // Filter only active products and offers
      const activeProducts = productsData.filter((p) => p.activo);
      const activeOffers = offersData.filter((o) => o.activo);
      setProducts(activeProducts);
      setCategories(categoriesData);
      setOffers(activeOffers);
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
  useEffect(() => {
    const handleFocus = () => {
      fetchData();
    };

    window.addEventListener('focus', handleFocus);

    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchData]);

  // Calculate cart total whenever items change
  useEffect(() => {
    const total = cartItems.reduce((sum, item) => sum + item.subtotal, 0);
    setCartTotal(total);
  }, [cartItems]);

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

  // Get cart quantities map for ProductQuickSelector (memoized)
  const cartQuantities = useMemo(() => {
    const quantities = new Map<number, number>();
    cartItems.forEach((item) => {
      if (item.tipo === 'producto') {
        quantities.set(item.producto_id, item.cantidad);
      }
    });
    return quantities;
  }, [cartItems]);

  // Add product to cart
  const handleAddProduct = useCallback((product: Product) => {
    setCartItems((prev) => {
      // Check if product already exists in cart
      const existingItemIndex = prev.findIndex(
        (item) => item.tipo === 'producto' && item.producto_id === product.id
      );

      if (existingItemIndex >= 0) {
        // Product exists, increment quantity
        return prev.map((item, index) => {
          if (index === existingItemIndex && item.tipo === 'producto') {
            const newQuantity = item.cantidad + 1;
            const newPrice = Number(getProductPrice(product, newQuantity));
            return {
              ...item,
              cantidad: newQuantity,
              precio_unitario: newPrice,
              subtotal: newPrice * newQuantity,
            };
          }
          return item;
        });
      } else {
        // Product doesn't exist, create new item
        const price = Number(getProductPrice(product, 1));
        const category = categories.find((c) => c.id === product.categoria_id);

        const newItem: CartProductItem = {
          id: `producto-${product.id}-${Date.now()}`,
          tipo: 'producto',
          producto_id: product.id,
          producto_nombre: product.nombre,
          categoria_nombre: category?.nombre || 'Sin categoría',
          imagen: product.imagen,
          cantidad: 1,
          precio_unitario: price,
          subtotal: price,
        };

        return [...prev, newItem];
      }
    });
    
    // Show toast feedback
    setAddedItemToast(product.nombre);
    setTimeout(() => setAddedItemToast(null), 2000);
  }, [categories]);

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
          cantidad: item.cantidad,
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
          // For products, recalculate price based on quantity
          if (item.tipo === 'producto') {
            const product = products.find((p) => p.id === item.producto_id);
            if (!product) return item;

            const newPrice = Number(getProductPrice(product, newQuantity));
            return {
              ...item,
              cantidad: newQuantity,
              precio_unitario: newPrice,
              subtotal: newPrice * newQuantity,
            };
          }

          // For offers, just update quantity
          return {
            ...item,
            cantidad: newQuantity,
            subtotal: Number(item.precio_unitario) * newQuantity,
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

  // Confirm sale
  const handleConfirmSale = async () => {
    if (cartItems.length === 0) return;

    try {
      setIsConfirming(true);
      setError(null);

      // Build sale items payload
      const saleItems: SaleItemRequest[] = cartItems.map((item) => {
        if (item.tipo === 'producto') {
          return {
            producto_id: item.producto_id,
            cantidad: item.cantidad,
            // precio_unitario is optional for create (backend calculates)
          };
        } else if (item.tipo === 'oferta') {
          // Offer items (Fase 2+)
          return {
            oferta_id: item.oferta_id,
            cantidad: item.cantidad,
            productos_seleccionados: item.productos_seleccionados.map((p) => ({
              producto_id: p.producto_id,
              cantidad: p.cantidad,
            })),
          };
        } else {
          // Pizza mitad-mitad items
          return {
            pizza_mitad_mitad: {
              producto_id_izquierda: item.producto_id_izquierda,
              producto_id_derecha: item.producto_id_derecha,
              cantidad: item.cantidad,
            },
            cantidad: item.cantidad,
          };
        }
      });

      // Create sale
      await createSale({
        items: saleItems,
      });

      const saleEventKey = 'pizza_fiori:sale_created_at';
      const timestamp = Date.now().toString();
      window.dispatchEvent(new CustomEvent('sale:created'));
      localStorage.setItem(saleEventKey, timestamp);

      // Show success feedback
      setShowSuccess(true);
      setCartItems([]);

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

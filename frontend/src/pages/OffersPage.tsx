import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { ArrowDownWideNarrow, GripVertical } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { formatLocalISO } from "../utils/formatters";
import { getOfertas, reorderOfertas } from "../services/ofertasService";
import { getProductos } from "../services/productsService";
import { getProductosCategorias } from "../services/productosCategoriasService";
import OfferCard from "../components/OfferCard";
import OfferModal from "../components/OfferModal";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import "../styles/offers-page.css";

const OffersPage = () => {
  type OfferDragOverlay = {
    left: number;
    top: number;
    width: number;
    height: number;
    clone: HTMLDivElement;
  };

  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [ofertas, setOfertas] = useState<Offer[]>([]);
  const [productos, setProductos] = useState<Product[]>([]);
  const [categorias, setCategorias] = useState<ProductoCategoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOferta, setSelectedOferta] = useState<Offer | null>(null);
  const [isReordering, setIsReordering] = useState(false);
  const [draggedOfferId, setDraggedOfferId] = useState<number | null>(null);
  const [isSavingOrder, setIsSavingOrder] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);
  const offerOrderBeforeDrag = useRef<Offer[] | null>(null);
  const offerOrderPreview = useRef<Offer[]>([]);
  const draggedOfferIdRef = useRef<number | null>(null);
  const [offerDragOverlay, setOfferDragOverlay] = useState<OfferDragOverlay | null>(null);
  const offerDragOverlayRef = useRef<HTMLDivElement | null>(null);
  const offersGridRef = useRef<HTMLDivElement | null>(null);
  const offerDragPointerRef = useRef({ x: 0, y: 0 });
  const offerDragStartPointerRef = useRef({ x: 0, y: 0 });
  const offerDragGrabOffsetRef = useRef({ x: 0, y: 0 });
  const offerDragInsertionPointsRef = useRef<Map<number, {
    x: number;
    y: number;
    width: number;
    height: number;
  }>>(new Map());
  const offerDragSlotPositionsRef = useRef<Array<{ left: number; top: number }>>([]);
  const offerDragPointerIdRef = useRef<number | null>(null);
  const offerDragFrameRef = useRef<number | null>(null);
  const offerDragListenersRef = useRef<{
    onMove: (event: PointerEvent) => void;
    onUp: (event: PointerEvent) => void;
    onCancel: (event: PointerEvent) => void;
  } | null>(null);
  const pageScrollBehaviorRef = useRef("");

  useLayoutEffect(() => {
    if (!offerDragOverlay || !offerDragOverlayRef.current) return;
    offerDragOverlayRef.current.replaceChildren(offerDragOverlay.clone);
    return () => offerDragOverlay.clone.remove();
  }, [offerDragOverlay]);

  useEffect(() => () => {
    const listeners = offerDragListenersRef.current;
    if (listeners) {
      window.removeEventListener("pointermove", listeners.onMove);
      window.removeEventListener("pointerup", listeners.onUp);
      window.removeEventListener("pointercancel", listeners.onCancel);
    }
    if (offerDragFrameRef.current !== null) {
      cancelAnimationFrame(offerDragFrameRef.current);
    }
    if (offerDragPointerIdRef.current !== null) {
      document.documentElement.style.scrollBehavior = pageScrollBehaviorRef.current;
    }
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      setLoading(true);
      
      // Fetch ofertas activas, productos y categorías en paralelo
      const [offersData, productsData, categoriasData] = await Promise.all([
        getOfertas(true),
        getProductos(),
        getProductosCategorias(true),
      ]);

      setOfertas(offersData || []);
      setProductos(productsData || []);
      setCategorias(categoriasData || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido al cargar los datos";
      setError(`Error al cargar: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Recargar ofertas cuando la ventana recupera el foco
    const handleFocus = () => {
      if (draggedOfferIdRef.current !== null) return;
      fetchData();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  const handleCreateClick = () => {
    setSelectedOferta({
      id: 0,
      nombre: "",
      descripcion: null,
      precio: 0,
      activo: true,
      orden: ofertas.length,
      fecha_creacion: formatLocalISO(new Date()),
      fecha_actualizacion: formatLocalISO(new Date()),
      productos: [],
    });
    setIsModalOpen(true);
  };

  const handleOfferUpdate = (updatedOferta: Offer) => {
    setOfertas((prevOfertas) =>
      prevOfertas.map((o) => (o.id === updatedOferta.id ? updatedOferta : o))
    );
  };

  const handleOfferDelete = (ofertaId: number) => {
    setOfertas((prevOfertas) => prevOfertas.filter((o) => o.id !== ofertaId));
  };

  const previewOfferPosition = (pointerX: number, pointerY: number) => {
    const sourceOfferId = draggedOfferIdRef.current;
    const initialOrder = offerOrderBeforeDrag.current;
    if (sourceOfferId === null || !initialOrder || initialOrder.length === 0) return;

    const draggedOffer = initialOrder.find((offer) => offer.id === sourceOfferId);
    if (!draggedOffer) return;
    const remainingOffers = initialOrder.filter((offer) => offer.id !== sourceOfferId);
    const projectedX = pointerX + offerDragGrabOffsetRef.current.x;
    const projectedY =
      pointerY + offerDragGrabOffsetRef.current.y + window.scrollY;
    let nearestOfferIndex = -1;
    let nearestDistance = Number.POSITIVE_INFINITY;
    for (let index = 0; index < remainingOffers.length; index += 1) {
      const position = offerDragInsertionPointsRef.current.get(remainingOffers[index].id);
      if (!position) continue;
      const centerX = position.x + position.width / 2;
      const centerY = position.y + position.height / 2;
      const distance =
        ((projectedX - centerX) / Math.max(position.width, 1)) ** 2 +
        ((projectedY - centerY) / Math.max(position.height, 1)) ** 2;
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearestOfferIndex = index;
      }
    }

    let targetIndex = remainingOffers.length;
    if (nearestOfferIndex >= 0) {
      const target = offerDragInsertionPointsRef.current.get(
        remainingOffers[nearestOfferIndex].id,
      );
      if (target) {
        const targetCenterY = target.y + target.height / 2;
        const isWithinTargetRow =
          projectedY >= target.y && projectedY <= target.y + target.height;
        const insertAfter = isWithinTargetRow
          ? projectedX >= target.x + target.width / 2
          : projectedY >= targetCenterY;
        targetIndex = nearestOfferIndex + (insertAfter ? 1 : 0);
      }
    }

    const nextOrder = [...remainingOffers];
    nextOrder.splice(targetIndex, 0, draggedOffer);
    if (nextOrder.some((offer, index) => offer.id !== offerOrderPreview.current[index]?.id)) {
      offerOrderPreview.current = nextOrder;
      setOfertas(nextOrder.map((offer, orden) => ({ ...offer, orden })));
    }
  };

  const updateOfferDragPreview = (x: number, y: number) => {
    const overlay = offerDragOverlayRef.current;
    if (overlay) {
      const { x: startX, y: startY } = offerDragStartPointerRef.current;
      overlay.style.transform = `translate3d(${x - startX}px, ${y - startY}px, 0)`;
    }
    previewOfferPosition(x, y);
  };

  const scheduleOfferDragFrame = () => {
    if (offerDragFrameRef.current !== null) return;
    offerDragFrameRef.current = requestAnimationFrame(() => {
      offerDragFrameRef.current = null;
      const { x, y } = offerDragPointerRef.current;
      updateOfferDragPreview(x, y);

      const edgeSize = 56;
      const maxScrollY =
        document.documentElement.scrollHeight - window.innerHeight;
      let scrollDelta = 0;
      if (
        y >= -edgeSize &&
        y < edgeSize &&
        window.scrollY > 0
      ) {
        const strength = Math.min(1, (edgeSize - y) / edgeSize);
        scrollDelta = -Math.max(1, Math.ceil(strength * 10));
      } else if (
        y > window.innerHeight - edgeSize &&
        y <= window.innerHeight + edgeSize &&
        window.scrollY < maxScrollY
      ) {
        const strength = Math.min(
          1,
          (y - (window.innerHeight - edgeSize)) / edgeSize,
        );
        scrollDelta = Math.max(1, Math.ceil(strength * 10));
      }

      if (scrollDelta !== 0) {
        window.scrollTo(0, Math.max(0, Math.min(maxScrollY, window.scrollY + scrollDelta)));
        updateOfferDragPreview(x, y);
        scheduleOfferDragFrame();
      }
    });
  };

  const handleOfferPointerMove = (event: PointerEvent) => {
    if (
      event.pointerId !== offerDragPointerIdRef.current ||
      !offerDragOverlayRef.current ||
      draggedOfferIdRef.current === null
    ) return;
    offerDragPointerRef.current = { x: event.clientX, y: event.clientY };
    scheduleOfferDragFrame();
  };

  const removeOfferDragListeners = () => {
    const listeners = offerDragListenersRef.current;
    if (!listeners) return;
    window.removeEventListener("pointermove", listeners.onMove);
    window.removeEventListener("pointerup", listeners.onUp);
    window.removeEventListener("pointercancel", listeners.onCancel);
    offerDragListenersRef.current = null;
  };

  const stopOfferDragFrame = () => {
    if (offerDragFrameRef.current === null) return;
    cancelAnimationFrame(offerDragFrameRef.current);
    offerDragFrameRef.current = null;
  };

  const finishOfferDrag = () => {
    document.documentElement.style.scrollBehavior = pageScrollBehaviorRef.current;
    draggedOfferIdRef.current = null;
    offerDragPointerIdRef.current = null;
    setDraggedOfferId(null);
    setOfferDragOverlay(null);
    offerDragInsertionPointsRef.current.clear();
    offerDragSlotPositionsRef.current = [];
    offerOrderBeforeDrag.current = null;
    offerOrderPreview.current = [];
  };

  const handleOfferPointerCancel = (event: PointerEvent) => {
    if (event.pointerId !== offerDragPointerIdRef.current) return;
    removeOfferDragListeners();
    stopOfferDragFrame();
    const previousOrder = offerOrderBeforeDrag.current;
    if (previousOrder) setOfertas(previousOrder);
    finishOfferDrag();
  };

  const settleOfferDragOverlay = (offerId: number, nextOrder: Offer[]) =>
    new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const overlay = offerDragOverlayRef.current;
          const targetIndex = nextOrder.findIndex((offer) => offer.id === offerId);
          const slot = offerDragSlotPositionsRef.current[targetIndex];
          if (!overlay || !slot) {
            resolve();
            return;
          }

          const currentRect = overlay.getBoundingClientRect();
          overlay.style.transition = "none";
          overlay.style.left = `${currentRect.left}px`;
          overlay.style.top = `${currentRect.top}px`;
          overlay.style.transform = "none";
          void overlay.offsetWidth;
          overlay.style.transition = "left 180ms ease-out, top 180ms ease-out";
          overlay.style.left = `${slot.left}px`;
          overlay.style.top = `${slot.top - window.scrollY}px`;
          window.setTimeout(resolve, 200);
        });
      });
    });

  const handleOfferPointerUp = async (event: PointerEvent) => {
    if (event.pointerId !== offerDragPointerIdRef.current) return;
    removeOfferDragListeners();
    stopOfferDragFrame();
    updateOfferDragPreview(event.clientX, event.clientY);

    const previousOrder = offerOrderBeforeDrag.current;
    const offerId = draggedOfferIdRef.current;
    const nextOrder = [...offerOrderPreview.current];
    if (!previousOrder || offerId === null) {
      finishOfferDrag();
      return;
    }

    const hasOrderChanged = nextOrder.some(
      (offer, index) => offer.id !== previousOrder[index]?.id,
    );
    await settleOfferDragOverlay(offerId, nextOrder);
    finishOfferDrag();
    if (!hasOrderChanged) return;

    const orderedOffers = nextOrder.map((offer, orden) => ({ ...offer, orden }));
    setOrderError(null);
    setIsSavingOrder(true);
    try {
      await reorderOfertas(orderedOffers.map((offer) => offer.id));
    } catch (err) {
      setOfertas(previousOrder);
      setOrderError(
        err instanceof Error ? err.message : "No se pudo guardar el orden.",
      );
    } finally {
      setIsSavingOrder(false);
    }
  };

  const handleOfferPointerDown = (
    event: ReactPointerEvent<HTMLSpanElement>,
    oferta: Offer,
    card: HTMLDivElement,
  ) => {
    if (
      !isReordering ||
      isSavingOrder ||
      draggedOfferIdRef.current !== null ||
      event.button !== 0 ||
      !event.isPrimary
    ) return;
    const grid = offersGridRef.current;
    if (!grid) return;

    const offerElements = Array.from(
      grid.querySelectorAll<HTMLElement>(".offer-sortable-item"),
    );
    const slotPositions: Array<{ left: number; top: number }> = [];
    const insertionPoints = new Map<number, {
      x: number;
      y: number;
      width: number;
      height: number;
    }>();
    for (const element of offerElements) {
      const offerId = Number(element.dataset.offerId);
      const bounds = element.getBoundingClientRect();
      if (!Number.isFinite(offerId)) continue;
      slotPositions.push({
        left: bounds.left,
        top: bounds.top + window.scrollY,
      });
      insertionPoints.set(offerId, {
        x: bounds.left,
        y: bounds.top + window.scrollY,
        width: bounds.width,
        height: bounds.height,
      });
    }
    if (slotPositions.length !== ofertas.length) return;

    event.preventDefault();
    const bounds = card.getBoundingClientRect();
    const clone = card.cloneNode(true) as HTMLDivElement;
    clone.classList.add("offer-card-drag-overlay");
    const previousScrollBehavior = document.documentElement.style.scrollBehavior;
    pageScrollBehaviorRef.current = previousScrollBehavior;
    document.documentElement.style.scrollBehavior = "auto";
    offerOrderBeforeDrag.current = [...ofertas];
    offerOrderPreview.current = [...ofertas];
    offerDragInsertionPointsRef.current = insertionPoints;
    offerDragSlotPositionsRef.current = slotPositions;
    offerDragGrabOffsetRef.current = {
      x: bounds.left + bounds.width / 2 - event.clientX,
      y: bounds.top + bounds.height / 2 - event.clientY,
    };
    offerDragPointerRef.current = { x: event.clientX, y: event.clientY };
    offerDragStartPointerRef.current = { x: event.clientX, y: event.clientY };
    offerDragPointerIdRef.current = event.pointerId;
    draggedOfferIdRef.current = oferta.id;
    offerDragListenersRef.current = {
      onMove: handleOfferPointerMove,
      onUp: (upEvent) => void handleOfferPointerUp(upEvent),
      onCancel: handleOfferPointerCancel,
    };
    window.addEventListener("pointermove", offerDragListenersRef.current.onMove);
    window.addEventListener("pointerup", offerDragListenersRef.current.onUp);
    window.addEventListener("pointercancel", offerDragListenersRef.current.onCancel);
    setDraggedOfferId(oferta.id);
    setOfferDragOverlay({
      left: bounds.left,
      top: bounds.top,
      width: bounds.width,
      height: bounds.height,
      clone,
    });
  };

  const handleEdit = (oferta: Offer) => {
    setSelectedOferta(oferta);
    setIsModalOpen(true);
  };

  const handleSave = async (oferta: Offer) => {
    const isEditing = selectedOferta && selectedOferta.id > 0;
    
    if (isEditing) {
      // Actualización: reemplazar la oferta existente
      setOfertas((prev) =>
        prev.map((o) => (o.id === selectedOferta.id ? oferta : o))
      );
    } else {
      // Creación: agregar al final
      setOfertas((prev) => [...prev, oferta]);
    }
    setIsModalOpen(false);
    setSelectedOferta(null);
    
    // Refrescar datos completos del servidor para asegurar sincronización
    await fetchData();
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedOferta(null);
  };

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="offers-container">
      <div className="page-header">
        <h1 className="page-title">Ofertas</h1>
        <div className="offers-page-actions">
          <motion.button
            className="btn-create-offer"
            onClick={handleCreateClick}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Icons.PlusIcon size={16} /> Nueva Oferta
          </motion.button>
          <button
            className={`btn-order-offers${isReordering ? " is-active" : ""}`}
            onClick={() => {
              if (draggedOfferId !== null) return;
              setIsReordering((current) => !current);
              setOrderError(null);
            }}
            disabled={loading || ofertas.length < 2 || isSavingOrder || draggedOfferId !== null}
            title="Ordenar"
            aria-label="Ordenar ofertas"
            aria-pressed={isReordering}
          >
            <ArrowDownWideNarrow size={20} />
          </button>
        </div>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />
      {isReordering && (
        <p className="offers-order-hint" role="status">
          <GripVertical size={16} />
          Arrastrá las ofertas para cambiar su orden.
          {isSavingOrder && <span> Guardando...</span>}
        </p>
      )}
      {orderError && (
        <p className="offers-order-error" role="alert">{orderError}</p>
      )}

      {/* Modal de creación/edición */}
      <OfferModal
        oferta={selectedOferta}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        productos={productos}
        categorias={categorias}
      />

      {loading ? (
        <div className="offers-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : ofertas.length === 0 ? (
        <motion.div 
          className="offer-quick-selector"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="offer-selector-empty">
            <div className="offer-selector-empty-icon"><Icons.DiscountIcon size={36} /></div>
            <p>No hay ofertas disponibles</p>
            <p className="offer-selector-empty-sub">Crea tu primera oferta para comenzar</p>
          </div>
        </motion.div>
      ) : (
        <div className="offers-grid" ref={offersGridRef}>
          {ofertas.map((oferta) => (
            <div
              key={oferta.id}
              className={`offer-sortable-item${isReordering ? " is-reordering" : ""}${draggedOfferId === oferta.id ? " is-drag-source" : ""}`}
              data-offer-id={oferta.id}
            >
              <OfferCard
                oferta={oferta}
                productos={productos}
                onEdit={handleEdit}
                onOfferUpdate={handleOfferUpdate}
                onOfferDelete={handleOfferDelete}
                isReordering={isReordering}
                isDragSource={draggedOfferId === oferta.id}
                onOfferPointerDown={handleOfferPointerDown}
              />
            </div>
          ))}
        </div>
      )}
    </div>
    {offerDragOverlay && createPortal(
      <div
        ref={offerDragOverlayRef}
        className="offer-drag-overlay"
        style={{
          left: offerDragOverlay.left,
          top: offerDragOverlay.top,
          width: offerDragOverlay.width,
          height: offerDragOverlay.height,
          transform: "translate3d(0, 0, 0)",
        }}
      />,
      document.body,
    )}
    </>
  );
};

export default OffersPage;

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getOfertas } from "../services/ofertasService";
import { getProductos } from "../services/productsService";
import { getCategorias } from "../services/categoriasService";
import OfferCard from "../components/OfferCard";
import OfferModal from "../components/OfferModal";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import "../styles/offers-page.css";

const OffersPage = () => {
  const [ofertas, setOfertas] = useState<Offer[]>([]);
  const [productos, setProductos] = useState<Product[]>([]);
  const [categorias, setCategorias] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOferta, setSelectedOferta] = useState<Offer | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      setLoading(true);
      
      // Fetch ofertas activas, productos y categorías en paralelo
      const [offersData, productsData, categoriasData] = await Promise.all([
        getOfertas(true),
        getProductos(),
        getCategorias(),
      ]);

      setOfertas(offersData || []);
      setProductos(productsData || []);
      setCategorias(categoriasData || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido al cargar los datos";
      setError(`Error al cargar: ${errorMessage}`);
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Recargar ofertas cuando la ventana recupera el foco
    const handleFocus = () => {
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
      fecha_creacion: new Date().toISOString(),
      fecha_actualizacion: new Date().toISOString(),
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

  return (
    <div className="offers-container">
      <div className="page-header">
        <h1 className="page-title">Ofertas</h1>
        <motion.button
          className="btn-create-offer"
          onClick={handleCreateClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Icons.PlusIcon size={16} /> Nueva Oferta
        </motion.button>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />

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
        <div className="offers-grid">
          {ofertas.map((oferta) => (
            <OfferCard
              key={oferta.id}
              oferta={oferta}
              productos={productos}
              onEdit={handleEdit}
              onOfferUpdate={handleOfferUpdate}
              onOfferDelete={handleOfferDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default OffersPage;

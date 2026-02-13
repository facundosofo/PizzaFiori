import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { getCategorias } from "../services/categoriasService";
import { getProductos } from "../services/productsService";
import { getOfertas } from "../services/ofertasService";
import CategoryModal from "../components/CategoryModal";
import ErrorAlert from "../components/shared/ErrorAlert";
import ConfirmDialog from "../components/shared/ConfirmDialog";
import * as Icons from "../components/shared/Icons";
import { deactivateCategoria } from "../services/categoriasService";
import type { Category } from "../types/category";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import "../styles/categories-page.css";

const CategoriesPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [categorias, setCategorias] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState<Category | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [categoriaToDelete, setCategoriaToDelete] = useState<Category | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [affectedProducts, setAffectedProducts] = useState<Product[]>([]);
  const [affectedOffers, setAffectedOffers] = useState<Offer[]>([]);
  const [loadingAffected, setLoadingAffected] = useState(false);

  const fetchData = async () => {
    try {
      setError(null);
      setLoading(true);
      
      const categoriasData = await getCategorias(true);
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

    // Recargar categorías cuando la ventana recupera el foco
    const handleFocus = () => {
      fetchData();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  const handleCreateClick = () => {
    setSelectedCategoria({
      id: 0,
      nombre: "",
    });
    setIsModalOpen(true);
  };

  const handleEdit = (categoria: Category) => {
    setSelectedCategoria(categoria);
    setIsModalOpen(true);
  };

  const handleSave = async (categoria: Category) => {
    const isEditing = selectedCategoria && selectedCategoria.id > 0;
    
    if (isEditing) {
      // Actualización: reemplazar la categoría existente
      setCategorias((prev) =>
        prev.map((c) => (c.id === selectedCategoria.id ? categoria : c))
      );
    } else {
      // Creación: agregar al final
      setCategorias((prev) => [...prev, categoria]);
    }
    setIsModalOpen(false);
    setSelectedCategoria(null);
    
    // Refrescar datos completos del servidor para asegurar sincronización
    await fetchData();
  };

  const handleDeleteClick = async (categoria: Category) => {
    setCategoriaToDelete(categoria);
    setShowDeleteConfirm(true);
    await loadAffectedData(categoria.id);
  };

  const loadAffectedData = async (categoriaId: number) => {
    setLoadingAffected(true);
    try {
      // Cargar productos activos de la categoría
      const products = await getProductos(categoriaId);
      setAffectedProducts(products);

      // Cargar ofertas activas que contengan esos productos
      if (products.length > 0) {
        const allOffers = await getOfertas(true);
        const productIds = products.map(p => p.id);
        
        const affected = allOffers.filter(offer => 
          offer.productos?.some(item => 
            item.productos?.some(prod => productIds.includes(prod.id))
          )
        );
        
        setAffectedOffers(affected);
      } else {
        setAffectedOffers([]);
      }
    } catch (error) {
      setAffectedProducts([]);
      setAffectedOffers([]);
    } finally {
      setLoadingAffected(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!categoriaToDelete) return;

    setIsDeleting(true);
    try {
      await deactivateCategoria(categoriaToDelete.id);
      setCategorias((prev) => prev.filter((c) => c.id !== categoriaToDelete.id));
      setShowDeleteConfirm(false);
      setCategoriaToDelete(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`No se pudo desactivar: ${msg}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedCategoria(null);
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
    <div className="categories-page-container">
      <div className="page-header">
        <h1 className="page-title">Categorías</h1>
        <button
          className="btn-primary"
          onClick={handleCreateClick}
        >
          <Icons.PlusIcon size={16} /> Nueva Categoría
        </button>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      {/* Modal de creación/edición */}
      <CategoryModal
        categoria={selectedCategoria}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
      />

      <div className="categories-table-container">
        {loading ? (
          <p className="loading-message">Cargando categorías...</p>
        ) : categorias.length === 0 ? (
          <div className="empty-state">
            <Icons.LayersIcon size={48} />
            <p>No hay categorías disponibles</p>
            <span>Crea tu primera categoría para comenzar</span>
          </div>
        ) : (
          <table className="categories-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {categorias.map((categoria) => (
                <tr key={categoria.id}>
                  <td className="categoria-nombre">{categoria.nombre}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn-action btn-edit"
                        onClick={() => handleEdit(categoria)}
                        title="Editar categoría"
                      >
                        <Icons.EditIcon size={16} />
                      </button>
                      <button
                        className="btn-action btn-delete"
                        onClick={() => handleDeleteClick(categoria)}
                        disabled={isDeleting}
                        title="Desactivar categoría"
                      >
                        <Icons.TrashIcon size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Dialog de confirmación */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={<><Icons.WarningIcon size={18} /> Desactivar Categoría</>}
        message={
          <>
            ¿Está seguro que desea desactivar <strong style={{ color: "#ffffff" }}>{categoriaToDelete?.nombre}</strong>?
            {loadingAffected && (
              <div style={{ marginTop: "10px", fontSize: "14px", color: "#aaa" }}>
                Cargando elementos relacionados...
              </div>
            )}
            {!loadingAffected && affectedProducts.length > 0 && (
              <div style={{ 
                marginTop: "15px", 
                padding: "15px", 
                backgroundColor: "rgba(255, 193, 7, 0.15)", 
                borderRadius: "10px", 
                border: "1px solid rgba(255, 193, 7, 0.4)",
                textAlign: "left"
              }}>
                <div style={{ 
                  color: "#ffc107", 
                  fontWeight: 600, 
                  marginBottom: "12px", 
                  fontSize: "15px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px"
                }}>
                  <Icons.WarningIcon size={16} color="#ffc107" />
                  También se desactivarán {affectedProducts.length} {affectedProducts.length === 1 ? "producto" : "productos"}:
                </div>
                <ul style={{ 
                  margin: 0, 
                  paddingLeft: "28px", 
                  fontSize: "14px", 
                  color: "#ffffff",
                  listStyleType: "disc",
                  maxHeight: "120px",
                  overflowY: "auto"
                }}>
                  {affectedProducts.map(product => (
                    <li key={product.id} style={{ 
                      marginBottom: "6px",
                      lineHeight: "1.5"
                    }}>
                      {product.nombre}
                    </li>
                  ))}
                </ul>
                
                {affectedOffers.length > 0 && (
                  <>
                    <div style={{ 
                      color: "#ffc107", 
                      fontWeight: 600, 
                      marginTop: "16px",
                      marginBottom: "12px", 
                      fontSize: "15px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}>
                      <Icons.WarningIcon size={16} color="#ffc107" />
                      Y {affectedOffers.length} {affectedOffers.length === 1 ? "oferta" : "ofertas"}:
                    </div>
                    <ul style={{ 
                      margin: 0, 
                      paddingLeft: "28px", 
                      fontSize: "14px", 
                      color: "#ffffff",
                      listStyleType: "disc",
                      maxHeight: "100px",
                      overflowY: "auto"
                    }}>
                      {affectedOffers.map(offer => (
                        <li key={offer.id} style={{ 
                          marginBottom: "6px",
                          lineHeight: "1.5"
                        }}>
                          {offer.nombre}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </>
        }
        confirmText="Desactivar"
        cancelText="Cancelar"
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false);
          setCategoriaToDelete(null);
          setAffectedProducts([]);
          setAffectedOffers([]);
        }}
        confirmDanger
        confirmDisabled={isDeleting}
        cancelDisabled={isDeleting}
      />
    </div>
  );
};

export default CategoriesPage;

# Guía para Crear una Página en el Frontend de PizzaFiori

Esta guía describe paso a paso cómo crear una nueva página/módulo en el frontend siguiendo la arquitectura y patrones implementados en el proyecto React + TypeScript.

## Patrones Implementados

- **Component-Based Architecture**: Componentes reutilizables y modulares
- **Service Layer**: Separación de lógica de API en servicios
- **Type Safety**: TypeScript para tipado fuerte
- **State Management**: React Hooks (useState, useEffect)
- **Routing**: React Router DOM
- **Animations**: Framer Motion para transiciones suaves
- **Error Handling**: Manejo consistente de errores con componentes reutilizables

---

## Arquitectura del Frontend

```
Frontend Structure
├── src/
│   ├── types/          # Definiciones TypeScript
│   ├── services/       # Llamadas a la API
│   ├── components/     # Componentes reutilizables
│   ├── pages/          # Páginas principales
│   ├── styles/         # Archivos CSS
│   ├── config/         # Configuración
│   └── App.tsx         # Router principal
```

---

## Ejemplo: Crear el Módulo "Ofertas" (Offers)

Vamos a crear un módulo completo para gestionar ofertas como ejemplo.

---

## PASO 1: Crear los Tipos TypeScript

**Archivo:** `frontend/src/types/offer.ts`

```typescript
export interface OfferItem {
  id: number;
  producto_id: number;
  cantidad: number;
}

export interface Offer {
  id: number;
  nombre: string;
  descripcion?: string | null;
  precio: number;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  productos?: OfferItem[];
}
```

**Archivo:** `frontend/src/types/offer_item.ts`

```typescript
import type { Product } from './product';
import type { Offer } from './offer';

export interface OfferItem {
  id: number;
  oferta_id: number;
  producto_id: number;
  cantidad: number;
  producto?: Product;
  oferta?: Offer;
}
```

**Nota:** Si los tipos ya existen en `types/`, verifica que coincidan con la estructura de la API.

---

## PASO 2: Crear el Servicio de API

**Archivo:** `frontend/src/services/offersService.ts`

```typescript
import env from "../config/env";
import type { Offer } from "../types/offer";

export const getOfertas = async (active?: boolean): Promise<Offer[]> => {
  try {
    const url = active !== undefined 
      ? `${env.API_BASE_URL}/ofertas?active=${active}`
      : `${env.API_BASE_URL}/ofertas`;
    
    const res = await fetch(url);
    
    if (!res.ok) {
      const errorMsg = res.status === 404 
        ? "No se encontraron ofertas" 
        : res.status === 500 
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener las ofertas";
      throw new Error(errorMsg);
    }
    
    const data = await res.json();
    return data as Offer[];
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching ofertas:", err);
    throw new Error(errorMessage);
  }
};

export const getOfertaById = async (id: number): Promise<Offer> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}`);
    
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Oferta no encontrada"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : "No se pudo obtener la oferta";
      throw new Error(errorMsg);
    }
    
    return (await res.json()) as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching oferta:", err);
    throw new Error(errorMessage);
  }
};

export const createOferta = async (
  data: {
    nombre: string;
    descripcion?: string;
    precio: number;
    productos: Array<{ producto_id: number; cantidad: number }>;
  }
): Promise<Offer> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 404
        ? "Uno o más productos no encontrados"
        : res.status === 500
        ? "Error al crear la oferta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo crear la oferta";
      throw new Error(errorMsg);
    }
    
    return (await res.json()) as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error creating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const updateOferta = async (
  id: number,
  data: {
    nombre?: string;
    descripcion?: string;
    precio?: number;
    productos?: Array<{ producto_id: number; cantidad: number }>;
  }
): Promise<Offer> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 404 
        ? "Oferta no encontrada"
        : res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al guardar los cambios. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo actualizar la oferta";
      throw new Error(errorMsg);
    }
    
    return (await res.json()) as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error updating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const deactivateOferta = async (id: number): Promise<void> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}/desactivar`, {
      method: "PATCH",
      headers: {
        accept: "application/json",
      },
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Oferta no encontrada"
        : res.status === 500
        ? "Error al desactivar la oferta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo desactivar la oferta";
      throw new Error(errorMsg);
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error deactivating oferta:", err);
    throw new Error(errorMessage);
  }
};
```

**Convenciones:**
- Usar `env.API_BASE_URL` para la URL base
- Manejar errores HTTP de forma consistente
- Retornar tipos TypeScript específicos
- Usar async/await para operaciones asíncronas

---

## PASO 3: Crear Componente Card (Opcional)

**Archivo:** `frontend/src/components/OfferCard.tsx`

```typescript
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import OfferModal from "./OfferModal";
import ErrorAlert from "./ErrorAlert";
import { deactivateOferta } from "../services/offersService";
import "../styles/offer-card.css";

interface OfferCardProps {
  oferta: Offer;
  productos: Product[];
  onOfferUpdate?: (oferta: Offer) => void;
  onOfferDelete?: (ofertaId: number) => void;
}

const OfferCard = ({
  oferta,
  productos,
  onOfferUpdate,
  onOfferDelete,
}: OfferCardProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const formatPrecio = (value: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleSaveOffer = (updatedOferta: Offer) => {
    if (onOfferUpdate) {
      onOfferUpdate(updatedOferta);
    }
    setIsModalOpen(false);
  };

  const handleDeactivateOffer = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deactivateOferta(oferta.id);
      if (onOfferDelete) {
        onOfferDelete(oferta.id);
      }
      setShowDeleteConfirm(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido al desactivar oferta";
      setDeleteError(`No se pudo desactivar: ${errorMessage}`);
      console.error("Error desactivando oferta:", error);
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
        whileHover={{ scale: 1.05, y: -5 }}
        whileTap={{ scale: 0.97 }}
        onClick={handleOpenModal}
      >
        <button
          className="offer-card-deactivate"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteConfirm(true);
          }}
          title="Desactivar oferta"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>

        <div className="offer-card-body">
          <h3 className="offer-card-title">{oferta.nombre.toUpperCase()}</h3>
          
          {oferta.descripcion && (
            <p className="offer-card-description">{oferta.descripcion}</p>
          )}

          <div className="offer-card-price">
            <span className="price-label">Precio:</span>
            <span className="price-amount">{formatPrecio(oferta.precio)}</span>
          </div>

          {oferta.productos && oferta.productos.length > 0 && (
            <div className="offer-card-products">
              <span className="products-label">Incluye:</span>
              <ul>
                {oferta.productos.map((item) => {
                  const producto = productos.find(p => p.id === item.producto_id);
                  return (
                    <li key={item.id}>
                      {item.cantidad}x {producto?.nombre || `Producto ${item.producto_id}`}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          <button
            className="offer-card-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenModal();
            }}
          >
            Editar
          </button>
        </div>
      </motion.div>

      <OfferModal
        oferta={oferta}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveOffer}
        productos={productos}
      />

      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !isDeleting && setShowDeleteConfirm(false)}
          >
            <motion.div
              className="confirm-dialog"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="confirm-title">⚠️ Desactivar Oferta</h3>
              <p className="confirm-message">
                ¿Está seguro que desea desactivar{" "}
                <strong>{oferta.nombre}</strong>?
              </p>

              <div className="confirm-actions">
                <button
                  className="confirm-cancel-btn"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                >
                  Cancelar
                </button>
                <button
                  className="confirm-deactivate-btn"
                  onClick={handleDeactivateOffer}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Desactivando..." : "Desactivar"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ErrorAlert message={deleteError} onClose={() => setDeleteError(null)} />
    </>
  );
};

export default OfferCard;
```

---

## PASO 4: Crear Componente Modal (Opcional)

**Archivo:** `frontend/src/components/OfferModal.tsx`

```typescript
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import { updateOferta, createOferta } from "../services/offersService";
import "../styles/shared.css";
import "../styles/offer-modal.css";

interface OfferModalProps {
  oferta: Offer | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (oferta: Offer) => void;
  productos?: Product[];
}

const OfferModal = ({
  oferta,
  isOpen,
  onClose,
  onSave,
  productos = [],
}: OfferModalProps) => {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [precio, setPrecio] = useState("");
  const [selectedProductos, setSelectedProductos] = useState<
    Array<{ producto_id: number; cantidad: number }>
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (oferta && isOpen) {
      setNombre(oferta.nombre || "");
      setDescripcion(oferta.descripcion || "");
      setPrecio(oferta.precio.toString());
      setSelectedProductos(
        oferta.productos?.map(p => ({
          producto_id: p.producto_id,
          cantidad: p.cantidad
        })) || []
      );
      setError("");
    }
  }, [oferta, isOpen]);

  if (!oferta) return null;

  const handleAddProducto = () => {
    setSelectedProductos([
      ...selectedProductos,
      { producto_id: 0, cantidad: 1 }
    ]);
  };

  const handleRemoveProducto = (index: number) => {
    setSelectedProductos(selectedProductos.filter((_, i) => i !== index));
  };

  const handleProductoChange = (index: number, productoId: number) => {
    const newProductos = [...selectedProductos];
    newProductos[index].producto_id = productoId;
    setSelectedProductos(newProductos);
  };

  const handleCantidadChange = (index: number, cantidad: number) => {
    const newProductos = [...selectedProductos];
    newProductos[index].cantidad = Math.max(1, cantidad);
    setSelectedProductos(newProductos);
  };

  const handleSave = async () => {
    setError("");
    
    if (!nombre.trim()) return setError("El nombre es requerido");
    if (!precio || parseFloat(precio) <= 0) return setError("El precio debe ser mayor a 0");
    if (selectedProductos.length === 0) return setError("Debes agregar al menos un producto");
    if (selectedProductos.some(p => p.producto_id === 0)) {
      return setError("Todos los productos deben estar seleccionados");
    }

    setLoading(true);
    try {
      const offerData = {
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || undefined,
        precio: parseFloat(precio),
        productos: selectedProductos,
      };

      let savedOferta: Offer;
      
      if (oferta.id === 0) {
        savedOferta = await createOferta(offerData);
      } else {
        savedOferta = await updateOferta(oferta.id, offerData);
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

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="modal-content"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-close" onClick={onClose} aria-label="Cerrar">✕</button>

            <div className="modal-header-edit">
              <h2 className="modal-title">
                {oferta.id === 0 ? "Nueva Oferta" : "Editar Oferta"}
              </h2>
            </div>

            <div className="modal-body">
              {error && <div className="form-error">{error}</div>}

              <div className="edit-form">
                <div className="form-group">
                  <label htmlFor="offer-nombre">Nombre de la Oferta:</label>
                  <input
                    id="offer-nombre"
                    type="text"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    className="form-input"
                    disabled={loading}
                    placeholder="Ej. Combo Familiar"
                    maxLength={255}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="offer-descripcion">Descripción:</label>
                  <textarea
                    id="offer-descripcion"
                    value={descripcion}
                    onChange={(e) => setDescripcion(e.target.value)}
                    className="form-input"
                    disabled={loading}
                    placeholder="Ej. 2 Pizzas + 2 Bebidas"
                    rows={3}
                    maxLength={1000}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="offer-precio">Precio:</label>
                  <input
                    id="offer-precio"
                    type="number"
                    step="0.01"
                    min="0"
                    value={precio}
                    onChange={(e) => setPrecio(e.target.value)}
                    className="form-input"
                    disabled={loading}
                    placeholder="Ej: 3500.00"
                  />
                </div>

                <div className="form-group">
                  <label>Productos Incluidos:</label>
                  <div className="products-editor">
                    {selectedProductos.map((item, index) => (
                      <div key={index} className="product-edit-row">
                        <select
                          value={item.producto_id}
                          onChange={(e) => handleProductoChange(index, parseInt(e.target.value))}
                          className="form-input"
                          disabled={loading}
                        >
                          <option value="0">Seleccionar producto</option>
                          {productos.map((prod) => (
                            <option key={prod.id} value={prod.id}>
                              {prod.nombre}
                            </option>
                          ))}
                        </select>

                        <div className="quantity-control">
                          <button
                            type="button"
                            className="qty-btn"
                            onClick={() => handleCantidadChange(index, item.cantidad - 1)}
                            disabled={loading || item.cantidad <= 1}
                          >
                            −
                          </button>
                          <span className="qty-value">{item.cantidad}</span>
                          <button
                            type="button"
                            className="qty-btn"
                            onClick={() => handleCantidadChange(index, item.cantidad + 1)}
                            disabled={loading}
                          >
                            +
                          </button>
                        </div>

                        <button
                          type="button"
                          className="product-remove-btn"
                          onClick={() => handleRemoveProducto(index)}
                          disabled={loading}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="product-add-btn"
                    onClick={handleAddProducto}
                    disabled={loading}
                  >
                    + Agregar Producto
                  </button>
                </div>

                <div className="form-actions">
                  <button 
                    className="form-save-btn" 
                    onClick={handleSave} 
                    disabled={loading}
                  >
                    {loading ? "Guardando..." : oferta.id === 0 ? "Crear Oferta" : "Actualizar Oferta"}
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
      )}
    </AnimatePresence>
  );
};

export default OfferModal;
```

---

## PASO 5: Crear la Página Principal

**Archivo:** `frontend/src/pages/OffersPage.tsx`

```typescript
import { useEffect, useState } from "react";
import { getOfertas } from "../services/offersService";
import { getProductos } from "../services/productsService";
import OfferCard from "../components/OfferCard";
import OfferModal from "../components/OfferModal";
import SkeletonLoader from "../components/SkeletonLoader";
import ErrorAlert from "../components/ErrorAlert";
import type { Offer } from "../types/offer";
import type { Product } from "../types/product";
import "../styles/offer-card.css";

const OffersPage = () => {
  const [ofertas, setOfertas] = useState<Offer[]>([]);
  const [productos, setProductos] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newOffer, setNewOffer] = useState<Offer | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [offers, prods] = await Promise.all([
          getOfertas(true), // Solo ofertas activas
          getProductos(),
        ]);

        setOfertas(offers || []);
        setProductos(prods || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido al cargar los datos";
        setError(`Error al cargar: ${errorMessage}`);
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleOfferUpdate = (updatedOferta: Offer) => {
    setOfertas((prevOfertas) =>
      prevOfertas.map((o) => (o.id === updatedOferta.id ? updatedOferta : o))
    );
  };

  const handleOfferDelete = (ofertaId: number) => {
    setOfertas((prevOfertas) => prevOfertas.filter((o) => o.id !== ofertaId));
  };

  const handleCreateClick = () => {
    setNewOffer({
      id: 0,
      nombre: "",
      descripcion: null,
      precio: 0,
      activo: true,
      fecha_creacion: new Date().toISOString(),
      fecha_actualizacion: new Date().toISOString(),
      productos: [],
    });
    setIsCreating(true);
  };

  const handleCreateOffer = async (oferta: Offer) => {
    setOfertas((prev) => [...prev, oferta]);
    setIsCreating(false);
    setNewOffer(null);
  };

  return (
    <div className="offers-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1 className="offers-title">Ofertas</h1>
        <button
          className="btn-create-offer"
          onClick={handleCreateClick}
          style={{
            padding: "0.75rem 1.5rem",
            backgroundColor: "#4CAF50",
            color: "white",
            border: "none",
            borderRadius: "8px",
            fontSize: "1rem",
            fontWeight: "600",
            cursor: "pointer",
            transition: "background-color 0.3s ease",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#45a049")}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#4CAF50")}
        >
          + Nueva Oferta
        </button>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      {newOffer && (
        <OfferModal
          oferta={newOffer}
          isOpen={isCreating}
          onClose={() => {
            setIsCreating(false);
            setNewOffer(null);
          }}
          onSave={handleCreateOffer}
          productos={productos}
        />
      )}

      {loading ? (
        <div className="skeleton-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : ofertas.length === 0 ? (
        <p className="empty-state">No hay ofertas disponibles</p>
      ) : (
        <div className="offers-grid">
          {ofertas.map((oferta) => (
            <OfferCard
              key={oferta.id}
              oferta={oferta}
              productos={productos}
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
```

---

## PASO 6: Agregar Ruta en App.tsx

**Archivo:** `frontend/src/App.tsx`

```typescript
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import ProductosPage from "./pages/ProductsPage";
import OffersPage from "./pages/OffersPage"; // ✅ NUEVO

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/productos" element={<ProductosPage />} />
        <Route path="/ofertas" element={<OffersPage />} /> {/* ✅ NUEVO */}
      </Routes>
    </Router>
  );
}

export default App;
```

---

## PASO 7: Agregar Módulo en HomePage (Opcional)

**Archivo:** `frontend/src/pages/HomePage.tsx`

```typescript
import { motion } from "framer-motion";
import logo from "../assets/PizzaFioriLogo.png";
import { ModuleCard } from "../components/ModuleCard";
import "../styles/home.css";

export const HomePage = () => {
  return (
    <div className="home-container">
      {/* LOGO */}
      <motion.img
        src={logo}
        alt="PizzaFiori"
        className="logo"
        initial={{ scale: 1.4 }}
        animate={{ scale: 0.85, y: -90 }}
        transition={{
          duration: 1.5,
          ease: "easeInOut",
        }}
      />

      {/* MÓDULOS */}
      <motion.div
        className="modules"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <ModuleCard title="Productos" to="/productos" />
        <ModuleCard title="Ofertas" to="/ofertas" /> {/* ✅ NUEVO */}
        <ModuleCard title="Ventas" to="/ventas" />
        <ModuleCard title="Reportes" to="/reportes" />
      </motion.div>
    </div>
  );
};
```

---

## PASO 8: Crear Estilos CSS

**Archivo:** `frontend/src/styles/offer-card.css`

```css
.offers-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.offers-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.btn-create-offer {
  padding: 0.75rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.btn-create-offer:hover {
  background-color: #45a049;
}

.offers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.offer-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  position: relative;
  transition: box-shadow 0.3s ease;
}

.offer-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.offer-card-deactivate {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.offer-card-deactivate:hover {
  background-color: rgba(231, 76, 60, 0.1);
}

.offer-card-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.offer-card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.offer-card-description {
  color: #666;
  font-size: 0.95rem;
  margin: 0;
}

.offer-card-price {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.price-label {
  font-weight: 600;
  color: #666;
}

.price-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: #4CAF50;
}

.offer-card-products {
  margin-top: 0.5rem;
}

.products-label {
  font-weight: 600;
  color: #666;
  display: block;
  margin-bottom: 0.5rem;
}

.offer-card-products ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.offer-card-products li {
  padding: 0.25rem 0;
  color: #555;
  font-size: 0.9rem;
}

.offer-card-btn {
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-top: 1rem;
}

.offer-card-btn:hover {
  background-color: #0056b3;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-size: 1.2rem;
}
```

**Archivo:** `frontend/src/styles/offer-modal.css`

```css
.products-editor {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.5rem;
}

.product-edit-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.product-edit-row select {
  flex: 1;
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.25rem;
}

.qty-btn {
  background: #f8f9fa;
  border: none;
  width: 2rem;
  height: 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.qty-btn:hover:not(:disabled) {
  background-color: #e9ecef;
}

.qty-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qty-value {
  min-width: 2rem;
  text-align: center;
  font-weight: 600;
}

.product-remove-btn {
  background: #e74c3c;
  color: white;
  border: none;
  width: 2rem;
  height: 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.product-remove-btn:hover {
  background-color: #c0392b;
}

.product-add-btn {
  padding: 0.75rem 1rem;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-top: 0.5rem;
}

.product-add-btn:hover {
  background-color: #218838;
}
```

---

## Checklist de Creación de Página

- [ ] **Paso 1**: Crear tipos TypeScript en `types/`
- [ ] **Paso 2**: Crear servicio de API en `services/`
- [ ] **Paso 3**: Crear componente Card (si aplica) en `components/`
- [ ] **Paso 4**: Crear componente Modal (si aplica) en `components/`
- [ ] **Paso 5**: Crear página principal en `pages/`
- [ ] **Paso 6**: Agregar ruta en `App.tsx`
- [ ] **Paso 7**: Agregar módulo en `HomePage.tsx` (si aplica)
- [ ] **Paso 8**: Crear estilos CSS en `styles/`
- [ ] **Paso 9**: Probar la funcionalidad completa
- [ ] **Paso 10**: Verificar manejo de errores y estados de carga

---

## Convenciones y Mejores Prácticas

### Nomenclatura

- **Tipos:** PascalCase (`Offer`, `Product`, `Category`)
- **Servicios:** camelCase (`getOfertas`, `createOferta`)
- **Componentes:** PascalCase (`OfferCard`, `OfferModal`)
- **Páginas:** PascalCase con sufijo `Page` (`OffersPage`, `ProductsPage`)
- **Archivos CSS:** kebab-case (`offer-card.css`, `product-modal.css`)

### Estructura de Componentes

- Usar componentes funcionales con hooks
- Separar lógica de presentación
- Usar TypeScript para tipado fuerte
- Manejar estados de carga y error consistentemente

### Manejo de Errores

```typescript
try {
  const data = await getOfertas();
  setOfertas(data);
} catch (err) {
  const errorMessage = err instanceof Error ? err.message : "Error desconocido";
  setError(`Error al cargar: ${errorMessage}`);
  console.error("Error fetching data:", err);
}
```

### Estados de Carga

```typescript
const [loading, setLoading] = useState(true);

// En el render
{loading ? (
  <SkeletonLoader />
) : (
  // Contenido
)}
```

### Animaciones

Usar Framer Motion para transiciones suaves:

```typescript
import { motion } from "framer-motion";

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4 }}
>
  {/* Contenido */}
</motion.div>
```

### Formateo de Precios

```typescript
const formatPrecio = (value: number) => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};
```

### Validación de Formularios

- Validar en el cliente antes de enviar
- Mostrar mensajes de error claros
- Deshabilitar botones durante el guardado
- Validar campos requeridos

---

## Recursos Adicionales

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [React Router](https://reactrouter.com/)
- [Framer Motion](https://www.framer.com/motion/)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

---

## Notas Finales

Esta estructura proporciona:

✅ **Separación de responsabilidades** clara entre tipos, servicios, componentes y páginas  
✅ **Reutilización** de componentes comunes (ErrorAlert, SkeletonLoader)  
✅ **Type Safety** con TypeScript  
✅ **Consistencia** en el manejo de errores y estados  
✅ **Mantenibilidad** mediante patrones claros y bien definidos  
✅ **UX mejorada** con animaciones y feedback visual  

Cada nueva página debe seguir estos mismos pasos para mantener la consistencia arquitectónica del proyecto.

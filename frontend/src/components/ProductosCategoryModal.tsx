import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import * as Icons from './shared/Icons';
import type { ProductoCategoria } from "../types/product_category";
import { createProductoCategoria, updateProductoCategoria } from "../services/productosCategoriasService";
import "../styles/category-modal.css";

interface ProductosCategoryModalProps {
  categoria: ProductoCategoria | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (categoria: ProductoCategoria) => void;
}

const ProductosCategoryModal = ({
  categoria,
  isOpen,
  onClose,
  onSave,
}: ProductosCategoryModalProps) => {
  const [nombre, setNombre] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isEditing = categoria && categoria.id > 0;

  useEffect(() => {
    if (categoria && isOpen) {
      setNombre(categoria.nombre || "");
      setError("");
    } else if (!categoria && isOpen) {
      setNombre("");
      setError("");
    }
  }, [categoria, isOpen]);

  const handleSave = async () => {
    setError("");

    if (!nombre.trim()) {
      return setError("El nombre es requerido");
    }
    if (nombre.trim().length > 50) {
      return setError("El nombre no puede superar los 50 caracteres");
    }

    setLoading(true);

    try {
      let savedCategoria: ProductoCategoria;

      if (isEditing) {
        savedCategoria = await updateProductoCategoria(categoria.id, {
          nombre: nombre.trim(),
        });
      } else {
        savedCategoria = await createProductoCategoria({
          nombre: nombre.trim(),
        });
      }

      onSave?.(savedCategoria);
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`Error al guardar: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="category-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="category-modal"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="category-modal-header">
              <h2 className="category-modal-title">
                {isEditing ? "Editar Categoría" : "Nueva Categoría"}
              </h2>
              <button
                className="category-modal-close"
                onClick={onClose}
                disabled={loading}
              >
                <Icons.XIcon size={20} />
              </button>
            </div>

            <div className="category-modal-body">
              <div className="category-form-group">
                <label htmlFor="nombre" className="category-form-label">
                  Nombre <span className="category-required">*</span>
                </label>
                <input
                  id="nombre"
                  type="text"
                  className="category-form-input"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Pizzas, Bebidas, Postres..."
                  maxLength={50}
                  disabled={loading}
                  autoFocus
                />
                <span className="form-hint">
                  {nombre.length}/50 caracteres
                </span>
              </div>

              {error && (
                <div className="category-error-alert">
                  <Icons.AlertCircleIcon size={20} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="category-modal-footer">
              <button
                className="category-btn category-btn-cancel"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                className="category-btn category-btn-save"
                onClick={handleSave}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Icons.LoaderIcon size={16} className="category-spinner" />
                    Guardando...
                  </>
                ) : (
                  <>{isEditing ? "Actualizar" : "Crear"}</>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProductosCategoryModal;

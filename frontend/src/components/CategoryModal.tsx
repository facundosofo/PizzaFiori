import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import * as Icons from './shared/Icons';
import type { Category } from "../types/category";
import { createCategoria, updateCategoria } from "../services/categoriasService";
import "../styles/category-modal.css";

interface CategoryModalProps {
  categoria: Category | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (categoria: Category) => void;
}

const CategoryModal = ({
  categoria,
  isOpen,
  onClose,
  onSave,
}: CategoryModalProps) => {
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

    // Validaciones
    if (!nombre.trim()) {
      return setError("El nombre es requerido");
    }

    setLoading(true);

    try {
      let savedCategoria: Category;

      if (isEditing) {
        // Actualizar
        savedCategoria = await updateCategoria(categoria.id, {
          nombre: nombre.trim(),
        });
      } else {
        // Crear
        savedCategoria = await createCategoria({
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
          {/* Modal */}
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
              {/* Nombre */}
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
                  disabled={loading}
                  autoFocus
                />
              </div>

              {/* Error */}
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
                  <>
                    {isEditing ? "Actualizar" : "Crear"}
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default CategoryModal;

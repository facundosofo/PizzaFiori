import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import type { ExpenseCategory } from "../types/expense_category";
import {
  createGastoCategoria,
  updateGastoCategoria,
} from "../services/gastosCategoriasService";
import "../styles/expense-category-modal.css";

interface ExpenseCategoryModalProps {
  categoria: ExpenseCategory | null;
  categorias: ExpenseCategory[];
  isOpen: boolean;
  defaultParentId?: number | null;
  onClose: () => void;
  onSave?: (categoria: ExpenseCategory) => void;
}

const ExpenseCategoryModal = ({
  categoria,
  categorias,
  isOpen,
  defaultParentId = null,
  onClose,
  onSave,
}: ExpenseCategoryModalProps) => {
  const [nombre, setNombre] = useState("");
  const [padreId, setPadreId] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isEditing = categoria && categoria.id > 0;

  useEffect(() => {
    if (categoria && isOpen) {
      setNombre(categoria.nombre || "");
      setPadreId(categoria.padre_id ?? "");
      setError("");
      return;
    }

    if (!categoria && isOpen) {
      setNombre("");
      setPadreId(defaultParentId ?? "");
      setError("");
    }
  }, [categoria, isOpen, defaultParentId]);

  const handleSave = async () => {
    setError("");

    if (!nombre.trim()) {
      setError("El nombre es requerido");
      return;
    }

    if (nombre.trim().length > 100) {
      setError("El nombre no puede superar los 100 caracteres");
      return;
    }

    setLoading(true);

    try {
      let savedCategoria: ExpenseCategory;
      const payload = {
        nombre: nombre.trim(),
        ...(padreId === "" ? {} : { padre_id: Number(padreId) }),
      };

      if (isEditing && categoria) {
        savedCategoria = await updateGastoCategoria(categoria.id, payload);
      } else {
        savedCategoria = await createGastoCategoria(payload);
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
          className="expense-category-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="expense-category-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="expense-category-modal-header">
              <div>
                <p className="expense-category-modal-eyebrow">Gastos</p>
                <h2 className="expense-category-modal-title">
                  {isEditing ? "Editar categoria" : "Nueva categoria"}
                </h2>
              </div>
              <button
                className="expense-category-modal-close"
                onClick={onClose}
                disabled={loading}
              >
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="expense-category-modal-body">
              <div className="expense-category-form-group">
                <label className="expense-category-form-label">
                  Nombre <span className="expense-required">*</span>
                </label>
                <input
                  className="expense-category-form-input"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Servicios, Sueldos, Insumos"
                  maxLength={100}
                  disabled={loading}
                  autoFocus
                />
                <span className="expense-form-hint">
                  {nombre.length}/100 caracteres
                </span>
              </div>


              {error && (
                <div className="expense-category-error">
                  <Icons.AlertCircleIcon size={20} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="expense-category-modal-footer">
              <button
                className="expense-category-btn cancel"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                className="expense-category-btn save"
                onClick={handleSave}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Icons.LoaderIcon size={16} className="expense-spinner" />
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

export default ExpenseCategoryModal;

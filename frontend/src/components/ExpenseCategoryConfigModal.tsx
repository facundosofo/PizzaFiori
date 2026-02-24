import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import ExpenseCategoryModal from "./ExpenseCategoryModal";
import ConfirmDialog from "./shared/ConfirmDialog";
import type { ExpenseCategory } from "../types/expense_category";
import { deactivateGastoCategoria } from "../services/gastosCategoriasService";
import "../styles/expense-category-config-modal.css";

interface ExpenseCategoryConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  categorias: ExpenseCategory[];
  onRefresh: () => void;
}

const ExpenseCategoryConfigModal = ({
  isOpen,
  onClose,
  categorias,
  onRefresh,
}: ExpenseCategoryConfigModalProps) => {
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState<ExpenseCategory | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [defaultParentId, setDefaultParentId] = useState<number | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [categoriaToDelete, setCategoriaToDelete] = useState<ExpenseCategory | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const categoriasPadre = useMemo(() => {
    return categorias
      .filter((item) => !item.padre_id)
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
  }, [categorias]);

  const subcategoriasPorPadre = useMemo(() => {
    const map = new Map<number, ExpenseCategory[]>();
    categorias
      .filter((item) => item.padre_id)
      .forEach((item) => {
        const parentId = item.padre_id as number;
        if (!map.has(parentId)) {
          map.set(parentId, []);
        }
        map.get(parentId)?.push(item);
      });
    return map;
  }, [categorias]);

  useEffect(() => {
    if (!isOpen) return;

    if (categoriasPadre.length === 0) {
      setSelectedCategoryId(null);
      return;
    }

    const hasSelected = categoriasPadre.some((item) => item.id === selectedCategoryId);
    if (!hasSelected) {
      setSelectedCategoryId(categoriasPadre[0].id);
    }
  }, [categoriasPadre, selectedCategoryId, isOpen]);

  const selectedCategoriaPadre = useMemo(() => {
    if (!selectedCategoryId) return null;
    return categoriasPadre.find((item) => item.id === selectedCategoryId) || null;
  }, [selectedCategoryId, categoriasPadre]);

  const subcategoriasSeleccionadas = useMemo(() => {
    if (!selectedCategoriaPadre) return [];
    return subcategoriasPorPadre.get(selectedCategoriaPadre.id) || [];
  }, [selectedCategoriaPadre, subcategoriasPorPadre]);


  const handleCreateCategory = () => {
    setDefaultParentId(null);
    setSelectedCategoria(null);
    setIsCategoryModalOpen(true);
  };

  const handleCreateSubcategory = () => {
    if (!selectedCategoriaPadre) return;
    setDefaultParentId(selectedCategoriaPadre.id);
    setSelectedCategoria(null);
    setIsCategoryModalOpen(true);
  };

  const handleEditCategory = (cat: ExpenseCategory) => {
    setDefaultParentId(null);
    setSelectedCategoria(cat);
    setIsCategoryModalOpen(true);
  };

  const handleDeleteCategoryClick = (cat: ExpenseCategory) => {
    setCategoriaToDelete(cat);
    setShowDeleteConfirm(true);
  };

  const handleConfirmCategoryDelete = async () => {
    if (!categoriaToDelete) return;

    setIsDeleting(true);
    try {
      await deactivateGastoCategoria(categoriaToDelete.id);
      onRefresh();
      setShowDeleteConfirm(false);
      setCategoriaToDelete(null);
    } catch (err) {
      console.error("Error al desactivar categoria:", err);
      alert("Error al desactivar la categoria");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCategorySaved = () => {
    onRefresh();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="category-config-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="category-config-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="category-config-header">
              <div>
                <h2 className="category-config-title">Configurar categorías</h2>
              </div>
              <button className="category-config-close" onClick={onClose}>
                <Icons.XIcon size={20} />
              </button>
            </div>

            <div className="category-config-body">
              {categoriasPadre.length === 0 ? (
                <div className="empty-state">
                  <Icons.LayersIcon size={48} />
                  <p>No hay categorías de gastos</p>
                  <span>Crea categorías para comenzar a clasificar tus gastos.</span>
                </div>
              ) : (
                <div className="category-config-panels">
                  <div className="category-panel-left">
                    <div className="category-panel-left-header">
                      <span className="category-panel-label">Categorias</span>
                      <button className="btn-new-category" onClick={handleCreateCategory}>
                        <Icons.PlusIcon size={14} /> Nueva
                      </button>
                    </div>
                    <div className="category-panel-list">
                      {categoriasPadre.map((item) => {
                        const subcategorias = subcategoriasPorPadre.get(item.id) || [];
                        const isActive = selectedCategoryId === item.id;

                        return (
                          <button
                            key={item.id}
                            type="button"
                            className={`category-panel-item ${isActive ? "active" : ""}`}
                            onClick={() => setSelectedCategoryId(item.id)}
                          >
                            <span className="category-panel-dot" />
                            <span className="category-panel-info">
                              <span className="category-panel-name">{item.nombre}</span>
                              <span className="category-panel-meta">
                                {subcategorias.length > 0
                                  ? `${subcategorias.length} subcategoria${subcategorias.length === 1 ? "" : "s"}`
                                  : "Sin subcategorias"}
                              </span>
                            </span>
                            <Icons.FolderTreeIcon size={14} className="category-panel-arrow" />
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="category-panel-right">
                    <div className="category-panel-right-header">
                      <div className="category-panel-right-info">
                        <h3 className="category-panel-right-title">
                          {selectedCategoriaPadre?.nombre || "Selecciona una categoria"}
                        </h3>
                        {selectedCategoriaPadre && (
                          <span className="category-panel-right-meta">
                            {subcategoriasSeleccionadas.length} subcategoria{subcategoriasSeleccionadas.length === 1 ? "" : "s"}
                          </span>
                        )}
                      </div>
                      <div className="category-panel-right-actions">
                        <button
                          className="btn-action btn-edit"
                          onClick={() => selectedCategoriaPadre && handleEditCategory(selectedCategoriaPadre)}
                          disabled={!selectedCategoriaPadre}
                          title="Editar"
                        >
                          <Icons.EditIcon size={16} />
                        </button>
                        <button
                          className="btn-action btn-delete"
                          onClick={() => selectedCategoriaPadre && handleDeleteCategoryClick(selectedCategoriaPadre)}
                          disabled={!selectedCategoriaPadre}
                          title="Desactivar"
                        >
                          <Icons.TrashIcon size={16} />
                        </button>
                        <div className="category-panel-divider" />
                        <button
                          className="btn-add-subcategory"
                          onClick={handleCreateSubcategory}
                          disabled={!selectedCategoriaPadre}
                        >
                          <Icons.PlusIcon size={14} /> Subcategoria
                        </button>
                      </div>
                    </div>

                    <div className="category-panel-sublist">
                      {!selectedCategoriaPadre ? (
                        <div className="empty-state">
                          <Icons.FolderTreeIcon size={48} />
                          <p>Selecciona una categoria</p>
                          <span>Visualiza y administra las subcategorias desde este panel.</span>
                        </div>
                      ) : subcategoriasSeleccionadas.length === 0 ? (
                        <div className="empty-state">
                          <Icons.FolderTreeIcon size={48} />
                          <p>Sin subcategorias</p>
                          <span>Agrega una subcategoria para organizar mejor tus gastos.</span>
                        </div>
                      ) : (
                        subcategoriasSeleccionadas.map((subcat) => (
                          <div key={subcat.id} className="category-panel-subitem">
                            <span className="category-panel-bullet">•</span>
                            <span className="category-panel-subname">{subcat.nombre}</span>
                            <div className="category-panel-subactions">
                              <button
                                className="btn-action btn-edit"
                                onClick={() => handleEditCategory(subcat)}
                                title="Editar"
                              >
                                <Icons.EditIcon size={16} />
                              </button>
                              <button
                                className="btn-action btn-delete"
                                onClick={() => handleDeleteCategoryClick(subcat)}
                                disabled={!subcat.activo}
                                title="Desactivar"
                              >
                                <Icons.TrashIcon size={16} />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          <ExpenseCategoryModal
            categoria={selectedCategoria}
            categorias={categorias}
            isOpen={isCategoryModalOpen}
            defaultParentId={defaultParentId}
            onClose={() => setIsCategoryModalOpen(false)}
            onSave={handleCategorySaved}
          />

          <ConfirmDialog
            isOpen={showDeleteConfirm}
            title="¿Desactivar categoria?"
            message={`¿Está seguro de que desea desactivar la categoría "${categoriaToDelete?.nombre}"?`}
            confirmText="Desactivar"
            cancelText="Cancelar"
            confirmDisabled={isDeleting}
            cancelDisabled={isDeleting}
            onConfirm={handleConfirmCategoryDelete}
            onCancel={() => setShowDeleteConfirm(false)}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ExpenseCategoryConfigModal;

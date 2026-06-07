import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import * as Icons from "../components/shared/Icons";
import ErrorAlert from "../components/shared/ErrorAlert";
import ConfirmDialog from "../components/shared/ConfirmDialog";
import ExpenseCategoryModal from "../components/ExpenseCategoryModal";
import type { ExpenseCategory } from "../types/expense_category";
import {
  deactivateGastoCategoria,
  getGastosCategorias,
} from "../services/gastosCategoriasService";
import "../styles/expense-categories.css";

const ExpenseCategoriesPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [categorias, setCategorias] = useState<ExpenseCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState<ExpenseCategory | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [categoriaToDelete, setCategoriaToDelete] = useState<ExpenseCategory | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchCategorias = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getGastosCategorias();
      setCategorias(data || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`Error al cargar: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategorias();
  }, []);

  const categoriasPorId = useMemo(() => {
    return new Map(categorias.map((item) => [item.id, item]));
  }, [categorias]);

  const categoriasOrdenadas = useMemo(() => {
    const childrenMap = new Map<number | null, ExpenseCategory[]>();
    categorias.forEach((item) => {
      const key = item.padre_id ?? null;
      if (!childrenMap.has(key)) {
        childrenMap.set(key, []);
      }
      childrenMap.get(key)?.push(item);
    });

    childrenMap.forEach((items) => items.sort((a, b) => a.nombre.localeCompare(b.nombre)));

    const ordered: { item: ExpenseCategory; level: number }[] = [];
    const walk = (parentId: number | null, level: number) => {
      const items = childrenMap.get(parentId) || [];
      items.forEach((child) => {
        ordered.push({ item: child, level });
        walk(child.id, level + 1);
      });
    };

    walk(null, 0);
    return ordered;
  }, [categorias]);

  const handleCreateClick = () => {
    setSelectedCategoria({
      id: 0,
      nombre: "",
      descripcion: "",
      padre_id: null,
      activo: true,
      fecha_creacion: "",
      fecha_actualizacion: "",
    });
    setIsModalOpen(true);
  };

  const handleEdit = (categoria: ExpenseCategory) => {
    setSelectedCategoria(categoria);
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    setIsModalOpen(false);
    setSelectedCategoria(null);
    await fetchCategorias();
  };

  const handleDeleteClick = (categoria: ExpenseCategory) => {
    setCategoriaToDelete(categoria);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!categoriaToDelete) return;

    setIsDeleting(true);
    try {
      await deactivateGastoCategoria(categoriaToDelete.id);
      setShowDeleteConfirm(false);
      setCategoriaToDelete(null);
      await fetchCategorias();
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
      <div className="expense-categories-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta pagina.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="expense-categories-container">
      <header className="expense-categories-hero">
        <div>
          <p className="expense-kicker">Configuracion</p>
          <h1>Categoria de Gastos</h1>
          <p>Organiza jerarquias para analizar egresos en el dashboard.</p>
        </div>
        <button className="btn-primary" onClick={handleCreateClick}>
          <Icons.PlusIcon size={16} /> Nueva categoria
        </button>
      </header>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      <ExpenseCategoryModal
        categoria={selectedCategoria}
        categorias={categorias}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
      />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Desactivar categoria"
        message={
          categoriaToDelete
            ? `Se desactivara ${categoriaToDelete.nombre}. Puedes reactivarla luego.`
            : "Se desactivara la categoria."
        }
        warning="Esta accion no elimina la categoria del historial de gastos."
        confirmText={isDeleting ? "Desactivando..." : "Desactivar"}
        confirmDanger
        confirmDisabled={isDeleting}
        cancelDisabled={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />

      <div className="expense-categories-table">
        {loading ? (
          <p className="loading-message">Cargando categorias...</p>
        ) : categoriasOrdenadas.length === 0 ? (
          <div className="empty-state">
            <Icons.LayersIcon size={48} />
            <p>No hay categorias de gastos</p>
            <span>Define jerarquias para iniciar el control de egresos.</span>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Categoria</th>
                <th>Padre</th>
                <th>Descripcion</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {categoriasOrdenadas.map(({ item, level }) => {
                const padre = item.padre_id ? categoriasPorId.get(item.padre_id) : null;
                return (
                  <tr key={item.id} className={!item.activo ? "is-inactive" : ""}>
                    <td>
                      <div className="categoria-nombre" style={{ paddingLeft: `${level * 18}px` }}>
                        {level > 0 && <span className="categoria-indent">▸</span>}
                        {item.nombre}
                      </div>
                    </td>
                    <td>{padre?.nombre || "Raiz"}</td>
                    <td className="categoria-descripcion">{item.descripcion || "-"}</td>
                    <td>
                      <span className={`badge ${item.activo ? "active" : "inactive"}`}>
                        {item.activo ? "Activa" : "Inactiva"}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn-action btn-edit"
                          onClick={() => handleEdit(item)}
                        >
                          <Icons.EditIcon size={16} />
                          Editar
                        </button>
                        <button
                          className="btn-action btn-delete"
                          onClick={() => handleDeleteClick(item)}
                          disabled={!item.activo}
                        >
                          <Icons.TrashIcon size={16} />
                          Desactivar
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default ExpenseCategoriesPage;

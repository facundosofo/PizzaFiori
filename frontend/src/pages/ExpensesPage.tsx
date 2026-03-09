import { useEffect, useMemo, useState } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import { useAuth } from "../contexts/AuthContext";
import * as Icons from "../components/shared/Icons";
import DateRangeInput from "../components/shared/DateRangeInput";
import FilterBar from "../components/shared/FilterBar";
import ErrorAlert from "../components/shared/ErrorAlert";
import ConfirmDialog from "../components/shared/ConfirmDialog";
import ExpenseModal from "../components/ExpenseModal";
import ExpenseCategoryConfigModal from "../components/ExpenseCategoryConfigModal";
import type { Expense } from "../types/expense";
import type { ExpenseCategory } from "../types/expense_category";
import { getGastos, deleteGasto } from "../services/gastosService";
import { getGastosCategorias } from "../services/gastosCategoriasService";
import { formatCurrency, formatDateDisplay } from "../utils/formatters";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/shared/datepicker-custom.css";
import "../styles/expenses.css";

registerLocale("es", es);

const ExpensesPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [gastos, setGastos] = useState<Expense[]>([]);
  const [categorias, setCategorias] = useState<ExpenseCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedGasto, setSelectedGasto] = useState<Expense | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [gastoToDelete, setGastoToDelete] = useState<Expense | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showCategoryConfig, setShowCategoryConfig] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [limit] = useState(10);

  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [dateFrom, dateTo] = dateRange;
  const [categoriaFiltro, setCategoriaFiltro] = useState<string>("");
  const [subcategoriaFiltro, setSubcategoriaFiltro] = useState<string>("");

  // Applied filters (only applied on Search click)
  const [appliedFilters, setAppliedFilters] = useState({
    dateFrom: null as Date | null,
    dateTo: null as Date | null,
    categoriaFiltro: "",
    subcategoriaFiltro: "",
  });

  const categoriasActivas = useMemo(
    () => (Array.isArray(categorias) ? categorias : []).filter((item) => item.activo),
    [categorias]
  );

  const categoriasPadre = useMemo(
    () => categoriasActivas.filter((item) => !item.padre_id),
    [categoriasActivas]
  );

  const subcategoriasPorPadre = useMemo(() => {
    const map = new Map<number, ExpenseCategory[]>();
    categoriasActivas
      .filter((item) => item.padre_id)
      .forEach((item) => {
        const parentId = item.padre_id as number;
        if (!map.has(parentId)) {
          map.set(parentId, []);
        }
        map.get(parentId)?.push(item);
      });
    map.forEach((items) => items.sort((a, b) => a.nombre.localeCompare(b.nombre)));
    return map;
  }, [categoriasActivas]);

  const subcategoriasDisponibles = useMemo(() => {
    if (!categoriaFiltro) return [];
    return subcategoriasPorPadre.get(Number(categoriaFiltro)) || [];
  }, [categoriaFiltro, subcategoriasPorPadre]);

  const categoriasPorId = useMemo(() => {
    return new Map(categorias.map((item) => [item.id, item]));
  }, [categorias]);

  const sortedGastos = useMemo(() => {
    const parseFecha = (value: string) => {
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const [year, month, day] = value.split("-").map(Number);
        return new Date(year, month - 1, day).getTime();
      }
      return new Date(value).getTime();
    };

    return (Array.isArray(gastos) ? [...gastos] : []).sort((a, b) => parseFecha(b.fecha_pago) - parseFecha(a.fecha_pago));
  }, [gastos]);

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(sortedGastos.length / limit));
  }, [sortedGastos.length, limit]);

  const paginatedGastos = useMemo(() => {
    const start = (currentPage - 1) * limit;
    return sortedGastos.slice(start, start + limit);
  }, [sortedGastos, currentPage, limit]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const catId = appliedFilters.subcategoriaFiltro
        ? Number(appliedFilters.subcategoriaFiltro)
        : appliedFilters.categoriaFiltro
          ? Number(appliedFilters.categoriaFiltro)
          : null;

      const [categoriasData, gastosData] = await Promise.all([
        getGastosCategorias(),
        getGastos(appliedFilters.dateFrom, appliedFilters.dateTo, catId),
      ]);

      setCategorias(categoriasData || []);
      setGastos(gastosData || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`Error al cargar: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [appliedFilters]);

  useEffect(() => {
    setCurrentPage(1);
  }, [appliedFilters]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const handleCalendarClose = () => {
    if (dateFrom && !dateTo) {
      const today = new Date();
      setDateRange([dateFrom, today]);
    }
  };

  const handleSearch = () => {
    setAppliedFilters({
      dateFrom,
      dateTo,
      categoriaFiltro,
      subcategoriaFiltro,
    });
    setCurrentPage(1);
  };

  const handleClear = () => {
    setDateRange([null, null]);
    setCategoriaFiltro("");
    setSubcategoriaFiltro("");
    setAppliedFilters({
      dateFrom: null,
      dateTo: null,
      categoriaFiltro: "",
      subcategoriaFiltro: "",
    });
    setCurrentPage(1);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const handleGoToPage = (page: number) => {
    setCurrentPage(page);
  };

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxPagesToShow = 5;

    if (totalPages <= maxPagesToShow + 2) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);

      if (currentPage > 3) {
        pages.push("...");
      }

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push("...");
      }

      pages.push(totalPages);
    }

    return pages;
  };

  const handleCreateClick = () => {
    setSelectedGasto({
      id: 0,
      categoria_gasto_id: 0,
      descripcion: "",
      monto: 0,
      fecha_pago: "",
      activo: true,
      fecha_creacion: "",
      fecha_actualizacion: "",
    });
    setIsModalOpen(true);
  };

  const handleEdit = (gasto: Expense) => {
    setSelectedGasto(gasto);
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    setIsModalOpen(false);
    setSelectedGasto(null);
    await fetchData();
  };

  const handleDeleteClick = (gasto: Expense) => {
    setGastoToDelete(gasto);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!gastoToDelete) return;

    setIsDeleting(true);
    try {
      await deleteGasto(gastoToDelete.id);
      setShowDeleteConfirm(false);
      setGastoToDelete(null);
      await fetchData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`No se pudo eliminar: ${msg}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedGasto(null);
  };

  if (!isAdmin) {
    return (
      <div className="expenses-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta pagina.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="expenses-container">
      <header className="page-header">
        <h1 className="page-title">Gastos</h1>
        <div className="page-header-actions">
          <button className="btn-new-sale" onClick={handleCreateClick}>
            <Icons.PlusIcon size={16} /> Cargar gasto
          </button>
          <button
            className="btn-config"
            onClick={() => setShowCategoryConfig(true)}
          >
            <Icons.FolderTreeIcon size={16} />
            Categorías
          </button>
        </div>
      </header>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      <ExpenseModal
        gasto={selectedGasto}
        categorias={categoriasActivas}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
      />

      <ExpenseCategoryConfigModal
        isOpen={showCategoryConfig}
        onClose={() => setShowCategoryConfig(false)}
        categorias={categorias}
        onRefresh={fetchData}
      />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={<><Icons.WarningIcon size={18} /> Eliminar Gasto</>}
        message={
          gastoToDelete ? (
            <>
              ¿Está seguro que desea eliminar el gasto por{" "}
              <strong style={{ color: "#ffffff" }}>{formatCurrency(gastoToDelete.monto)}</strong>?
            </>
          ) : (
            "¿Está seguro que desea eliminar el gasto seleccionado?"
          )
        }
        confirmText={isDeleting ? "Eliminando..." : "Eliminar"}
        cancelText="Cancelar"
        confirmDanger
        confirmDisabled={isDeleting}
        cancelDisabled={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />

      <FilterBar onSearch={handleSearch} onClear={handleClear}>
        <div className="filter-group filter-group-range">
          <label htmlFor="date-range">Rango de fechas</label>
          <DatePicker
            id="date-range"
            selectsRange={true}
            startDate={dateFrom}
            endDate={dateTo}
            onChange={(update) => {
              setDateRange(update as [Date | null, Date | null]);
            }}
            onCalendarClose={handleCalendarClose}
            dateFormat="dd/MM/yyyy"
            maxDate={new Date()}
            placeholderText="Seleccionar Desde - Hasta"
            calendarClassName="custom-calendar"
            showMonthDropdown
            showYearDropdown
            dropdownMode="select"
            popperPlacement="bottom-start"
            autoComplete="off"
            monthsShown={1}
            locale="es"
            formatWeekDay={(day) => day.charAt(0).toUpperCase()}
            customInput={<DateRangeInput placeholder="Seleccionar Desde - Hasta" />}
          />
        </div>

        <div className="filter-group">
          <label>Categoria</label>
          <select
            className="filter-select"
            value={categoriaFiltro}
            onChange={(e) => {
              setCategoriaFiltro(e.target.value);
              setSubcategoriaFiltro("");
            }}
          >
            <option value="">Todas</option>
            {categoriasPadre.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </div>

        {subcategoriasDisponibles.length > 0 && (
          <div className="filter-group">
            <label>Subcategoria</label>
            <select
              className="filter-select"
              value={subcategoriaFiltro}
              onChange={(e) => setSubcategoriaFiltro(e.target.value)}
            >
              <option value="">Todas</option>
              {subcategoriasDisponibles.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nombre}
                </option>
              ))}
            </select>
          </div>
        )}
      </FilterBar>

      <div className="expenses-table">
        {loading ? (
          <p className="loading-message">Cargando gastos...</p>
        ) : sortedGastos.length === 0 ? (
          <div className="empty-state">
            <Icons.PesoIcon size={48} />
            <p>No hay gastos registrados</p>
            <span>Registra egresos para visualizar tu margen operativo.</span>
          </div>
        ) : (
          <>
            <div className="expenses-table-header">
              <div className="expenses-col-date">Fecha</div>
              <div className="expenses-col-category">Categoria</div>
              <div className="expenses-col-subcategory">Subcategoria</div>
              <div className="expenses-col-description">Descripcion</div>
              <div className="expenses-col-amount">Monto</div>
              <div className="expenses-col-actions">Acciones</div>
            </div>

            {paginatedGastos.map((gasto) => {
              const categoria = categorias.find((c) => c.id === gasto.categoria_gasto_id);
              const categoriaPadre = categoria?.padre_id
                ? categoriasPorId.get(categoria.padre_id)
                : null;
              return (
                <div key={gasto.id} className="expenses-table-row">
                  <div className="expenses-col-date">{formatDateDisplay(gasto.fecha_pago)}</div>
                  <div className="expenses-col-category">
                    {categoriaPadre?.nombre || categoria?.nombre || "-"}
                  </div>
                  <div className="expenses-col-subcategory">
                    {categoriaPadre ? categoria?.nombre : "-"}
                  </div>
                  <div className="expenses-col-description gasto-descripcion">
                    {gasto.descripcion || "-"}
                  </div>
                  <div className="expenses-col-amount gasto-monto">{formatCurrency(gasto.monto)}</div>
                  <div className="expenses-col-actions">
                    <button
                      className="sales-action-btn edit"
                      onClick={() => handleEdit(gasto)}
                      title="Editar gasto"
                    >
                      <Icons.EditIcon size={18} />
                    </button>
                    <button
                      className="sales-action-btn delete"
                      onClick={() => handleDeleteClick(gasto)}
                      title="Eliminar gasto"
                    >
                      <Icons.TrashIcon size={18} />
                    </button>
                  </div>
                </div>
              );
            })}

            <div className="sales-pagination">
              <button
                className="sales-pagination-btn nav"
                onClick={handlePrevPage}
                disabled={currentPage === 1}
              >
                ← Anterior
              </button>

              <div className="sales-pagination-numbers">
                {getPageNumbers().map((page, index) => (
                  typeof page === "number" ? (
                    <button
                      key={index}
                      className={`sales-pagination-number ${currentPage === page ? "active" : ""}`}
                      onClick={() => handleGoToPage(page)}
                    >
                      {page}
                    </button>
                  ) : (
                    <span key={index} className="sales-pagination-ellipsis">
                      {page}
                    </span>
                  )
                ))}
              </div>

              <button
                className="sales-pagination-btn nav"
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
              >
                Siguiente →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ExpensesPage;

import { forwardRef, useEffect, useMemo, useState } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import { Calendar } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import type { AuditLog } from "../services/auditService";
import { searchAuditLogs } from "../services/auditService";
import userManagementService from "../services/userManagementService";
import type { User } from "../services/userService";
import { formatDateTimeDisplay, validateDateRange } from "../utils/formatters";
import ErrorAlert from "../components/shared/ErrorAlert";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import * as Icons from "../components/shared/Icons";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/shared/datepicker-custom.css";
import "../styles/audit.css";

registerLocale("es", es);

type DateRangeInputProps = {
  value?: string;
  onClick?: () => void;
  placeholder?: string;
};

const DateRangeInput = forwardRef<HTMLButtonElement, DateRangeInputProps>(
  ({ value, onClick, placeholder }, ref) => (
    <button
      type="button"
      className="audit-filter-date-input"
      onClick={onClick}
      ref={ref}
    >
      <Calendar size={16} className="audit-filter-date-icon" />
      <span className="audit-filter-date-label">{value || placeholder}</span>
    </button>
  )
);

DateRangeInput.displayName = "DateRangeInput";

const ENTITY_OPTIONS = [
  { label: "Todas", value: "" },
  { label: "Producto", value: "Product" },
  { label: "Categoría", value: "Category" },
  { label: "Oferta", value: "Offer" },
  { label: "Venta", value: "Sale" },
  { label: "Usuario", value: "User" },
];

const ACTION_OPTIONS = [
  { label: "Todas", value: "" },
  { label: "Creado", value: "CREATE" },
  { label: "Actualizado", value: "UPDATE" },
  { label: "Eliminado", value: "DELETE" },
];

const translateEntityType = (entityType: string): string => {
  const translations: Record<string, string> = {
    Product: "Producto",
    Category: "Categoría",
    Offer: "Oferta",
    Sale: "Venta",
    User: "Usuario",
  };
  return translations[entityType] || entityType;
};

const translateAction = (action: string): string => {
  const translations: Record<string, string> = {
    CREATE: "Creado",
    UPDATE: "Actualizado",
    DELETE: "Eliminado",
  };
  return translations[action] || action;
};

const AuditPage = () => {
  const { user, isLoading: authLoading } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  const [records, setRecords] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [username, setUsername] = useState("");
  const [entityType, setEntityType] = useState("");
  const [action, setAction] = useState("");

  const [limit, setLimit] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const [appliedFilters, setAppliedFilters] = useState({
    startDate: null as Date | null,
    endDate: null as Date | null,
    username: "",
    entityType: "",
    action: "",
  });

  const [dateFrom, dateTo] = dateRange;

  const offset = useMemo(() => (currentPage - 1) * limit, [currentPage, limit]);

  const userOptions = useMemo(() => {
    return [...users].sort((a, b) => a.username.localeCompare(b.username));
  }, [users]);

  useEffect(() => {
    if (!isAdmin) {
      return;
    }

    const fetchUsers = async () => {
      try {
        const data = await userManagementService.getAllUsers();
        setUsers(data || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        setError(`Error al cargar usuarios: ${errorMessage}`);
      }
    };

    fetchUsers();
  }, [isAdmin]);

  useEffect(() => {
    if (!isAdmin) {
      return;
    }

    const fetchAudit = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await searchAuditLogs({
          startDate: appliedFilters.startDate,
          endDate: appliedFilters.endDate,
          username: appliedFilters.username || undefined,
          entityType: appliedFilters.entityType || undefined,
          action: appliedFilters.action || undefined,
          limit,
          offset,
        });

        setRecords(data.records || []);
        setTotalRecords(data.total || 0);
        setTotalPages(Math.max(1, Math.ceil((data.total || 0) / limit)));
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        setError(`Error al cargar auditoria: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAudit();
  }, [appliedFilters, limit, offset, isAdmin]);

  const handleSearch = () => {
    setError(null);

    const validationError = validateDateRange(dateFrom, dateTo);
    if (validationError) {
      setError(validationError);
      return;
    }

    setAppliedFilters({
      startDate: dateFrom,
      endDate: dateTo,
      username: username.trim(),
      entityType,
      action,
    });

    setCurrentPage(1);
  };

  const handleClear = () => {
    setDateRange([null, null]);
    setUsername("");
    setEntityType("");
    setAction("");
    setAppliedFilters({
      startDate: null,
      endDate: null,
      username: "",
      entityType: "",
      action: "",
    });
    setCurrentPage(1);
  };

  const handleToggleExpand = (auditId: number) => {
    setExpandedIds((prev) => {
      const updated = new Set(prev);
      if (updated.has(auditId)) {
        updated.delete(auditId);
      } else {
        updated.add(auditId);
      }
      return updated;
    });
  };

  const getChangeSummary = (changes: Record<string, any>) => {
    if (!changes || typeof changes !== "object") {
      return "Sin cambios";
    }

    if (changes.new || changes.old) {
      const snapshot = changes.new || changes.old || {};
      const count = Object.keys(snapshot).length;
      return `Snapshot (${count})`;
    }

    const keys = Object.keys(changes);
    if (keys.length === 0) {
      return "Sin cambios";
    }

    const preview = keys.slice(0, 3).join(", ");
    const suffix = keys.length > 3 ? ` +${keys.length - 3}` : "";
    return `${preview}${suffix}`;
  };

  const formatValue = (value: any) => {
    if (value === null || value === undefined) {
      return "—";
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }

    return JSON.stringify(value, null, 2);
  };

  const renderChangeRows = (changes: Record<string, any>) => {
    if (!changes || typeof changes !== "object") {
      return null;
    }

    if (changes.new || changes.old) {
      const snapshot = changes.new || changes.old || {};
      return Object.entries(snapshot).map(([field, value]) => (
        <div className="audit-detail-row" key={field}>
          <div className="audit-detail-field">{field}</div>
          <pre className="audit-detail-value audit-detail-value-span">
            {formatValue(value)}
          </pre>
        </div>
      ));
    }

    return Object.entries(changes).map(([field, value]) => {
      const hasOldNew =
        value &&
        typeof value === "object" &&
        Object.prototype.hasOwnProperty.call(value, "old") &&
        Object.prototype.hasOwnProperty.call(value, "new");

      if (hasOldNew) {
        return (
          <div className="audit-detail-row" key={field}>
            <div className="audit-detail-field">{field}</div>
            <pre className="audit-detail-value">{formatValue(value.old)}</pre>
            <pre className="audit-detail-value">{formatValue(value.new)}</pre>
          </div>
        );
      }

      return (
        <div className="audit-detail-row" key={field}>
          <div className="audit-detail-field">{field}</div>
          <pre className="audit-detail-value audit-detail-value-span">
            {formatValue(value)}
          </pre>
        </div>
      );
    });
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

  const today = new Date();

  if (authLoading) {
    return (
      <div className="audit-container">
        <div className="access-denied">
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="audit-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta pagina.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="audit-container">
      <div className="page-header">
        <h1 className="page-title">Auditoria</h1>
      </div>

      <div className="audit-filters">
        <div className="audit-filters-row">
          <div className="audit-filter-group audit-filter-group-range">
            <label htmlFor="audit-date-range">Rango de fechas</label>
            <DatePicker
              id="audit-date-range"
              selectsRange={true}
              startDate={dateFrom}
              endDate={dateTo}
              onChange={(update) => {
                setDateRange(update as [Date | null, Date | null]);
              }}
              onCalendarClose={() => {
                if (dateFrom && !dateTo) {
                  setDateRange([dateFrom, today]);
                }
              }}
              dateFormat="dd/MM/yyyy"
              maxDate={today}
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

          <div className="audit-filter-group">
            <label htmlFor="audit-username">Usuario</label>
            <select
              id="audit-username"
              className="audit-filter-select"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            >
              <option value="">Todos</option>
              {userOptions.map((option) => (
                <option key={option.id} value={option.username}>
                  {option.username} - {option.first_name} {option.last_name}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-group">
            <label htmlFor="audit-entity">Entidad</label>
            <select
              id="audit-entity"
              className="audit-filter-select"
              value={entityType}
              onChange={(event) => setEntityType(event.target.value)}
            >
              {ENTITY_OPTIONS.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-group">
            <label htmlFor="audit-action">Accion</label>
            <select
              id="audit-action"
              className="audit-filter-select"
              value={action}
              onChange={(event) => setAction(event.target.value)}
            >
              {ACTION_OPTIONS.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-group audit-filter-group-limit">
            <label htmlFor="audit-limit">Mostrar</label>
            <select
              id="audit-limit"
              className="audit-filter-select"
              value={limit}
              onChange={(event) => {
                setLimit(Number(event.target.value));
                setCurrentPage(1);
              }}
            >
              {[10, 25, 50, 100].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-actions">
            <button className="audit-filter-btn search" onClick={handleSearch}>
              <Icons.SearchIcon size={18} />
              <span>Buscar</span>
            </button>
            <button className="audit-filter-btn clear" onClick={handleClear}>
              <Icons.XIcon size={18} />
              <span>Limpiar</span>
            </button>
          </div>
        </div>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      {loading ? (
        <div className="audit-loading">
          {Array.from({ length: 8 }).map((_, index) => (
            <SkeletonLoader key={index} />
          ))}
        </div>
      ) : records.length === 0 ? (
        <div className="audit-empty">
          <div className="audit-empty-icon">
            <Icons.LayersIcon size={36} />
          </div>
          <p>No se encontraron registros de auditoria</p>
        </div>
      ) : (
        <>
          <div className="audit-table">
            <div className="audit-table-header">
              <div className="audit-col-date">Fecha</div>
              <div className="audit-col-user">Usuario</div>
              <div className="audit-col-entity">Entidad</div>
              <div className="audit-col-action">Accion</div>
              <div className="audit-col-changes">Cambios</div>
              <div className="audit-col-toggle"></div>
            </div>

            {records.map((record) => {
              const isExpanded = expandedIds.has(record.id);
              return (
                <div key={record.id} className="audit-table-row">
                  <div className="audit-col-date">
                    {formatDateTimeDisplay(record.timestamp)}
                  </div>
                  <div className="audit-col-user">{record.username}</div>
                  <div className="audit-col-entity">{translateEntityType(record.entity_type)}</div>
                  <div className="audit-col-action">
                    <span className={`audit-action-badge ${record.action.toLowerCase()}`}>
                      {translateAction(record.action)}
                    </span>
                  </div>
                  <div className="audit-col-changes">{getChangeSummary(record.changes)}</div>
                  <div className="audit-col-toggle">
                    <button
                      className="audit-toggle-btn"
                      onClick={() => handleToggleExpand(record.id)}
                      aria-label={isExpanded ? "Ocultar detalles" : "Ver detalles"}
                    >
                      {isExpanded ? (
                        <Icons.ChevronDownIcon size={18} />
                      ) : (
                        <Icons.ChevronRightIcon size={18} />
                      )}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="audit-detail">
                      <div className="audit-detail-header">
                        <span>Detalle de cambios</span>
                      </div>
                      <div
                        className={`audit-detail-grid${
                          record.changes?.new || record.changes?.old ? " is-snapshot" : ""
                        }`}
                      >
                        {record.changes?.new || record.changes?.old ? (
                          <div className="audit-detail-row audit-detail-head">
                            <div className="audit-detail-field">Campo</div>
                            <div className="audit-detail-value audit-detail-value-span">Valor</div>
                          </div>
                        ) : (
                          <div className="audit-detail-row audit-detail-head">
                            <div className="audit-detail-field">Campo</div>
                            <div className="audit-detail-value">Anterior</div>
                            <div className="audit-detail-value">Nuevo</div>
                          </div>
                        )}
                        {renderChangeRows(record.changes)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="audit-pagination">
            <button
              className="audit-pagination-btn nav"
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage <= 1}
            >
              Anterior
            </button>

            <div className="audit-pagination-numbers">
              {getPageNumbers().map((page, index) =>
                typeof page === "number" ? (
                  <button
                    key={page}
                    className={`audit-pagination-number ${
                      currentPage === page ? "active" : ""
                    }`}
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </button>
                ) : (
                  <span key={`ellipsis-${index}`} className="audit-pagination-ellipsis">
                    {page}
                  </span>
                )
              )}
            </div>

            <button
              className="audit-pagination-btn nav"
              onClick={() =>
                setCurrentPage((prev) => Math.min(prev + 1, totalPages))
              }
              disabled={currentPage >= totalPages}
            >
              Siguiente
            </button>

            <div className="audit-pagination-info">
              {totalRecords} registros
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AuditPage;

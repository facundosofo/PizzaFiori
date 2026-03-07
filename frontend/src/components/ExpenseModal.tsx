import { forwardRef, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import { Calendar } from "lucide-react";
import * as Icons from "./shared/Icons";
import type { Expense } from "../types/expense";
import type { ExpenseCategory } from "../types/expense_category";
import { createGasto, updateGasto } from "../services/gastosService";
import { formatCurrency, parseCurrencyInput, formatDateYMD } from "../utils/formatters";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/shared/datepicker-custom.css";
import "../styles/expense-modal.css";

registerLocale("es", es);

type DateInputProps = {
  value?: string;
  onClick?: () => void;
  placeholder?: string;
};

const DateInput = forwardRef<HTMLButtonElement, DateInputProps>(
  ({ value, onClick, placeholder }, ref) => (
    <button
      type="button"
      className="expense-date-input"
      onClick={onClick}
      ref={ref}
    >
      <Calendar size={16} className="expense-date-icon" />
      <span className="expense-date-label">{value || placeholder}</span>
    </button>
  )
);

DateInput.displayName = "DateInput";

interface ExpenseModalProps {
  gasto: Expense | null;
  categorias: ExpenseCategory[];
  isOpen: boolean;
  onClose: () => void;
  onSave?: (gasto: Expense) => void;
}

const ExpenseModal = ({
  gasto,
  categorias,
  isOpen,
  onClose,
  onSave,
}: ExpenseModalProps) => {
  const [categoriaId, setCategoriaId] = useState<number | "">("");
  const [subcategoriaId, setSubcategoriaId] = useState<number | "">("");
  const [descripcion, setDescripcion] = useState("");
  const [monto, setMonto] = useState<number>(0);
  const [montoInput, setMontoInput] = useState<string>("");
  const [fechaPago, setFechaPago] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDescripcionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDescripcion(e.target.value);
    // Auto-resize textarea
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  const handleDescripcionFocus = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  const isEditing = gasto && gasto.id > 0;

  const categoriasActivas = useMemo(
    () => categorias.filter((item) => item.activo),
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
    return map;
  }, [categoriasActivas]);

  const subcategoriasDisponibles = useMemo(() => {
    if (!categoriaId) return [];
    return subcategoriasPorPadre.get(Number(categoriaId)) || [];
  }, [categoriaId, subcategoriasPorPadre]);

  useEffect(() => {
    if (gasto && isOpen) {
      if (isEditing) {
        const categoria = categoriasActivas.find((item) => item.id === gasto.categoria_gasto_id);
        if (categoria?.padre_id) {
          setCategoriaId(categoria.padre_id);
          setSubcategoriaId(categoria.id);
        } else {
          setCategoriaId(gasto.categoria_gasto_id);
          setSubcategoriaId("");
        }
        setDescripcion(gasto.descripcion || "");
        setMonto(gasto.monto);
        setMontoInput(formatCurrency(gasto.monto));
        setFechaPago(gasto.fecha_pago ? new Date(gasto.fecha_pago) : null);
        setError("");
        return;
      }

      setCategoriaId("");
      setSubcategoriaId("");
      setDescripcion("");
      setMonto(0);
      setMontoInput("");
      setFechaPago(new Date());
      setError("");
      return;
    }

    if (!gasto && isOpen) {
      setCategoriaId("");
      setSubcategoriaId("");
      setDescripcion("");
      setMonto(0);
      setMontoInput("");
      setFechaPago(new Date());
      setError("");
    }
  }, [gasto, isOpen, categoriasActivas]);

  // Auto-resize textarea cuando cambia la descripción
  useEffect(() => {
    const textarea = document.getElementById("expense-descripcion") as HTMLTextAreaElement;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
    }
  }, [descripcion]);

  const handleSave = async () => {
    setError("");

    if (!categoriaId) {
      setError("Selecciona una categoria");
      return;
    }

    const subcategorias = subcategoriasPorPadre.get(Number(categoriaId)) || [];
    if (subcategorias.length > 0 && !subcategoriaId) {
      setError("Selecciona una subcategoria");
      return;
    }

    if (monto <= 0) {
      setError("Ingresa un monto valido");
      return;
    }

    if (!fechaPago) {
      setError("Selecciona una fecha de pago");
      return;
    }

    const fechaFormateada = formatDateYMD(fechaPago);

    setLoading(true);

    try {
      const payload = {
        categoria_gasto_id: Number(subcategoriaId || categoriaId),
        descripcion: descripcion.trim() || null,
        monto: monto,
        fecha_pago: fechaFormateada,
      };

      let saved: Expense;
      if (isEditing && gasto) {
        saved = await updateGasto(gasto.id, payload);
      } else {
        saved = await createGasto(payload);
      }

      onSave?.(saved);
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
          className="expense-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="expense-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="expense-modal-header">
              <div>
                <p className="expense-modal-eyebrow">Operacion</p>
                <h2 className="expense-modal-title">
                  {isEditing ? "Editar gasto" : "Nuevo gasto"}
                </h2>
              </div>
              <button
                className="expense-modal-close"
                onClick={onClose}
                disabled={loading}
              >
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="expense-modal-body">
              <div className="expense-form-group">
                <label className="expense-form-label">
                  Categoría <span className="expense-required">*</span>
                </label>
                <div className="expense-categories-grid">
                  {categoriasPadre.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={`expense-category-pill ${
                        categoriaId === item.id ? "active" : ""
                      }`}
                      onClick={() => {
                        setCategoriaId(item.id);
                        setSubcategoriaId("");
                      }}
                      disabled={loading}
                    >
                      {item.nombre}
                    </button>
                  ))}
                </div>
              </div>

              {subcategoriasDisponibles.length > 0 && (
                <div className="expense-form-group">
                  <label className="expense-form-label">
                    Subcategoría <span className="expense-required">*</span>
                  </label>
                  <div className="expense-categories-grid expense-subcategories-grid">
                    {subcategoriasDisponibles.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className={`expense-subcategory-pill ${
                          subcategoriaId === item.id ? "active" : ""
                        }`}
                        onClick={() => setSubcategoriaId(item.id)}
                        disabled={loading}
                      >
                        {item.nombre}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="expense-form-group">
                <label className="expense-form-label" htmlFor="expense-descripcion">
                  Descripción
                </label>
                <textarea
                  id="expense-descripcion"
                  className="expense-form-textarea"
                  value={descripcion}
                  onChange={handleDescripcionChange}
                  onFocus={handleDescripcionFocus}
                  placeholder="Detalle o nota interna"
                  maxLength={255}
                  disabled={loading}
                />
                <span className="expense-form-hint">
                  {descripcion.length}/255 caracteres
                </span>
              </div>

              <div className="expense-form-group">
                <label className="expense-form-label" htmlFor="expense-monto">
                  Monto <span className="expense-required">*</span>
                </label>
                <input
                  id="expense-monto"
                  type="text"
                  inputMode="decimal"
                  value={montoInput}
                  onFocus={(e) => {
                    setMontoInput(monto > 0 ? monto.toString().replace(".", ",") : "");
                    setTimeout(() => e.target.select(), 0);
                  }}
                  onChange={(e) => {
                    let value = e.target.value.replace(".", ",");
                    if (!/^\d*(,\d{0,2})?$/.test(value)) return;

                    setMontoInput(value);

                    const numeric = parseCurrencyInput(value);
                    if (!isNaN(numeric)) {
                      setMonto(numeric);
                    }
                  }}
                  onBlur={() => {
                    if (monto > 0) {
                      setMontoInput(formatCurrency(monto));
                    } else {
                      setMontoInput("");
                    }
                  }}
                  className="expense-form-input"
                  placeholder="$ 0,00"
                  disabled={loading}
                  autoComplete="off"
                />
              </div>

              <div className="expense-form-group">
                <label className="expense-form-label" htmlFor="expense-fecha">
                  Fecha de pago <span className="expense-required">*</span>
                </label>
                <DatePicker
                  id="expense-fecha"
                  selected={fechaPago}
                  onChange={(date: Date | null) => setFechaPago(date)}
                  dateFormat="dd/MM/yyyy"
                  maxDate={new Date()}
                  placeholderText="Seleccionar fecha"
                  calendarClassName="custom-calendar"
                  showMonthDropdown
                  showYearDropdown
                  dropdownMode="select"
                  locale="es"
                  disabled={loading}
                  customInput={<DateInput placeholder="Seleccionar fecha" />}
                />
              </div>

              {error && (
                <div className="expense-error">
                  <Icons.AlertCircleIcon size={20} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="expense-modal-footer">
              <button
                className="expense-btn cancel"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                className="expense-btn save"
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

export default ExpenseModal;

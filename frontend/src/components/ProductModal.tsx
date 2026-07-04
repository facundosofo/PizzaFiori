import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import * as Icons from './shared/Icons';
import ConfirmDialog from "./shared/ConfirmDialog";
import { updateProducto, createProducto } from "../services/productsService";
import { formatCurrency, parseCurrencyInput } from "../utils/formatters";
import "../styles/shared/forms.css";
import "../styles/shared/quantity-controls.css";
import "../styles/shared/add-button.css";
import "../styles/product-modal.css";
import env from "../config/env";

interface ProductModalProps {
  producto: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (producto: Product) => void;
  categorias?: ProductoCategoria[];
}

const ProductModal = ({
  producto,
  isOpen,
  onClose,
  onSave,
  categorias = [],
}: ProductModalProps) => {

  const [nombre, setNombre] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [imagen, setImagen] = useState<File | null>(null);
  const [previewImagen, setPreviewImagen] = useState("/placeholder.png");
  const [precios, setPrecios] = useState<Array<{ id?: number; cantidad: number; precio: number }>>([]);
  const [preciosInput, setPreciosInput] = useState<string[]>([]);
  const [cantidadInputs, setCantidadInputs] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showDeleteWarning, setShowDeleteWarning] = useState(false);
  const [priceIndexToDelete, setPriceIndexToDelete] = useState<number | null>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  const FRACTION_QUANTITIES = [0.125, 0.25, 0.5] as const;
  const isSameQuantity = (a: number, b: number) => Math.abs(a - b) < 1e-9;
  const isPortionQuantity = (cantidad: number) => FRACTION_QUANTITIES.some((value) => isSameQuantity(value, cantidad));
  const formatCantidadDisplay = (cantidad: number): string => {
    if (isSameQuantity(cantidad, 0.5)) return "1/2";
    if (isSameQuantity(cantidad, 0.25)) return "1/4";
    if (isSameQuantity(cantidad, 0.125)) return "1/8";
    return `${Math.round(cantidad)}`;
  };
  const parseCantidadInput = (value: string) => {
    const normalized = value.replace(",", ".").trim();
    const fractionMatch = normalized.match(/^(\d+)\s*\/\s*(\d+)$/);
    if (fractionMatch) {
      const numerator = parseInt(fractionMatch[1], 10);
      const denominator = parseInt(fractionMatch[2], 10);
      if (denominator > 0) {
        return numerator / denominator;
      }
    }
    const numeric = parseFloat(normalized);
    return Number.isFinite(numeric) ? numeric : NaN;
  };
  const getNearestPortion = (value: number): number => {
    let nearest: number = FRACTION_QUANTITIES[0];
    let minDiff = Infinity;
    FRACTION_QUANTITIES.forEach((portion) => {
      const diff = Math.abs(portion - value);
      if (diff < minDiff) {
        minDiff = diff;
        nearest = portion;
      }
    });
    return nearest;
  };
  const normalizeCantidad = (value: number) => {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      return 1;
    }
    if (numericValue < 1) {
      return getNearestPortion(numericValue);
    }
    return Math.max(1, Math.round(numericValue));
  };
  const getNextCantidad = (current: number) => {
    if (current < 1) {
      if (isSameQuantity(current, 0.125)) return 0.25;
      if (isSameQuantity(current, 0.25)) return 0.5;
      if (isSameQuantity(current, 0.5)) return 1;
      return 1;
    }
    return Math.round(current) + 1;
  };
  const getPrevCantidad = (current: number) => {
    if (current > 1) {
      return Math.round(current) - 1;
    }
    if (isSameQuantity(current, 1)) return 0.5;
    if (isSameQuantity(current, 0.5)) return 0.25;
    if (isSameQuantity(current, 0.25)) return 0.125;
    return 0.125;
  };
  const canDecreaseCantidad = (current: number, index: number) => {
    if (isSameQuantity(current, 0.125)) return false;
    if (isSameQuantity(current, 1)) {
      const hasOtherPortion = precios.some((p, i) => i !== index && p.cantidad < 1);
      return !hasOtherPortion;
    }
    return true;
  };
  const formatCantidadBadge = (cantidad: number) => {
    if (isSameQuantity(cantidad, 0.5)) return "Porción 1/2";
    if (isSameQuantity(cantidad, 0.25)) return "Porción 1/4";
    if (isSameQuantity(cantidad, 0.125)) return "Porción 1/8";
    return "";
  };

  // Auto-scroll al error cuando aparece
  useEffect(() => {
    if (error && errorRef.current) {
      errorRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [error]);

  useEffect(() => {
    if (producto && isOpen) {
      setNombre(producto.nombre || "");
      setCategoriaId(producto.categoria_id && producto.categoria_id > 0 ? producto.categoria_id.toString() : "");

      // Si es un producto nuevo (id = 0), inicializar con  un precio unitario
      if (producto.id === 0) {
        setPrecios([{ cantidad: 1, precio: 0 }]);
        setPreciosInput([""]);
        setCantidadInputs([formatCantidadDisplay(1)]);
      } else {
        setPrecios(producto.precios?.map(p => ({
          id: p.id,
          cantidad: Number(p.cantidad),
          precio: Number(p.precio),
        })) || []);
        setPreciosInput(producto.precios?.map(p => formatCurrency(Number(p.precio))) || []);
        setCantidadInputs(producto.precios?.map(p => formatCantidadDisplay(Number(p.cantidad))) || []);
      }

      setPreviewImagen(
        producto.imagen
          ? `${env.API_BASE_URL}/${producto.imagen}`
          : "/placeholder.png"
      );
      setImagen(null);
      setError("");
    }
  }, [producto, isOpen]);

  if (!producto) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (!selected.type.startsWith("image/")) {
        setError("Por favor, selecciona una imagen válida.");
        return;
      }

      if (selected.size > 5 * 1024 * 1024) {
        setError("La imagen no puede exceder 5MB.");
        return;
      }

      setImagen(selected);
      const reader = new FileReader();
      reader.onload = () => setPreviewImagen(reader.result as string);
      reader.onerror = () => setError("Error al leer la imagen.");
      reader.readAsDataURL(selected);
    }
  };

  const handleSave = async () => {
    setError("");

    if (!nombre.trim()) return setError("El nombre es requerido");
    if (nombre.trim().length > 50) return setError("El nombre no puede superar los 50 caracteres");
    if (!categoriaId) return setError("Selecciona una categoría");
    if (precios.length === 0) return setError("Debes agregar al menos un precio");
    if (precios.some(p => p.cantidad <= 0 || p.precio <= 0)) {
      return setError("Cantidad y precio deben ser mayores a 0");
    }
    if (precios.some(p => p.precio > 99_999_999.99)) {
      return setError("El precio no puede exceder 99.999.999,99");
    }

    const normalizedPrecios = precios.map((p) => ({
      ...p,
      cantidad: p.cantidad < 1 ? normalizeCantidad(p.cantidad) : Math.max(1, Math.round(p.cantidad)),
    }));

    if (!normalizedPrecios.every((p, index) => isSameQuantity(p.cantidad, precios[index].cantidad))) {
      setPrecios(normalizedPrecios);
      setCantidadInputs(normalizedPrecios.map((p) => formatCantidadDisplay(p.cantidad)));
    }

    // Validar que existe precio unitario
    const tienePrecioUnitario = normalizedPrecios.some(p => isSameQuantity(p.cantidad, 1));
    if (!tienePrecioUnitario) {
      return setError("Debe existir un precio unitario para el producto");
    }

    // Validar que no haya cantidades duplicadas
    const cantidades = normalizedPrecios.map(p => p.cantidad);
    const cantidadesUnicas = new Set(cantidades);
    if (cantidades.length !== cantidadesUnicas.size) {
      return setError("No se permiten cantidades duplicadas en los precios del producto");
    }

    const portionCount = normalizedPrecios.filter(p => p.cantidad < 1).length;
    if (portionCount > 1) {
      return setError("Un producto no puede tener más de un precio de porción");
    }

    setLoading(true);
    try {
      const productData = {
        nombre: nombre.trim(),
        categoria_id: parseInt(categoriaId),
        precios: normalizedPrecios,
        imagen: imagen,
      };

      let savedProducto: Product;

      if (producto.id === 0) {
        savedProducto = await createProducto(productData);
      } else {
        savedProducto = await updateProducto(producto.id, productData);
      }

      if (onSave) {
        onSave(savedProducto);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar el producto");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="product-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="product-modal-content"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="product-modal-close" onClick={onClose} aria-label="Cerrar"><Icons.XIcon size={18} /></button>

            <div className="product-modal-header-edit">
              <h2 className="product-modal-title">{producto.id === 0 ? "Nuevo Producto" : "Editar Producto"}</h2>
            </div>

            <div className="product-modal-image">
              <img src={previewImagen} alt="Vista previa del producto" />
            </div>

            <div className="product-modal-body">
              {error && <div className="form-error" ref={errorRef}>{error}</div>}

              <div className="edit-form">
                {producto.id > 0 && producto.sku && (
                  <div style={{ 
                    fontSize: "10px", 
                    color: "#999", 
                    textAlign: "right",
                    marginBottom: "8px",
                    fontFamily: "monospace"
                  }}>
                    SKU: {producto.sku}
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="edit-nombre">Nombre del Producto:</label>
                  <input
                    id="edit-nombre"
                    type="text"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    className="form-input"
                    disabled={loading}
                    placeholder="Ej. Hamburguesa Doble"
                    maxLength={50}
                  />
                  <div className={`char-counter ${nombre.length > 40 ? "warning" : ""} ${nombre.length === 50 ? "error" : ""}`}>
                    {nombre.length}/50
                  </div>
                </div>

                <div className="form-group">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <label>Precios:</label>
                    <div className="info-tooltip">
                      <Icons.InfoIcon className="info-icon" />
                      <div className="tooltip-content">
                        Debe existir un precio unitario.<br />
                        No se permiten cantidades duplicadas.
                      </div>
                    </div>
                  </div>
                  <div className="prices-editor">
                    {precios.length > 0 ? (
                      precios.map((precio_item, index) => (
                        <div key={precio_item.id ?? index} className="price-edit-row">

                          <div className="price-edit-field">
                            <label className="price-edit-label">
                              Cantidad
                              {isPortionQuantity(precio_item.cantidad) && (
                                <span className="unit-price-badge" title={formatCantidadBadge(precio_item.cantidad)}>
                                  ★ {formatCantidadBadge(precio_item.cantidad)}
                                </span>
                              )}
                              {isSameQuantity(precio_item.cantidad, 1) && (
                                <span className="unit-price-badge" title="Precio unitario obligatorio">
                                  ★ Unitario
                                </span>
                              )}
                              {isSameQuantity(precio_item.cantidad, 6) && (
                                <span className="unit-price-badge" title="Precio por media docena">
                                  ★ 1/2 Docena
                                </span>
                              )}
                              {isSameQuantity(precio_item.cantidad, 12) && (
                                <span className="unit-price-badge" title="Precio por docena">
                                  ★ Docena
                                </span>
                              )}
                              {precio_item.cantidad > 12 && isSameQuantity(precio_item.cantidad % 12, 0) && (
                                <span className="unit-price-badge" title={`Precio por ${precio_item.cantidad / 12} docenas`}>
                                  ★ {precio_item.cantidad / 12} Docenas
                                </span>
                              )}
                            </label>
                            <div className="quantity-control">
                              <button
                                type="button"
                                className="qty-btn qty-btn-minus"
                                aria-label="Disminuir cantidad"
                                onClick={() => {
                                  const newPrecios = [...precios];
                                  const current = newPrecios[index].cantidad;
                                  const next = getPrevCantidad(current);
                                  newPrecios[index].cantidad = next;
                                  setPrecios(newPrecios);
                                  const nextInputs = [...cantidadInputs];
                                  nextInputs[index] = formatCantidadDisplay(next);
                                  setCantidadInputs(nextInputs);
                                }}
                                disabled={loading || !canDecreaseCantidad(precio_item.cantidad, index)}
                              >
                                <Icons.MinusIcon size={14} />
                              </button>
                              <input
                                type="text"
                                inputMode="decimal"
                                className="qty-input"
                                value={cantidadInputs[index] ?? formatCantidadDisplay(precio_item.cantidad)}
                                onFocus={(e) => {
                                  e.target.select();
                                  const nextInputs = [...cantidadInputs];
                                  nextInputs[index] = cantidadInputs[index] ?? formatCantidadDisplay(precio_item.cantidad);
                                  setCantidadInputs(nextInputs);
                                }}
                                onChange={(e) => {
                                  const rawValue = e.target.value;
                                  const nextInputs = [...cantidadInputs];
                                  nextInputs[index] = rawValue;
                                  setCantidadInputs(nextInputs);

                                  const parsed = parseCantidadInput(rawValue);
                                  if (!Number.isNaN(parsed) && parsed > 0) {
                                    const newPrecios = [...precios];
                                    newPrecios[index].cantidad = parsed < 1 ? normalizeCantidad(parsed) : Math.max(1, Math.round(parsed));
                                    setPrecios(newPrecios);
                                  }
                                }}
                                onBlur={() => {
                                  const rawValue = cantidadInputs[index] ?? formatCantidadDisplay(precio_item.cantidad);
                                  const parsed = parseCantidadInput(rawValue);
                                  const normalized = !Number.isNaN(parsed) && parsed > 0 ? normalizeCantidad(parsed) : precio_item.cantidad;
                                  const newPrecios = [...precios];
                                  newPrecios[index].cantidad = normalized;
                                  setPrecios(newPrecios);
                                  const nextInputs = [...cantidadInputs];
                                  nextInputs[index] = formatCantidadDisplay(normalized);
                                  setCantidadInputs(nextInputs);
                                }}
                                disabled={loading}
                              />
                              <button
                                type="button"
                                className="qty-btn qty-btn-plus"
                                aria-label="Aumentar cantidad"
                                onClick={() => {
                                  const newPrecios = [...precios];
                                  const current = newPrecios[index].cantidad;
                                  const next = getNextCantidad(current);
                                  newPrecios[index].cantidad = next;
                                  setPrecios(newPrecios);
                                  const nextInputs = [...cantidadInputs];
                                  nextInputs[index] = formatCantidadDisplay(next);
                                  setCantidadInputs(nextInputs);
                                }}
                                disabled={loading}
                              >
                                <Icons.PlusIcon size={14} />
                              </button>
                            </div>
                          </div>

                          <div className="price-edit-field">
                            <label className="price-edit-label">Precio</label>
                            <input
                              type="text"
                              inputMode="decimal"
                              value={preciosInput[index] || ""}
                              onFocus={(e) => {
                                const newInputs = [...preciosInput];
                                newInputs[index] = precio_item.precio.toString().replace(".", ",");
                                setPreciosInput(newInputs);
                                setTimeout(() => e.target.select(), 0);
                              }}
                              onChange={(e) => {
                                let value = e.target.value.replace(".", ",");
                                if (!/^\d*(,\d{0,2})?$/.test(value)) return;

                                const newInputs = [...preciosInput];
                                newInputs[index] = value;
                                setPreciosInput(newInputs);

                                const numeric = parseCurrencyInput(value);
                                if (!isNaN(numeric)) {
                                  const newPrecios = [...precios];
                                  newPrecios[index].precio = numeric;
                                  setPrecios(newPrecios);
                                }
                              }}
                              onBlur={() => {
                                if (precio_item.precio > 0) {
                                  const newInputs = [...preciosInput];
                                  newInputs[index] = formatCurrency(precio_item.precio);
                                  setPreciosInput(newInputs);
                                } else {
                                  const newInputs = [...preciosInput];
                                  newInputs[index] = "";
                                  setPreciosInput(newInputs);
                                }
                              }}
                              className="form-input"
                              disabled={loading}
                              placeholder="$ 0,00"
                            />
                          </div>

                          <button
                            type="button"
                            className="item-remove-btn"
                            onClick={() => {
                              // Advertir si se intenta eliminar el precio unitario
                              if (precio_item.cantidad === 1 && precios.length > 1) {
                                setPriceIndexToDelete(index);
                                setShowDeleteWarning(true);
                              } else {
                                setPrecios(precios.filter((_, i) => i !== index));
                                setPreciosInput(preciosInput.filter((_, i) => i !== index));
                                setCantidadInputs(cantidadInputs.filter((_, i) => i !== index));
                              }
                            }}
                            disabled={loading || (precio_item.cantidad === 1 && precios.length === 1)}
                            title={precio_item.cantidad === 1 && precios.length === 1 
                              ? "No se puede eliminar el único precio unitario" 
                              : "Eliminar precio"}
                          >
                            <Icons.TrashIcon size={16} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <div className="no-prices-editor">
                        No hay precios configurados
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    className="price-add-btn"
                    onClick={() => {
                      const cantidadesExistentes = precios.map(p => p.cantidad).sort((a, b) => a - b);
                      let nuevaCantidad = 1;
                      if (cantidadesExistentes.includes(1)) {
                        nuevaCantidad = cantidadesExistentes[cantidadesExistentes.length - 1] + 1;
                      }
                      setPrecios([...precios, { cantidad: nuevaCantidad, precio: 0 }]);
                      setPreciosInput([...preciosInput, ""]);
                      setCantidadInputs([...cantidadInputs, formatCantidadDisplay(nuevaCantidad)]);
                    }}
                    disabled={loading}
                  >
                    <Icons.PlusIcon size={16} /> Agregar Precio
                  </button>
                </div>

                <div className="form-group">
                  <label htmlFor="edit-categoria">Categoría:</label>
                  <select
                    id="edit-categoria"
                    value={categoriaId}
                    onChange={(e) => setCategoriaId(e.target.value)}
                    className="form-input"
                    disabled={loading}
                  >
                    <option value="">Seleccionar categoría</option>
                    {categorias.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="file-input">Imagen del Producto:</label>
                  <div className="file-input-wrapper">
                    <input
                    id="file-input"
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                    disabled={loading}
                    />
                    <label htmlFor="file-input" className="file-label">
                        {imagen ? `✓ ${imagen.name}` : "Subir nueva imagen"}
                    </label>
                  </div>
                  {imagen && (
                    <button
                      type="button"
                      className="file-clear-btn"
                      onClick={() => {
                        setImagen(null);
                        const input = document.getElementById("file-input") as HTMLInputElement;
                        if (input) input.value = "";
                        setPreviewImagen(
                          producto.imagen ? `${env.API_BASE_URL}/${producto.imagen}` : "/placeholder.png"
                        );
                      }}
                      disabled={loading}
                    >
                      {producto.id === 0 ? "Quitar imagen" : "Cancelar cambio de imagen"}
                    </button>
                  )}
                </div>

                <div className="form-actions">
                  <button 
                    className="form-save-btn" 
                    onClick={handleSave} 
                    disabled={loading}
                  >
                    {loading ? "Guardando..." : producto.id === 0 ? "Crear Producto" : "Actualizar Producto"}
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

          {/* Diálogo de confirmación para eliminar precio unitario */}
          <ConfirmDialog
            isOpen={showDeleteWarning}
            title={<><Icons.WarningIcon size={18} /> Eliminar Precio unitario</>}
            message={
              <>
                Estás eliminando el precio <strong>Unitario</strong>.
              </>
            }
            warning={
              <>
                El producto debe tener un precio unitario obligatoriamente.
                Asegúrate de agregar otro precio unitario.
              </>
            }
            confirmText="Eliminar"
            cancelText="Cancelar"
            onCancel={() => {
              setShowDeleteWarning(false);
              setPriceIndexToDelete(null);
            }}
            onConfirm={() => {
              if (priceIndexToDelete !== null) {
                setPrecios(precios.filter((_, i) => i !== priceIndexToDelete));
                setPreciosInput(preciosInput.filter((_, i) => i !== priceIndexToDelete));
                setCantidadInputs(cantidadInputs.filter((_, i) => i !== priceIndexToDelete));
              }
              setShowDeleteWarning(false);
              setPriceIndexToDelete(null);
            }}
            confirmDanger
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProductModal;
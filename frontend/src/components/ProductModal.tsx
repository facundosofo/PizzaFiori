import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import { updateProducto } from "../services/productsService";
import "../styles/product-modal.css";
import env from "../config/env";

interface ProductModalProps {
  producto: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (producto: Product) => void;
  categorias?: Category[];
}

const ProductModal = ({
  producto,
  isOpen,
  onClose,
  onSave,
  categorias = [],
}: ProductModalProps) => {

  const [nombre, setNombre] = useState("");
  const [precio, setPrecio] = useState(0);
  const [precioInput, setPrecioInput] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [imagen, setImagen] = useState<File | null>(null);
  const [previewImagen, setPreviewImagen] = useState("/placeholder.png");
  

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const formatPrecio = (value: number) =>
  value.toLocaleString("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 2,
  });

  const normalizePrecio = (value: string) => {
    return Number(
      value
        .replace(/\$/g, "")
        .replace(/\./g, "")
        .replace(",", ".")
    );
  };

  useEffect(() => {
    if (producto && isOpen) {
      setNombre(producto.nombre);
      const firstPrice = producto.precios && producto.precios.length > 0 
        ? producto.precios[0].precio 
        : 0;
      setPrecio(Number(firstPrice));
      setPrecioInput(formatPrecio(Number(firstPrice)));
      setCategoriaId(producto.categoria_id?.toString() || "");
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
    if (nombre.trim().length > 100) return setError("El nombre no puede superar los 100 caracteres");
    if (!categoriaId) return setError("Selecciona una categoría");
    if (precio <= 0) return setError("El precio debe ser mayor a 0");

    setLoading(true);
    try {
      const updatedData = {
        nombre: nombre.trim(),
        precio_venta: precio,
        categoria_id: parseInt(categoriaId),
        imagen: imagen,
      };

      const updatedProducto = await updateProducto(producto.id, updatedData);
      
      if (onSave) {
        onSave(updatedProducto);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar los cambios");
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
              <h2 className="modal-title">Editar Producto</h2>
            </div>

            <div className="modal-image">
              <img src={previewImagen} alt="Vista previa del producto" />
            </div>

            <div className="modal-body">
              {error && <div className="form-error">{error}</div>}

              <div className="edit-form">
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
                    maxLength={100}
                  />
                  <div className={`char-counter ${ nombre.length > 80 ? "warning" : ""} ${ nombre.length === 100 ? "error" : "" }`}>
                    {nombre.length}/100
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="edit-precio">Precio de Venta:</label>
                  <input
                    id="edit-precio"
                    type="text"
                    inputMode="decimal"
                    value={precioInput}
                    onFocus={() => {
                      setPrecioInput(precio.toString().replace(".", ","));
                    }}
                    onChange={(e) => {
                      let value = e.target.value.replace(".", ",");
                      if (!/^\d*(,\d{0,2})?$/.test(value)) return;
                      setPrecioInput(value);
                      const numeric = normalizePrecio(value);
                      if (!isNaN(numeric)) {
                        setPrecio(numeric);
                      }
                    }}
                    onBlur={() => {
                      if (precio > 0) {
                        setPrecioInput(formatPrecio(precio));
                      } else {
                        setPrecioInput("");
                      }
                    }}
                    className="form-input"
                    disabled={loading}
                    placeholder="$ 0,00"
                  />
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
                      Cancelar cambio de imagen
                    </button>
                  )}
                </div>

                <div className="form-actions">
                  <button 
                    className="form-save-btn" 
                    onClick={handleSave} 
                    disabled={loading}
                  >
                    {loading ? "Guardando..." : "Actualizar Producto"}
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

export default ProductModal;
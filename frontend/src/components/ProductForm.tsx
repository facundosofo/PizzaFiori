import React, { useState, useEffect } from "react";
import type { Product } from "../types/product";
import "../styles/shared.css";
import "../styles/product-form.css";
import env from "../config/env";

interface ProductFormProps {
  producto?: Product | null;
  categorias: { id: number; nombre: string }[];
  onSave: (producto: Product) => Promise<void>;
  onCancel: () => void;
}

const ProductForm: React.FC<ProductFormProps> = ({
  producto,
  categorias,
  onSave,
  onCancel,
}) => {
  const [nombre, setNombre] = useState(producto?.nombre || "");
  const [categoria, setCategoria] = useState(producto?.categoria_id?.toString() || "");
  const [precioVenta, setPrecioVenta] = useState(() => {
    if (producto?.precios && producto.precios.length > 0) {
      return producto.precios[0].precio.toString();
    }
    return "";
  });
  const [preview, setPreview] = useState<string>(
    producto?.imagen ? `${env.API_BASE_URL}/${producto.imagen}` : ""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (producto) {
      setNombre(producto.nombre);
      setCategoria(producto.categoria_id?.toString() || "");
      if (producto.precios && producto.precios.length > 0) {
        setPrecioVenta(producto.precios[0].precio.toString());
      }
      if (producto.imagen) {
        setPreview(`${env.API_BASE_URL}/${producto.imagen}`);
      }
    }
  }, [producto]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(selected);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (!nombre.trim()) {
        setError("El nombre del producto es requerido");
        return;
      }
      if (!categoria) {
        setError("Selecciona una categoría");
        return;
      }
      if (!precioVenta || parseFloat(precioVenta) <= 0) {
        setError("El precio debe ser mayor a 0");
        return;
      }

      const nuevoProducto: Product = {
        id: producto?.id || 0,
        nombre: nombre.trim(),
        categoria_id: parseInt(categoria),
        imagen: producto?.imagen,
        activo: producto?.activo ?? true,
        fecha_creacion: producto?.fecha_creacion || new Date().toISOString(),
        fecha_actualizacion: new Date().toISOString(),
      };

      await onSave(nuevoProducto);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar el producto");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="product-form">
      <h2>{producto ? "Editar Producto" : "Nuevo Producto"}</h2>

      {error && <div className="form-error">{error}</div>}

      <div className="form-group">
        <label htmlFor="nombre">Nombre del Producto *</label>
        <input
          id="nombre"
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Ej: Pizza Hawaiana"
          className="form-input"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="categoria">Categoría *</label>
        <select
          id="categoria"
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
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
        <label htmlFor="precio">Precio de Venta *</label>
        <input
          id="precio"
          type="number"
          step="0.01"
          min="0"
          value={precioVenta}
          onChange={(e) => setPrecioVenta(e.target.value)}
          placeholder="Ej: 25.50"
          className="form-input"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="imagen">Imagen del Producto</label>
        <div className="file-input-wrapper">
          <input
            id="imagen"
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="file-input"
            disabled={loading}
          />
          <span className="file-label">Seleccionar archivo</span>
        </div>
      </div>

      {preview && (
        <div className="image-preview">
          <img src={preview} alt="Vista previa" />
        </div>
      )}

      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="form-cancel-btn"
          disabled={loading}
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="form-save-btn"
          disabled={loading}
        >
          {loading ? "Guardando..." : producto ? "Actualizar" : "Crear"}
        </button>
      </div>
    </form>
  );
};

export default ProductForm;

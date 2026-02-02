import { useState, useEffect } from "react";
import RadioGroup, { type RadioOption } from "./shared/RadioGroup";
import MultiSelect, { type MultiSelectItem } from "./shared/MultiSelect";
import { InfoIcon, XIcon, PlusIcon, MinusIcon } from "./shared/Icons";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import type { OfferItemRequest } from "../types/offer_item";
import "../styles/offer-item-form.css";
import "../styles/shared/quantity-controls.css";
import "../styles/shared/add-button.css";

type TipoOfferItem = "producto" | "categoria" | "opciones";

interface OfferItemFormProps {
  productos: Product[];
  categorias: Category[];
  onAdd: (item: OfferItemRequest) => void;
  onCancel: () => void;
}

const OfferItemForm = ({
  productos,
  categorias,
  onAdd,
  onCancel,
}: OfferItemFormProps) => {
  const [tipo, setTipo] = useState<TipoOfferItem>("producto");
  const [productoId, setProductoId] = useState<number>(0);
  const [categoriaId, setCategoriaId] = useState<number>(0);
  const [productosSeleccionados, setProductosSeleccionados] = useState<number[]>([]);
  const [cantidad, setCantidad] = useState<number>(1);
  const [error, setError] = useState<string>("");

  const tipoOptions: RadioOption[] = [
    { value: "producto", label: "Producto" },
    { value: "categoria", label: "Categoría" },
    { value: "opciones", label: "Opciones múltiples" },
  ];

  const productosActivos = productos.filter((p) => p.activo);
  const categoriasDisponibles = categorias; // Todas las categorías

  const productosMultiSelect: MultiSelectItem[] = productosActivos.map((p) => ({
    id: p.id,
    label: p.nombre,
    disabled: false,
  }));

  // Reset fields cuando cambia el tipo
  useEffect(() => {
    setProductoId(0);
    setCategoriaId(0);
    setProductosSeleccionados([]);
    setError("");
  }, [tipo]);

  const handleAdd = () => {
    setError("");

    // Validaciones según tipo
    if (tipo === "producto") {
      if (productoId === 0) {
        return setError("Debes seleccionar un producto");
      }
    } else if (tipo === "categoria") {
      if (categoriaId === 0) {
        return setError("Debes seleccionar una categoría");
      }
    } else if (tipo === "opciones") {
      if (productosSeleccionados.length < 2) {
        return setError("Debes seleccionar al menos 2 productos para las opciones");
      }
    }

    if (cantidad <= 0) {
      return setError("La cantidad debe ser mayor a 0");
    }

    // Construir el item según el tipo
    const item: OfferItemRequest = {
      cantidad,
    };

    if (tipo === "producto") {
      item.producto_id = productoId;
    } else if (tipo === "categoria") {
      item.categoria_id = categoriaId;
    } else if (tipo === "opciones") {
      item.producto_opciones = productosSeleccionados;
    }

    onAdd(item);
  };

  return (
    <div className="offer-item-form">
      {error && <div className="form-error">{error}</div>}

      <div className="offer-item-form-body">
        {/* Tipo de item */}
        <RadioGroup
          name="tipo-item"
          options={tipoOptions}
          value={tipo}
          onChange={(value) => setTipo(value as TipoOfferItem)}
        />

        {/* Producto específico */}
        {tipo === "producto" && (
          <div className="form-group">
            <label htmlFor="producto-select">Producto</label>
            <select
              id="producto-select"
              value={productoId}
              onChange={(e) => setProductoId(parseInt(e.target.value))}
              className="form-input"
            >
              <option value={0}>Seleccionar producto...</option>
              {productosActivos.map((producto) => (
                <option key={producto.id} value={producto.id}>
                  {producto.nombre}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Categoría */}
        {tipo === "categoria" && (
          <div className="form-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label htmlFor="categoria-select">Categoría</label>
              <div className="info-tooltip">
                <InfoIcon className="info-icon" />
                <div className="tooltip-content">
                  Se podrá elegir cualquier producto activo de esta categoría
                </div>
              </div>
            </div>
            <select
              id="categoria-select"
              value={categoriaId}
              onChange={(e) => setCategoriaId(parseInt(e.target.value))}
              className="form-input"
            >
              <option value={0}>Seleccionar categoría...</option>
              {categoriasDisponibles.map((categoria) => (
                <option key={categoria.id} value={categoria.id}>
                  {categoria.nombre}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Opciones múltiples */}
        {tipo === "opciones" && (
          <div className="form-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label>Productos</label>
              <div className="info-tooltip">
                <InfoIcon className="info-icon" />
                <div className="tooltip-content">
                  Se podrá elegir un producto de entre todas las opciones seleccionadas
                </div>
              </div>
            </div>
            <MultiSelect
              items={productosMultiSelect}
              selectedIds={productosSeleccionados}
              onChange={setProductosSeleccionados}
              label=""
              searchable={productosActivos.length > 10}
              placeholder="Buscar productos..."
              minSelection={2}
            />
          </div>
        )}

        {/* Cantidad */}
        <div className="form-group">
          <label>Cantidad</label>
          <div className="quantity-control">
            <button
              type="button"
              className="qty-btn qty-btn-minus"
              onClick={() => setCantidad(Math.max(1, cantidad - 1))}
              disabled={cantidad <= 1}
              aria-label="Disminuir cantidad"
            >
              <MinusIcon size={14} />
            </button>
            <input
              type="number"
              min="1"
              max="1000"
              className="qty-input"
              value={cantidad}
              onFocus={(e) => e.target.select()}
              onChange={(e) => setCantidad(Math.max(1, parseInt(e.target.value) || 1))}
            />
            <button
              type="button"
              className="qty-btn qty-btn-plus"
              onClick={() => setCantidad(cantidad + 1)}
              aria-label="Aumentar cantidad"
            >
              <PlusIcon size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Acciones */}
      <div className="offer-item-form-actions">
        <button
          type="button"
          className="btn-add"
          onClick={handleAdd}
        >
          <PlusIcon size={16} /> Agregar Item
        </button>
        <button
          type="button"
          className="btn-cancel"
          onClick={onCancel}
        >
          <XIcon size={16} /> Cancelar
        </button>
      </div>
    </div>
  );
};

export default OfferItemForm;

import { useState, useEffect } from "react";
import RadioGroup, { type RadioOption } from "./shared/RadioGroup";
import MultiSelect, { type MultiSelectItem } from "./shared/MultiSelect";
import SearchableSelect from "./shared/SearchableSelect";
import * as Icons from './shared/Icons';
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import type { OfferItemRequest } from "../types/offer_item";
import "../styles/offer-item-form.css";
import "../styles/shared/add-button.css";

type TipoOfferItem = "producto" | "categoria" | "opciones";

interface OfferItemFormProps {
  productos: Product[];
  categorias: ProductoCategoria[];
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
  const [usarPorcionProducto, setUsarPorcionProducto] = useState<boolean>(false);
  const [usarPorcionOpciones, setUsarPorcionOpciones] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const tipoOptions: RadioOption[] = [
    { value: "producto", label: "Producto" },
    { value: "categoria", label: "Categoría" },
    { value: "opciones", label: "Opciones múltiples" },
  ];

  const productosActivos = productos.filter((p) => p.activo);
  const categoriasDisponibles = categorias; // Todas las categorías

  // Reset fields cuando cambia el tipo
  useEffect(() => {
    setProductoId(0);
    setCategoriaId(0);
    setProductosSeleccionados([]);
    setCantidad(1);
    setUsarPorcionProducto(false);
    setUsarPorcionOpciones(false);
    setError("");
  }, [tipo]);

  const getProductPortionQuantity = (product: Product | undefined): number | null => {
    if (!product?.precios || product.precios.length === 0) return null;
    const portionPrice = product.precios
      .map((price) => Number(price.cantidad))
      .find((cantidadPrecio) => cantidadPrecio < 1);
    return portionPrice ?? null;
  };

  const getPortionLabel = (portionQuantity: number | null): string => {
    if (!portionQuantity) return "";
    if (Math.abs(portionQuantity - 0.5) < 1e-9) return "1/2";
    if (Math.abs(portionQuantity - 0.25) < 1e-9) return "1/4";
    if (Math.abs(portionQuantity - 0.125) < 1e-9) return "1/8";
    return String(portionQuantity);
  };

  const selectedProduct = productosActivos.find((p) => p.id === productoId);
  const productPortionQuantity = getProductPortionQuantity(selectedProduct);
  const productHasPortionPrice = Boolean(productPortionQuantity);
  const productPortionLabel = getPortionLabel(productPortionQuantity);

  const selectedOptionProducts = productosActivos.filter((p) => productosSeleccionados.includes(p.id));
  const selectedOptionProductsHaveNonPortion = selectedOptionProducts.some((p) => !getProductPortionQuantity(p));
  const optionProductsWithPortion = productosActivos.filter((p) => Boolean(getProductPortionQuantity(p)));
  const optionPortionQuantity =
    (selectedOptionProducts.length > 0
      ? getProductPortionQuantity(selectedOptionProducts[0])
      : getProductPortionQuantity(optionProductsWithPortion[0])) ?? null;

  const productsForOptionSelect = usarPorcionOpciones ? optionProductsWithPortion : productosActivos;

  useEffect(() => {
    if (tipo === "producto" && productoId > 0) {
      if (productHasPortionPrice && usarPorcionProducto) {
        setCantidad(productPortionQuantity ?? 1);
      } else {
        setCantidad(1);
      }
    }
  }, [tipo, productoId, productPortionQuantity, productHasPortionPrice, usarPorcionProducto]);

  useEffect(() => {
    if (tipo === "producto" && !productHasPortionPrice && usarPorcionProducto) {
      setUsarPorcionProducto(false);
    }
  }, [tipo, productHasPortionPrice, usarPorcionProducto]);

  useEffect(() => {
    if (tipo !== "opciones") return;
    if (usarPorcionOpciones) {
      setCantidad(optionPortionQuantity ?? 1);
    } else {
      setCantidad(1);
    }
  }, [tipo, usarPorcionOpciones, optionPortionQuantity]);

  useEffect(() => {
    if (tipo === "opciones" && usarPorcionOpciones) {
      setProductosSeleccionados((prev) =>
        prev.filter((id) => {
          const product = productosActivos.find((p) => p.id === id);
          return Boolean(getProductPortionQuantity(product));
        })
      );
    }
  }, [tipo, usarPorcionOpciones, productosActivos]);

  const handleTogglePorcionOpciones = (checked: boolean) => {
    setError("");
    if (checked && selectedOptionProductsHaveNonPortion) {
      setError("No puedes activar porción si seleccionaste productos sin porciones");
      return;
    }
    setUsarPorcionOpciones(checked);
  };

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

  const productosMultiSelect: MultiSelectItem[] = productsForOptionSelect.map((p) => ({
    id: p.id,
    label: p.nombre,
    disabled: false,
  }));

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
            <SearchableSelect
              id="producto-select"
              value={productoId}
              onChange={setProductoId}
              options={[
                { value: 0, label: "Seleccionar producto..." },
                ...productosActivos.map((p) => ({ value: p.id, label: p.nombre }))
              ]}
              placeholder="Seleccionar producto..."
              searchPlaceholder="Buscar producto..."
            />
          </div>
        )}

        {tipo === "producto" && productHasPortionPrice && (
          <div className="form-group">
            <label htmlFor="usar-porcion-producto" className="portion-toggle-label">
              <input
                id="usar-porcion-producto"
                type="checkbox"
                className="portion-toggle-checkbox"
                checked={usarPorcionProducto}
                onChange={(e) => setUsarPorcionProducto(e.target.checked)}
              />
              <span className="portion-toggle-chip">{`PORCION ${productPortionLabel}`}</span>
            </label>
          </div>
        )}

        {tipo === "opciones" && (
          <div className="form-group">
            <label htmlFor="usar-porcion-opciones" className="portion-toggle-label">
              <input
                id="usar-porcion-opciones"
                type="checkbox"
                className="portion-toggle-checkbox"
                checked={usarPorcionOpciones}
                onChange={(e) => handleTogglePorcionOpciones(e.target.checked)}
              />
              <span className="portion-toggle-chip">PORCION</span>
            </label>
            {usarPorcionOpciones && (
              <span className="portion-toggle-hint">Solo se muestran productos con porción configurada</span>
            )}
          </div>
        )}

        {/* Categoría */}
        {tipo === "categoria" && (
          <div className="form-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label htmlFor="categoria-select">Categoría</label>
              <div className="info-tooltip">
                <Icons.InfoIcon className="info-icon" />
                <div className="tooltip-content">
                  Se podrá elegir cualquier producto activo de esta categoría
                </div>
              </div>
            </div>
            <SearchableSelect
              id="categoria-select"
              value={categoriaId}
              onChange={setCategoriaId}
              options={[
                { value: 0, label: "Seleccionar categoría..." },
                ...categoriasDisponibles.map((c) => ({ value: c.id, label: c.nombre }))
              ]}
              placeholder="Seleccionar categoría..."
              searchPlaceholder="Buscar categoría..."
            />
          </div>
        )}

        {/* Opciones múltiples */}
        {tipo === "opciones" && (
          <div className="form-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label>Productos</label>
              <div className="info-tooltip">
                <Icons.InfoIcon className="info-icon" />
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
      </div>

      {/* Acciones */}
      <div className="offer-item-form-actions">
        <button
          type="button"
          className="btn-add"
          onClick={handleAdd}
        >
          <Icons.PlusIcon size={16} /> Agregar Item
        </button>
        <button
          type="button"
          className="btn-cancel"
          onClick={onCancel}
        >
          <Icons.XIcon size={16} /> Cancelar
        </button>
      </div>
    </div>
  );
};

export default OfferItemForm;

import { useEffect, useState } from "react";
import type { DragEvent as ReactDragEvent } from "react";
import { ArrowDownWideNarrow } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { formatLocalISO } from "../utils/formatters";
import { getProductos, reorderProductos } from "../services/productsService";
import { getProductosCategorias } from "../services/productosCategoriasService";
import ProductCard from "../components/ProductCard";
import ProductModal from "../components/ProductModal";
import ProductosCategoryConfigModal from "../components/ProductosCategoryConfigModal";
import BulkPriceUpdateModal from "../components/BulkPriceUpdateModal";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import "../styles/product-card.css";

const ProductosPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [productos, setProductos] = useState<Product[]>([]);
  const [categorias, setCategorias] = useState<ProductoCategoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [newProduct, setNewProduct] = useState<Product | null>(null);
  const [showCategoryConfig, setShowCategoryConfig] = useState(false);
  const [showBulkPriceModal, setShowBulkPriceModal] = useState(false);
  const [orderingCategoryId, setOrderingCategoryId] = useState<number | null>(null);
  const [draggedProductId, setDraggedProductId] = useState<number | null>(null);
  const [isSavingOrder, setIsSavingOrder] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [prods, cats] = await Promise.all([
          getProductos(),
          getProductosCategorias(true),
        ]);

        if (!prods || prods.length === 0) {
          setError("No se pudieron cargar los productos. Intenta recargar la página.");
        }
        if (!cats || cats.length === 0) {
          setError("No se pudieron cargar las categorías. Intenta recargar la página.");
        }

        setProductos(prods || []);
        setCategorias(cats || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido al cargar los datos";
        setError(`Error al cargar: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleProductUpdate = (updatedProducto: Product) => {
    setProductos((prevProductos) => {
      const updated = prevProductos.map((p) => (p.id === updatedProducto.id ? updatedProducto : p));
      return updated;
    });
  };

  const handleBulkPriceSuccess = (updatedProducts: Product[]) => {
    setProductos((prevProductos) => {
      let updated = [...prevProductos];
      for (const prod of updatedProducts) {
        updated = updated.map((p) => (p.id === prod.id ? prod : p));
      }
      return updated;
    });
  };

  const handleProductDelete = (productoId: number) => {
    setProductos((prevProductos) => {
      const filtered = prevProductos.filter((p) => p.id !== productoId);
      return filtered;
    });
  };

  const handleCreateClick = () => {
    setNewProduct({
      id: 0,
      sku: "",
      nombre: "",
      categoria_id: 0,
      orden: 0,
      imagen: undefined,
      activo: true,
      fecha_creacion: formatLocalISO(new Date()),
      fecha_actualizacion: formatLocalISO(new Date()),
      precios: [],
    });
    setIsCreating(true);
  };

  const handleCreateProduct = async (producto: Product) => {
    setProductos((prev) => {
      const updated = [...prev, producto];
      return updated;
    });
    
    setCollapsedCategories((prev) => {
      const newSet = new Set(prev);
      if (producto.categoria_id) {
        newSet.delete(producto.categoria_id);
      }
      return newSet;
    });
    
    setIsCreating(false);
    setNewProduct(null);
  };

  const toggleCategoryCollapse = (categoryId: number) => {
    setCollapsedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const handleProductDragStart = (
    event: ReactDragEvent<HTMLDivElement>,
    productoId: number,
  ) => {
    if (orderingCategoryId === null || isSavingOrder) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(productoId));
    setDraggedProductId(productoId);
  };

  const handleProductDragOver = (event: ReactDragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const handleProductDrop = async (
    event: ReactDragEvent<HTMLDivElement>,
    targetProductId: number,
  ) => {
    event.preventDefault();
    if (orderingCategoryId === null || draggedProductId === null || isSavingOrder) return;

    const categoryId = orderingCategoryId;
    const previousProducts = productos;
    const categoryProducts = productos
      .filter((producto) => producto.categoria_id === categoryId)
      .sort((a, b) => a.orden - b.orden || a.id - b.id);
    const sourceIndex = categoryProducts.findIndex(
      (producto) => producto.id === draggedProductId,
    );
    const targetIndex = categoryProducts.findIndex(
      (producto) => producto.id === targetProductId,
    );
    if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) {
      setDraggedProductId(null);
      return;
    }

    const [movedProduct] = categoryProducts.splice(sourceIndex, 1);
    categoryProducts.splice(targetIndex, 0, movedProduct);
    const orderById = new Map(
      categoryProducts.map((producto, orden) => [producto.id, orden]),
    );
    const reorderedProducts = previousProducts.map((producto) => {
      const orden = orderById.get(producto.id);
      return orden === undefined ? producto : { ...producto, orden };
    });

    setProductos(reorderedProducts);
    setDraggedProductId(null);
    setOrderError(null);
    setIsSavingOrder(true);
    try {
      await reorderProductos(
        categoryId,
        categoryProducts.map((producto) => producto.id),
      );
    } catch (err) {
      setProductos(previousProducts);
      setOrderError(
        err instanceof Error ? err.message : "No se pudo guardar el orden de productos.",
      );
    } finally {
      setIsSavingOrder(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="productos-container">
      <div className="page-header">
        <h1 className="page-title">Productos</h1>
        <div className="page-header-actions">
          <button
            className="btn-create-product"
            onClick={handleCreateClick}
          >
            <Icons.PlusIcon size={16} /> Nuevo Producto
          </button>
          <button
            className="btn-config"
            onClick={() => setShowBulkPriceModal(true)}
          >
            <Icons.PesoIcon size={16} />
            Actualizar Precios
          </button>
          <button
            className="btn-config"
            onClick={() => setShowCategoryConfig(true)}
          >
            <Icons.FolderTreeIcon size={16} />
            Categorías
          </button>
        </div>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />
      <ErrorAlert message={orderError} onClose={() => setOrderError(null)} />

      <ProductosCategoryConfigModal
        isOpen={showCategoryConfig}
        onClose={() => setShowCategoryConfig(false)}
        categorias={categorias}
        onRefresh={async () => {
          const cats = await getProductosCategorias(true);
          setCategorias(cats || []);
        }}
      />

      <BulkPriceUpdateModal
        isOpen={showBulkPriceModal}
        onClose={() => setShowBulkPriceModal(false)}
        onSuccess={handleBulkPriceSuccess}
        categorias={categorias}
      />

      {newProduct && (
        <ProductModal
          producto={newProduct}
          isOpen={isCreating}
          onClose={() => {
            setIsCreating(false);
            setNewProduct(null);
          }}
          onSave={handleCreateProduct}
          categorias={categorias}
        />
      )}

      {loading ? (
        <div className="skeleton-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : productos.length === 0 ? (
        <div className="product-selector-empty product-selector-empty-box">
          <div className="product-selector-empty-icon"><Icons.PizzaIcon size={36} /></div>
          <p>No hay productos disponibles</p>
        </div>
      ) : categorias.length === 0 ? (
        <p className="product-empty-state">No hay categorías disponibles</p>
      ) : (
        categorias.map((cat) => {
          const productosDeCategoria = productos
            .filter((p) => p.categoria_id === cat.id)
            .sort((a, b) => a.orden - b.orden || a.id - b.id);

          if (productosDeCategoria.length === 0) return null;

          const isCollapsed = collapsedCategories.has(cat.id);
          const isOrdering = orderingCategoryId === cat.id;

          return (
            <section key={cat.id} className="categoria-section">
              <div className="categoria-header">
                <h2 className="categoria-title">{cat.nombre}</h2>
                <div className="categoria-actions">
                  <button
                    className={`categoria-order ${isOrdering ? "is-active" : ""}`}
                    onClick={() => {
                      if (isOrdering) {
                        setOrderingCategoryId(null);
                      } else {
                        setOrderingCategoryId(cat.id);
                        setCollapsedCategories((previous) => {
                          const expanded = new Set(previous);
                          expanded.delete(cat.id);
                          return expanded;
                        });
                      }
                      setDraggedProductId(null);
                      setOrderError(null);
                    }}
                    disabled={isSavingOrder || productosDeCategoria.length < 2}
                    title={
                      productosDeCategoria.length < 2
                        ? "Se necesitan al menos dos productos para ordenar"
                        : isOrdering
                          ? "Finalizar ordenamiento"
                          : "Ordenar productos de esta categoría"
                    }
                    aria-label={
                      isOrdering
                        ? `Finalizar ordenamiento de ${cat.nombre}`
                        : `Ordenar productos de ${cat.nombre}`
                    }
                    aria-pressed={isOrdering}
                  >
                    <ArrowDownWideNarrow size={18} />
                  </button>
                  <button
                    className={`categoria-toggle ${isCollapsed ? "collapsed" : ""}`}
                    onClick={() => toggleCategoryCollapse(cat.id)}
                    aria-label={isCollapsed ? "Expandir" : "Colapsar"}
                    disabled={isSavingOrder || isOrdering}
                  >
                    <Icons.ChevronDownIcon size={16} />
                  </button>
                </div>
              </div>

              {!isCollapsed && (
                <div className="product-scroll-horizontal">
                  {isOrdering && isSavingOrder && (
                    <p className="product-order-hint">
                      Guardando orden...
                    </p>
                  )}
                  {productosDeCategoria.map((p) => (
                    <ProductCard
                      key={p.id}
                      producto={p}
                      onProductUpdate={handleProductUpdate}
                      onProductDelete={handleProductDelete}
                      categorias={categorias}
                      isReordering={isOrdering && !isSavingOrder}
                      isDragging={draggedProductId === p.id}
                      onProductDragStart={handleProductDragStart}
                      onProductDragOver={handleProductDragOver}
                      onProductDrop={handleProductDrop}
                      onProductDragEnd={() => setDraggedProductId(null)}
                    />
                  ))}
                </div>
              )}
            </section>
          );
        })
      )}
    </div>
  );
};

export default ProductosPage;

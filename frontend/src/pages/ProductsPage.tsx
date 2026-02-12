import { useEffect, useState } from "react";
import { getProductos } from "../services/productsService";
import { getCategorias } from "../services/categoriasService";
import ProductCard from "../components/ProductCard";
import ProductModal from "../components/ProductModal";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import type { Product } from "../types/product";
import type { Category } from "../types/category";
import "../styles/product-card.css";

const ProductosPage = () => {
  const [productos, setProductos] = useState<Product[]>([]);
  const [categorias, setCategorias] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [newProduct, setNewProduct] = useState<Product | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [prods, cats] = await Promise.all([
          getProductos(),
          getCategorias(),
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
      imagen: undefined,
      activo: true,
      fecha_creacion: new Date().toISOString(),
      fecha_actualizacion: new Date().toISOString(),
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

  return (
    <div className="productos-container">
      <div className="page-header">
        <h1 className="page-title">Productos</h1>
        <button
          className="btn-create-product"
          onClick={handleCreateClick}
        >
          <Icons.PlusIcon size={16} /> Nuevo Producto
        </button>
      </div>

      <ErrorAlert message={error} onClose={() => setError(null)} />

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
          const productosDeCategoria = productos.filter(
            (p) => p.categoria_id === cat.id
          );

          if (productosDeCategoria.length === 0) return null;

          const isCollapsed = collapsedCategories.has(cat.id);

          return (
            <section key={cat.id} className="categoria-section">
              <div className="categoria-header">
                <h2 className="categoria-title">{cat.nombre}</h2>
                <button
                  className={`categoria-toggle ${isCollapsed ? "collapsed" : ""}`}
                  onClick={() => toggleCategoryCollapse(cat.id)}
                  aria-label={isCollapsed ? "Expandir" : "Colapsar"}
                >
                  <Icons.ChevronDownIcon size={16} />
                </button>
              </div>

              {!isCollapsed && (
                <div className="product-scroll-horizontal">
                  {productosDeCategoria.map((p) => (
                    <ProductCard
                      key={p.id}
                      producto={p}
                      onProductUpdate={handleProductUpdate}
                      onProductDelete={handleProductDelete}
                      categorias={categorias}
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

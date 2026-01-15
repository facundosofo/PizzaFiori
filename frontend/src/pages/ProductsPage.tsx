import { useEffect, useState } from "react";
import { getProductos } from "../services/productsService";
import { getCategorias } from "../services/categoriasService";
import ProductCard from "../components/ProductCard";
import SkeletonLoader from "../components/SkeletonLoader";
import ErrorAlert from "../components/ErrorAlert";
import type { Producto } from "../types/producto";
import type { Categoria } from "../types/categoria";
import "../styles/product-card.css";

const ProductosPage = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());

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
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleProductUpdate = (updatedProducto: Producto) => {
    setProductos((prevProductos) =>
      prevProductos.map((p) => (p.id === updatedProducto.id ? updatedProducto : p))
    );
  };

  const handleProductDelete = (productoId: number) => {
    setProductos((prevProductos) =>
      prevProductos.filter((p) => p.id !== productoId)
    );
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
      <h1 className="productos-title">Productos</h1>

      <ErrorAlert message={error} onClose={() => setError(null)} />

      {loading ? (
        <div className="skeleton-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : categorias.length === 0 ? (
        <p className="empty-state">No hay categorías disponibles</p>
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
                  ▼
                </button>
              </div>

              {!isCollapsed && (
                <div className="scroll-horizontal">
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

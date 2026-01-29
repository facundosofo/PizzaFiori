import { useEffect, useState } from "react";
import { getSales, deleteSale } from "../services/salesService";
import { getProductos } from "../services/productsService";
import { getOfertas } from "../services/ofertasService";
import SkeletonLoader from "../components/SkeletonLoader";
import ErrorAlert from "../components/ErrorAlert";
import SaleDetailModal from "../components/SaleDetailModal";
import SaleEditModal from "../components/SaleEditModal";
import ConfirmDialog from "../components/ConfirmDialog";
import SalesFilters from "../components/SalesFilters";
import { EyeIcon, EditIcon, TrashIcon } from "../components/Icons";
import type { Sale } from "../types/sale";
import type { Product } from "../types/product";
import type { Offer } from "../types/offer";
import { formatCurrency, formatDateDisplay } from "../utils/formatters";
import "../styles/sales.css";

const SalesPage = () => {
  const [sales, setSales] = useState<Sale[]>([]);
  const [allSales, setAllSales] = useState<Sale[]>([]); // All sales for filtering
  // Cache products and offers for use in detail/edit modals (Phase 2+)
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [allOffers, setAllOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [limit] = useState(10);
  const [hasMore, setHasMore] = useState(true);

  // Modal state
  const [selectedSaleId, setSelectedSaleId] = useState<number | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [saleToDelete, setSaleToDelete] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filter state
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);

  // Fetch products and offers once on mount (cache for reuse in modals)
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const [products, offers] = await Promise.all([
          getProductos(),
          getOfertas(),
        ]);
        setAllProducts(products || []);
        setAllOffers(offers || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        console.error("Error fetching catalog:", err);
        setError(`Error al cargar catálogo: ${errorMessage}`);
      }
    };

    fetchCatalog();
  }, []);

  // Fetch sales when page changes
  useEffect(() => {
    const fetchSales = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch all sales (max 1000) for client-side filtering
        const data = await getSales(0, 1000);
        
        setAllSales(data || []);
        
        // Apply filters and pagination
        applyFiltersAndPagination(data || [], dateFrom, dateTo, currentPage);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        setError(`Error al cargar ventas: ${errorMessage}`);
        console.error("Error fetching sales:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSales();
  }, []); // Only fetch once on mount

  // Apply filters and pagination when filters or page changes
  useEffect(() => {
    applyFiltersAndPagination(allSales, dateFrom, dateTo, currentPage);
  }, [currentPage, dateFrom, dateTo, allSales]);

  const applyFiltersAndPagination = (
    salesData: Sale[],
    from: Date | null,
    to: Date | null,
    page: number
  ) => {
    let filtered = [...salesData];

    // Apply date filters
    if (from || to) {
      filtered = filtered.filter((sale) => {
        const saleDate = new Date(sale.fecha_creacion);
        
        if (from && to) {
          // Set time to start/end of day for proper comparison
          const fromStart = new Date(from);
          fromStart.setHours(0, 0, 0, 0);
          const toEnd = new Date(to);
          toEnd.setHours(23, 59, 59, 999);
          
          return saleDate >= fromStart && saleDate <= toEnd;
        } else if (from) {
          const fromStart = new Date(from);
          fromStart.setHours(0, 0, 0, 0);
          return saleDate >= fromStart;
        } else if (to) {
          const toEnd = new Date(to);
          toEnd.setHours(23, 59, 59, 999);
          return saleDate <= toEnd;
        }
        
        return true;
      });
    }

    // Apply pagination
    const skip = (page - 1) * limit;
    const paginatedSales = filtered.slice(skip, skip + limit);
    
    setSales(paginatedSales);
    setHasMore(skip + paginatedSales.length < filtered.length);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const handleFilter = (from: Date | null, to: Date | null) => {
    setDateFrom(from);
    setDateTo(to);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleClearFilters = () => {
    setDateFrom(null);
    setDateTo(null);
    setCurrentPage(1);
  };

  const handleViewDetail = (saleId: number) => {
    setSelectedSaleId(saleId);
    setIsDetailModalOpen(true);
  };

  const handleCloseDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedSaleId(null);
  };

  const handleEdit = (saleId: number) => {
    setSelectedSaleId(saleId);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setSelectedSaleId(null);
  };

  const handleSaveEdit = (updatedSale: Sale) => {
    // Update sale in both allSales and current page
    setAllSales((prev) =>
      prev.map((sale) => (sale.id === updatedSale.id ? updatedSale : sale))
    );
    setSales((prev) =>
      prev.map((sale) => (sale.id === updatedSale.id ? updatedSale : sale))
    );
    setSuccessMessage("Venta actualizada exitosamente");
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleDeleteClick = (saleId: number) => {
    setSaleToDelete(saleId);
    setIsDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!saleToDelete) return;

    try {
      await deleteSale(saleToDelete);
      
      // Remove sale from both lists
      setAllSales((prev) => prev.filter((sale) => sale.id !== saleToDelete));
      setSales((prev) => prev.filter((sale) => sale.id !== saleToDelete));
      
      setSuccessMessage("Venta eliminada exitosamente");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido";
      setError(`Error al eliminar venta: ${errorMessage}`);
    } finally {
      setIsDeleteDialogOpen(false);
      setSaleToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setIsDeleteDialogOpen(false);
    setSaleToDelete(null);
  };

  const getTotalItems = (sale: Sale): number => {
    return sale.items.reduce((sum, item) => sum + item.cantidad, 0);
  };

  return (
    <div className="sales-container">
      <div className="sales-header">
        <h1>Ventas</h1>
      </div>

      <SalesFilters onFilter={handleFilter} onClear={handleClearFilters} />

      <ErrorAlert message={error} onClose={() => setError(null)} />

      {successMessage && (
        <div className="sales-success-alert">
          <p>{successMessage}</p>
          <button onClick={() => setSuccessMessage(null)} className="close-btn">
            ×
          </button>
        </div>
      )}

      {loading ? (
        <div className="sales-loading">
          {Array.from({ length: 10 }).map((_, index) => (
            <SkeletonLoader key={index} />
          ))}
        </div>
      ) : sales.length === 0 ? (
        <div className="sales-empty">
          <p>
            {dateFrom || dateTo
              ? "No se encontraron ventas en el rango seleccionado"
              : "No se encontraron ventas"}
          </p>
        </div>
      ) : (
        <>
          <div className="sales-table">
            <div className="sales-table-header">
              <div className="sales-col-date">Fecha</div>
              <div className="sales-col-order">N° Orden</div>
              <div className="sales-col-items">Items</div>
              <div className="sales-col-total">Total</div>
              <div className="sales-col-actions">Acciones</div>
            </div>
            
            {sales.map((sale) => (
              <div key={sale.id} className="sales-table-row">
                <div className="sales-col-date">
                  {formatDateDisplay(sale.fecha_creacion)}
                </div>
                <div className="sales-col-order">
                  {sale.numero_orden || `#${sale.id}`}
                </div>
                <div className="sales-col-items">
                  {getTotalItems(sale)}
                </div>
                <div className="sales-col-total">
                  {formatCurrency(sale.total)}
                </div>
                <div className="sales-col-actions">
                  <button
                    className="sales-action-btn view"
                    onClick={() => handleViewDetail(sale.id)}
                    title="Ver detalle"
                  >
                    <EyeIcon size={18} />
                  </button>
                  <button
                    className="sales-action-btn edit"
                    onClick={() => handleEdit(sale.id)}
                    title="Editar venta"
                  >
                    <EditIcon size={18} />
                  </button>
                  <button
                    className="sales-action-btn delete"
                    onClick={() => handleDeleteClick(sale.id)}
                    title="Eliminar venta"
                  >
                    <TrashIcon size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="sales-pagination">
            <button
              className="sales-pagination-btn"
              onClick={handlePrevPage}
              disabled={currentPage === 1}
            >
              ← Anterior
            </button>
            
            <span className="sales-pagination-info">
              Página {currentPage}
            </span>
            
            <button
              className="sales-pagination-btn"
              onClick={handleNextPage}
              disabled={!hasMore}
            >
              Siguiente →
            </button>
          </div>
        </>
      )}

      <SaleDetailModal
        saleId={selectedSaleId}
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetailModal}
      />

      <SaleEditModal
        saleId={selectedSaleId}
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        onSave={handleSaveEdit}
        allProducts={allProducts}
        allOffers={allOffers}
      />

      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        title="Confirmar Eliminación"
        message={
          saleToDelete
            ? `¿Estás seguro de que deseas eliminar la venta ${
                allSales.find((s) => s.id === saleToDelete)?.numero_orden ||
                `#${saleToDelete}`
              }?`
            : ""
        }
        confirmText="Eliminar"
        cancelText="Cancelar"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        confirmDanger
      />
    </div>
  );
};

export default SalesPage;

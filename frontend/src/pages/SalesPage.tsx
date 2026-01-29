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
  // Cache products and offers for use in detail/edit modals (Phase 2+)
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [allOffers, setAllOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [limit] = useState(10);
  const [totalSales, setTotalSales] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

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

  // Fetch sales when page or filters change
  useEffect(() => {
    const fetchSales = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const skip = (currentPage - 1) * limit;
        const data = await getSales(skip, limit, dateFrom, dateTo);
        
        setSales(data.items || []);
        setTotalSales(data.total || 0);
        setTotalPages(Math.ceil((data.total || 0) / limit));
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        setError(`Error al cargar ventas: ${errorMessage}`);
        console.error("Error fetching sales:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSales();
  }, [currentPage, limit, dateFrom, dateTo]); // Re-fetch cuando cambian los filtros de fecha

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const handleGoToPage = (page: number) => {
    setCurrentPage(page);
  };

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow + 2) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);
      
      if (currentPage > 3) {
        pages.push('...');
      }
      
      // Show pages around current page
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      if (currentPage < totalPages - 2) {
        pages.push('...');
      }
      
      // Always show last page
      pages.push(totalPages);
    }
    
    return pages;
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

  const handleSaveEdit = async (updatedSale: Sale) => {
    // Refresh current page
    const skip = (currentPage - 1) * limit;
    const data = await getSales(skip, limit);
    setSales(data.items || []);
    
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
      
      // Refresh current page
      const skip = (currentPage - 1) * limit;
      const data = await getSales(skip, limit);
      setSales(data.items || []);
      setTotalSales(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / limit));
      
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
              className="sales-pagination-btn nav"
              onClick={handlePrevPage}
              disabled={currentPage === 1}
            >
              ← Anterior
            </button>
            
            <div className="sales-pagination-numbers">
              {getPageNumbers().map((page, index) => (
                typeof page === 'number' ? (
                  <button
                    key={index}
                    className={`sales-pagination-number ${currentPage === page ? 'active' : ''}`}
                    onClick={() => handleGoToPage(page)}
                  >
                    {page}
                  </button>
                ) : (
                  <span key={index} className="sales-pagination-ellipsis">
                    {page}
                  </span>
                )
              ))}
            </div>
            
            <button
              className="sales-pagination-btn nav"
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
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
            ? `¿Estás seguro de que deseas eliminar esta venta?`
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

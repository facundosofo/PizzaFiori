import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import ProductosPage from "./pages/ProductsPage";
import SalesPage from "./pages/SalesPage";
import SalesCreatePage from "./pages/SalesCreate";
import OffersPage from "./pages/OffersPage";
import DashboardOverview from "./pages/DashboardOverview";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/productos" element={<ProductosPage />} />
        <Route path="/ofertas" element={<OffersPage />} />
        <Route path="/ventas" element={<SalesPage />} />
        <Route path="/registrar-venta" element={<SalesCreatePage />} />
        <Route path="/dashboard" element={<DashboardOverview />} />
        <Route path="/reportes" element={<DashboardOverview />} />
      </Routes>
    </Router>
  );
}

export default App;

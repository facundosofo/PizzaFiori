import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import ProductosPage from "./pages/ProductsPage";
import SalesPage from "./pages/SalesPage";
import OffersPage from "./pages/OffersPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/productos" element={<ProductosPage />} />
        <Route path="/ofertas" element={<OffersPage />} />
        <Route path="/ventas" element={<SalesPage />} />
      </Routes>
    </Router>
  );
}

export default App;

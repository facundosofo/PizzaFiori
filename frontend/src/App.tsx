import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import UserProfilePage from "./pages/UserProfilePage";
import UserManagementPage from "./pages/UserManagementPage";
import { HomePage } from "./pages/HomePage";
import ProductosPage from "./pages/ProductsPage";
import SalesPage from "./pages/SalesPage";
import SalesCreatePage from "./pages/SalesCreate";
import OffersPage from "./pages/OffersPage";
import DashboardOverview from "./pages/DashboardOverview";
import AppLayout from "./components/layout/AppLayout";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<HomePage />} />
            <Route path="/productos" element={<ProductosPage />} />
            <Route path="/ofertas" element={<OffersPage />} />
            <Route path="/ventas" element={<SalesPage />} />
            <Route path="/registrar-venta" element={<SalesCreatePage />} />
            <Route path="/dashboard" element={<DashboardOverview />} />
            <Route path="/profile" element={<UserProfilePage />} />
            <Route path="/admin/users" element={<UserManagementPage />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

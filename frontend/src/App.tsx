import { lazy, Suspense } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { useZoom } from "./hooks/useZoom";
import AppLayout from "./components/layout/AppLayout";

function ZoomController() {
  useZoom();
  return null;
}

// Each page is a separate chunk — heavy libs (recharts, framer-motion) only
// download when the user first navigates to the route that needs them.
const LoginPage = lazy(() => import("./pages/LoginPage"));
const UserProfilePage = lazy(() => import("./pages/UserProfilePage"));
const UserManagementPage = lazy(() => import("./pages/UserManagementPage"));
const HomePage = lazy(() =>
  import("./pages/HomePage").then((m) => ({ default: m.HomePage }))
);
const ProductosPage = lazy(() => import("./pages/ProductsPage"));
const OffersPage = lazy(() => import("./pages/OffersPage"));
const SalesPage = lazy(() => import("./pages/SalesPage"));
const SalesCreatePage = lazy(() => import("./pages/SalesCreate"));
const DashboardOverview = lazy(() => import("./pages/DashboardOverview"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const AuditPage = lazy(() => import("./pages/AuditPage"));
const ExpensesPage = lazy(() => import("./pages/ExpensesPage"));
const StockPage = lazy(() => import("./pages/StockPage"));

function App() {
  return (
    <AuthProvider>
      <Router>
        <ZoomController />
        <Suspense fallback={null}>
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
              <Route path="/reportes" element={<ReportsPage />} />
              <Route path="/auditoria" element={<AuditPage />} />
              <Route path="/gastos" element={<ExpensesPage />} />
              <Route path="/stock" element={<StockPage />} />
              <Route path="/profile" element={<UserProfilePage />} />
              <Route path="/admin/users" element={<UserManagementPage />} />
            </Route>
          </Routes>
        </Suspense>
      </Router>
    </AuthProvider>
  );
}

export default App;

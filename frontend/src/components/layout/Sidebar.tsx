import { useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Boxes,
  ChartLine,
  FileText,
  Home,
  LogOut,
  Moon,
  PanelRight,
  Pizza,
  ShoppingBasket,
  Sun,
  Wallet,
  Receipt,
  FileSearch,
  Tags,
  Users,
  Cog,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { usePersistentState } from "../../utils/usePersistentState";

export type SidebarProps = {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNavigate: () => void;
};

const navItems = [
  { label: "Home", to: "/", icon: Home },
  { label: "Registrar venta", to: "/registrar-venta", icon: ShoppingBasket },
  { label: "Ventas", to: "/ventas", icon: Receipt },
  { label: "Stock", to: "/stock", icon: Boxes }
];

const adminNavItems = [
  { label: "Ofertas", to: "/ofertas", icon: Tags, adminOnly: true },
  { label: "Productos", to: "/productos", icon: Pizza, adminOnly: true },
  { label: "Gastos", to: "/gastos", icon: Wallet, adminOnly: true },
  { label: "Dashboard", to: "/dashboard", icon: ChartLine, adminOnly: true },
  { label: "Reportes", to: "/reportes", icon: FileText, adminOnly: true },
  { label: "Auditoría", to: "/auditoria", icon: FileSearch, adminOnly: true },
  { label: "Gestión Usuarios", to: "/admin/users", icon: Users, adminOnly: true },
  { label: "Configuración", to: "/admin/config", icon: Cog, adminOnly: true }
];

const Sidebar = ({ collapsed, onToggleCollapse, onNavigate }: SidebarProps) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [themeMode, setThemeMode] = usePersistentState<"light" | "dark">(
    "ui-theme",
    "dark"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
    document.documentElement.style.colorScheme = themeMode;
  }, [themeMode]);

  const isAdmin = user?.role === 'ADMIN';

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (error) {
      // Ignore logout errors
    }
  };

  const handleThemeToggle = () => {
    setThemeMode((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <aside className={`sidebar ${collapsed ? "is-collapsed" : "is-expanded"}`}>
      <div className="sidebar-inner">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="sidebar-brand-text">Pizza Fiori</span>
          </div>
          <div className="sidebar-actions">
            <button
              type="button"
              className="sidebar-action"
              onClick={onToggleCollapse}
              aria-label={collapsed ? "Expandir menu" : "Colapsar menu"}
            >
              <PanelRight size={18} />
            </button>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Navegacion principal">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? "is-active" : ""}`
                }
              >
                <span className="sidebar-icon">
                  <Icon size={20} />
                </span>
                <span className="sidebar-label">{item.label}</span>
              </NavLink>
            );
          })}

          {/* Admin-only navigation items */}
          {isAdmin && (
            <>
              <div className="sidebar-divider" />
              {adminNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `sidebar-link ${isActive ? "is-active" : ""}`
                    }
                  >
                    <span className="sidebar-icon">
                      <Icon size={20} />
                    </span>
                    <span className="sidebar-label">{item.label}</span>
                  </NavLink>
                );
              })}
            </>
          )}
        </nav>

        {/* User profile section */}
        <div className="sidebar-footer">
          <div className="sidebar-theme">
            <span className="sidebar-theme-label">Tema</span>
            <label
              className={`sidebar-theme-toggle ${
                themeMode === "dark" ? "is-dark" : "is-light"
              }`}
            >
              <input
                type="checkbox"
                checked={themeMode === "dark"}
                onChange={handleThemeToggle}
                aria-label="Cambiar tema"
              />
              <span className="sidebar-theme-track" aria-hidden="true">
                <span title="Modo claro">
                  <Sun size={14} className="sidebar-theme-icon sidebar-theme-icon-sun" />
                </span>
                <span title="Modo oscuro">
                  <Moon size={14} className="sidebar-theme-icon sidebar-theme-icon-moon" />
                </span>
                <span className="sidebar-theme-thumb" />
              </span>
            </label>
          </div>

          <NavLink
            to="/profile"
            onClick={onNavigate}
            className={({ isActive }) =>
              `sidebar-link sidebar-user ${isActive ? "is-active" : ""}`
            }
          >
            <span className="sidebar-icon">
              <div className="user-avatar">
                {user?.first_name?.charAt(0).toUpperCase() || "U"}
                {user?.last_name?.charAt(0).toUpperCase() || "S"}
              </div>
            </span>
            <span className="sidebar-label">
              <div className="user-info">
                <div className="user-name">
                  {user?.first_name} {user?.last_name}
                </div>
                <div className="user-role">{user?.role === 'ADMIN' ? 'ADMINISTRADOR' : 'USUARIO'}</div>
              </div>
            </span>
          </NavLink>

          <button
            type="button"
            className="sidebar-link sidebar-logout"
            onClick={handleLogout}
            aria-label="Cerrar sesión"
          >
            <span className="sidebar-icon">
              <LogOut size={20} />
            </span>
            <span className="sidebar-label">Cerrar sesión</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

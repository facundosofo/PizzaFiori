import { NavLink, useNavigate } from "react-router-dom";
import {
  ChartLine,
  Home,
  LogOut,
  PanelRight,
  Pizza,
  PlusCircle,
  Receipt,
  Settings,
  Tag,
  Users,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

export type SidebarProps = {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNavigate: () => void;
};

const navItems = [
  { label: "Home", to: "/", icon: Home },
  { label: "Ventas", to: "/ventas", icon: Receipt },
  { label: "Registrar venta", to: "/registrar-venta", icon: PlusCircle },
  { label: "Productos", to: "/productos", icon: Pizza },
  { label: "Ofertas", to: "/ofertas", icon: Tag },
  { label: "Dashboard", to: "/dashboard", icon: ChartLine },
];

const adminNavItems = [
  { label: "Gestión Usuarios", to: "/admin/users", icon: Users, adminOnly: true },
];

const Sidebar = ({ collapsed, onToggleCollapse, onNavigate }: SidebarProps) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const isAdmin = user?.role === 'ADMIN';

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (error) {
      // Ignore logout errors
    }
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
                <div className="user-role">{user?.role}</div>
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

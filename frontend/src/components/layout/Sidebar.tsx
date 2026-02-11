import { NavLink } from "react-router-dom";
import {
  Home,
  LayoutDashboard,
  Menu,
  Package,
  PlusCircle,
  Receipt,
  Tag,
} from "lucide-react";

export type SidebarProps = {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNavigate: () => void;
};

const navItems = [
  { label: "Home", to: "/", icon: Home },
  { label: "Ventas", to: "/ventas", icon: Receipt },
  { label: "Registrar venta", to: "/registrar-venta", icon: PlusCircle },
  { label: "Productos", to: "/productos", icon: Package },
  { label: "Ofertas", to: "/ofertas", icon: Tag },
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
];

const Sidebar = ({ collapsed, onToggleCollapse, onNavigate }: SidebarProps) => {
  return (
    <aside className={`sidebar ${collapsed ? "is-collapsed" : "is-expanded"}`}>
      <div className="sidebar-inner">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="sidebar-brand-text">PizzaFiori</span>
          </div>
          <div className="sidebar-actions">
            <button
              type="button"
              className="sidebar-action"
              onClick={onToggleCollapse}
              aria-label={collapsed ? "Expandir menu" : "Colapsar menu"}
            >
              <Menu size={18} />
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
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;

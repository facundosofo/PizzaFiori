import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import { usePersistentState } from "../../utils/usePersistentState";
import "../../styles/sidebar.css";

const AppLayout = () => {
  const [collapsed, setCollapsed] = usePersistentState("sidebar-collapsed", true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 960px)");
    const handleChange = () => setIsMobile(media.matches);

    handleChange();
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  const handleToggleCollapse = () => {
    setCollapsed((prev) => !prev);
  };

  const handleNavigate = () => {
    return;
  };

  const showOverlay = !collapsed && isMobile;

  return (
    <div className={`app-layout ${collapsed ? "is-collapsed" : "is-expanded"}`}>
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={handleToggleCollapse}
        onNavigate={handleNavigate}
      />
      <main className="app-content">
        <Outlet />
      </main>
      {showOverlay && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Cerrar menu"
          onClick={() => setCollapsed(true)}
        />
      )}
    </div>
  );
};

export default AppLayout;

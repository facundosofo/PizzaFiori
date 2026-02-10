import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import { usePersistentState } from "../../utils/usePersistentState";
import "../../styles/sidebar.css";

const AppLayout = () => {
  const [collapsed, setCollapsed] = usePersistentState("sidebar-collapsed", true);
  const [pinned, setPinned] = usePersistentState("sidebar-pinned", false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 960px)");
    const handleChange = () => setIsMobile(media.matches);

    handleChange();
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    if (pinned && collapsed) {
      setCollapsed(false);
    }
  }, [pinned, collapsed, setCollapsed]);

  const handleToggleCollapse = () => {
    setCollapsed((prev) => {
      const next = !prev;
      if (next) {
        setPinned(false);
      }
      return next;
    });
  };

  const handleTogglePin = () => {
    setPinned((prev) => {
      const next = !prev;
      if (next) {
        setCollapsed(false);
      }
      return next;
    });
  };

  const handleNavigate = () => {
    if (!pinned && isMobile) {
      setCollapsed(true);
    }
  };

  const showOverlay = !pinned && !collapsed && isMobile;

  return (
    <div className={`app-layout ${collapsed ? "is-collapsed" : "is-expanded"}`}>
      <Sidebar
        collapsed={collapsed}
        pinned={pinned}
        onToggleCollapse={handleToggleCollapse}
        onTogglePin={handleTogglePin}
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

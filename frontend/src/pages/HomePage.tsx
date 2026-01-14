import { motion } from "framer-motion";
import logo from "../assets/PizzaFioriLogo.png";
import { ModuleCard } from "../components/ModuleCard";
import "../styles/home.css";

export const HomePage = () => {
  return (
    <div className="home-container">
      {/* LOGO */}
      <motion.img
        src={logo}
        alt="PizzaFiori"
        className="logo"
        initial={{ scale: 1.4 }}
        animate={{ scale: 0.85, y: -90 }}
        transition={{
          duration: 1.5,
          ease: "easeInOut",
        }}
      />

      {/* MÓDULOS */}
      <motion.div
        className="modules"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          delay: 1,
          duration: 0.6,
        }}
      >
        <ModuleCard title="Productos" />
        <ModuleCard title="Ventas" />
        <ModuleCard title="Reportes" />
      </motion.div>
    </div>
  );
};

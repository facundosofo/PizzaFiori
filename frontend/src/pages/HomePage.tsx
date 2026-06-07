import { motion } from "framer-motion";
import logo from "../assets/PizzaFioriLogo.png";
import { useAuth } from "../contexts/AuthContext";
import "../styles/home.css";

export const HomePage = () => {
  const { user } = useAuth();

  return (
    <div className="home-container">
      {/* LOGO */}
      <motion.img
        src={logo}
        alt="PizzaFiori"
        className="logo"
        initial={{ scale: 1.4, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{
          duration: 1.5,
          ease: "easeInOut",
        }}
      />

      {/* MENSAJE DE BIENVENIDA */}
      <motion.div
        className="welcome-message"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.8 }}
      >
        <h1>
          ¡Bienvenido{user && `, ${user.first_name}`}!
        </h1>
        <p>Utiliza el menú lateral para navegar por las diferentes secciones</p>
      </motion.div>
    </div>
  );
};

import { motion } from "framer-motion";
import "../styles/skeleton.css";

const SkeletonLoader = () => {
  return (
    <motion.div
      className="skeleton-card"
      initial={{ opacity: 0.6 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.5, repeat: Infinity, repeatType: "reverse" }}
    >
      <div className="skeleton-image"></div>
      <div className="skeleton-title"></div>
      <div className="skeleton-price"></div>
    </motion.div>
  );
};

export default SkeletonLoader;

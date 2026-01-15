import { motion, AnimatePresence } from "framer-motion";
import "../styles/error-alert.css";

interface ErrorAlertProps {
  message: string | null;
  onClose: () => void;
  autoCloseDuration?: number;
}

const ErrorAlert = ({
  message,
  onClose,
  autoCloseDuration = 5000,
}: ErrorAlertProps) => {
  if (message) {
    setTimeout(() => {
      onClose();
    }, autoCloseDuration);
  }

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          className="error-alert"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          <div className="error-alert-content">
            <span className="error-alert-icon">❌</span>
            <div className="error-alert-text">
              <p className="error-alert-title">Error</p>
              <p className="error-alert-message">{message}</p>
              <p className="error-alert-contact">
                Si el problema persiste, contacta al administrador de sistema.
              </p>
            </div>
            <button
              className="error-alert-close"
              onClick={onClose}
              aria-label="Cerrar alerta"
            >
              ✕
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ErrorAlert;

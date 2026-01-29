import { motion, AnimatePresence } from "framer-motion";
import "../../styles/shared/confirm-dialog.css";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: React.ReactNode;
  message: React.ReactNode;
  warning?: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmDanger?: boolean;
  confirmDisabled?: boolean;
  cancelDisabled?: boolean;
}

const ConfirmDialog = ({
  isOpen,
  title,
  message,
  warning,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  onConfirm,
  onCancel,
  confirmDanger = false,
  confirmDisabled = false,
  cancelDisabled = false,
}: ConfirmDialogProps) => {
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="confirm-overlay"
          onClick={handleOverlayClick}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div
            className="confirm-dialog"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <h3 className="confirm-title">{title}</h3>
            <p className="confirm-message">{message}</p>
            {warning ? <p className="confirm-warning">{warning}</p> : null}

            <div className="confirm-actions">
              <button
                className="confirm-cancel-btn"
                onClick={onCancel}
                disabled={cancelDisabled}
              >
                {cancelText}
              </button>
              <button
                className={confirmDanger ? "confirm-deactivate-btn" : "confirm-confirm-btn"}
                onClick={onConfirm}
                disabled={confirmDisabled}
              >
                {confirmText}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ConfirmDialog;

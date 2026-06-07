import { forwardRef } from "react";
import { Calendar } from "lucide-react";

export type DateRangeInputProps = {
  value?: string;
  onClick?: () => void;
  placeholder?: string;
};

const DateRangeInput = forwardRef<HTMLButtonElement, DateRangeInputProps>(
  ({ value, onClick, placeholder }, ref) => (
    <button
      type="button"
      className="filter-date-input filter-date-input-icon"
      onClick={onClick}
      ref={ref}
    >
      <Calendar size={16} className="filter-date-icon" />
      <span className="filter-date-label">{value || placeholder}</span>
    </button>
  )
);

DateRangeInput.displayName = "DateRangeInput";

export default DateRangeInput;

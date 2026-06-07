import "../../styles/shared/radio-group.css";

export interface RadioOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface RadioGroupProps {
  name: string;
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  label?: string;
  className?: string;
}

const RadioGroup = ({
  name,
  options,
  value,
  onChange,
  label,
  className = "",
}: RadioGroupProps) => {
  return (
    <div className={`radio-group ${className}`}>
      {label && <label className="radio-group-label">{label}</label>}
      <div className="radio-group-options">
        {options.map((option) => (
          <label
            key={option.value}
            className={`radio-option ${value === option.value ? "radio-option-selected" : ""} ${
              option.disabled ? "radio-option-disabled" : ""
            }`}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange(e.target.value)}
              disabled={option.disabled}
              className="radio-input"
            />
            <span className="radio-label">{option.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

export default RadioGroup;

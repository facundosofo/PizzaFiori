import { formatStockQuantityParts } from "../../utils/stockQuantityFormatter";
import type { StockQuantityFormatOptions } from "../../utils/stockQuantityFormatter";

interface StockQuantityDisplayProps {
  value: unknown;
  className?: string;
  formatOptions?: StockQuantityFormatOptions;
}

const StockQuantityDisplay = ({ value, className = "", formatOptions }: StockQuantityDisplayProps) => {
  const parts = formatStockQuantityParts(value, formatOptions);

  return (
    <span className={`stock-quantity-display ${className}`.trim()}>
      <span className="stock-quantity-display-main">{parts.main}</span>
      {parts.fraction && <span className="stock-quantity-display-fraction">{parts.fraction}</span>}
    </span>
  );
};

export default StockQuantityDisplay;
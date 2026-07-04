const EPSILON = 1e-9;
const TOLERANCE = 1e-3;

const gcd = (a: number, b: number): number => {
  let x = Math.abs(a);
  let y = Math.abs(b);

  while (y !== 0) {
    const remainder = x % y;
    x = y;
    y = remainder;
  }

  return x || 1;
};

const toNumber = (value: unknown): number => {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  if (typeof value === "string") {
    const parsed = parseFloat(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

export interface StockQuantityFormatOptions {
  preferredDenominator?: number;
  reduceFraction?: boolean;
}

export const formatStockQuantity = (value: unknown, options?: StockQuantityFormatOptions): string => {
  const parts = formatStockQuantityParts(value, options);
  if (parts.fraction) {
    const base = parts.main === "0" ? parts.fraction : `${parts.main} ${parts.fraction}`;
    return `${parts.sign}${base}`;
  }

  return `${parts.sign}${parts.main}`;
};

export const formatStockQuantityParts = (
  value: unknown,
  options?: StockQuantityFormatOptions,
): { sign: string; main: string; fraction: string | null } => {
  const quantity = toNumber(value);
  const reduceFraction = options?.reduceFraction ?? true;

  if (Math.abs(quantity) < EPSILON) {
    return { sign: "", main: "0", fraction: null };
  }

  const sign = quantity < 0 ? "-" : "";
  const absoluteQuantity = Math.abs(quantity);
  const wholePart = Math.floor(absoluteQuantity + EPSILON);
  const fractionPart = absoluteQuantity - wholePart;

  const preferredDenominator = options?.preferredDenominator;
  if (preferredDenominator && preferredDenominator > 1) {
    const scaled = Math.round(fractionPart * preferredDenominator);
    if (Math.abs(fractionPart * preferredDenominator - scaled) <= TOLERANCE) {
      if (scaled === 0) {
        return { sign, main: `${wholePart}`, fraction: null };
      }

      if (scaled === preferredDenominator) {
        return { sign, main: `${wholePart + 1}`, fraction: null };
      }

      const divisor = reduceFraction ? gcd(scaled, preferredDenominator) : 1;
      const numerator = scaled / divisor;
      const denominator = preferredDenominator / divisor;
      const fraction = `${numerator}/${denominator}`;

      return wholePart > 0
        ? { sign, main: `${wholePart}`, fraction }
        : { sign, main: "0", fraction };
    }
  }

  const eighths = Math.round(fractionPart * 8);
  if (Math.abs(fractionPart * 8 - eighths) <= TOLERANCE) {
    if (eighths === 0) {
      return { sign, main: `${wholePart}`, fraction: null };
    }

    if (eighths === 8) {
      return { sign, main: `${wholePart + 1}`, fraction: null };
    }

    const divisor = reduceFraction ? gcd(eighths, 8) : 1;
    const numerator = eighths / divisor;
    const denominator = 8 / divisor;
    const fraction = `${numerator}/${denominator}`;

    return wholePart > 0
      ? { sign, main: `${wholePart}`, fraction }
      : { sign, main: "0", fraction };
  }

  const compact = Number(absoluteQuantity.toFixed(3))
    .toString()
    .replace(/\.0+$/, "")
    .replace(/(\.\d*?[1-9])0+$/, "$1");

  return { sign, main: compact, fraction: null };
};
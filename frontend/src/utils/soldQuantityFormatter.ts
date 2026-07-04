const EPS = 1e-9;

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const toNumber = (value: unknown): number | null => {
  if (isFiniteNumber(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const inferDenominator = (
  baseQuantity?: number | null,
  itemName?: string | null,
  categoryName?: string | null,
): number => {
  const base = toNumber(baseQuantity);
  if (base && base > 0 && base < 1) {
    const inverse = Math.round(1 / base);
    if ([2, 4, 8].includes(inverse)) return inverse;
  }

  const text = `${itemName ?? ""} ${categoryName ?? ""}`.toLowerCase();
  if (text.includes("tarta")) return 4;
  return 8;
};

export const formatMixedFraction = (
  quantityRaw: unknown,
  options?: {
    baseQuantity?: number | null;
    itemName?: string | null;
    categoryName?: string | null;
    fallbackDenominator?: 2 | 4 | 8;
  },
): string => {
  const quantity = toNumber(quantityRaw) ?? 0;
  if (!Number.isFinite(quantity) || Math.abs(quantity) < EPS) return "0";

  const sign = quantity < 0 ? "-" : "";
  const abs = Math.abs(quantity);
  const whole = Math.floor(abs + EPS);

  const denominator =
    options?.fallbackDenominator ??
    inferDenominator(options?.baseQuantity, options?.itemName, options?.categoryName);

  const fractional = abs - whole;
  let numerator = Math.round(fractional * denominator);

  if (numerator === 0) return `${sign}${whole}`;
  if (numerator >= denominator) {
    return `${sign}${whole + 1}`;
  }

  if (whole === 0) return `${sign}${numerator}/${denominator}`;
  return `${sign}${whole} ${numerator}/${denominator}`;
};

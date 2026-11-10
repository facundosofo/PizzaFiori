import env from "../config/env";

interface ProductImageSource {
  imagen?: string | null;
  fecha_actualizacion: string;
}

export const getProductImageUrl = (
  product: ProductImageSource,
  fallback = "/placeholder.png",
): string => {
  if (!product.imagen) return fallback;

  const imageUrl = `${env.API_BASE_URL}/${product.imagen}`;
  const separator = imageUrl.includes("?") ? "&" : "?";
  return `${imageUrl}${separator}v=${encodeURIComponent(product.fecha_actualizacion)}`;
};

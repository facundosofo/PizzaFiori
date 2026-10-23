export interface CatalogPrice {
  cantidad: string;
  precio: string;
}

export interface CatalogCategory {
  id: number;
  nombre: string;
}

export interface CatalogProduct {
  id: number;
  nombre: string;
  categoria_id: number;
  imagen_url: string | null;
  precios: CatalogPrice[];
}

export interface CatalogOfferItem {
  cantidad: string;
  categoria_id: number | null;
  producto_ids: number[];
}

export interface CatalogOffer {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio: string;
  items: CatalogOfferItem[];
}

export interface PublicCatalog {
  version: number;
  publicado_en: string;
  categorias: CatalogCategory[];
  productos: CatalogProduct[];
  ofertas: CatalogOffer[];
}

interface CatalogPointer {
  version: number;
  catalogo_version: string;
  publicado_en: string;
  catalogo_url: string;
}

export class CatalogLoadError extends Error {}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteNumberString(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Number(value));
}

function isImageUrl(value: unknown): value is string | null {
  if (value === null) return true;
  if (typeof value !== "string") return false;
  try {
    return new URL(value).protocol === "https:";
  } catch {
    return false;
  }
}

function isCatalogCategory(value: unknown): value is CatalogCategory {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isInteger(value.id) &&
    typeof value.nombre === "string"
  );
}

function isCatalogPrice(value: unknown): value is CatalogPrice {
  return (
    isRecord(value) &&
    isFiniteNumberString(value.cantidad) &&
    isFiniteNumberString(value.precio)
  );
}

function isCatalogProduct(value: unknown): value is CatalogProduct {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isInteger(value.id) &&
    typeof value.nombre === "string" &&
    typeof value.categoria_id === "number" &&
    Number.isInteger(value.categoria_id) &&
    isImageUrl(value.imagen_url) &&
    Array.isArray(value.precios) &&
    value.precios.every(isCatalogPrice)
  );
}

function isCatalogOfferItem(value: unknown): value is CatalogOfferItem {
  return (
    isRecord(value) &&
    isFiniteNumberString(value.cantidad) &&
    (value.categoria_id === null ||
      (typeof value.categoria_id === "number" &&
        Number.isInteger(value.categoria_id))) &&
    Array.isArray(value.producto_ids) &&
    value.producto_ids.every(
      (productId) => typeof productId === "number" && Number.isInteger(productId),
    )
  );
}

function isCatalogOffer(value: unknown): value is CatalogOffer {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isInteger(value.id) &&
    typeof value.nombre === "string" &&
    (typeof value.descripcion === "string" || value.descripcion === null) &&
    isFiniteNumberString(value.precio) &&
    Array.isArray(value.items) &&
    value.items.every(isCatalogOfferItem)
  );
}

function parsePointer(value: unknown, expectedOrigin: string): CatalogPointer {
  if (
    !isRecord(value) ||
    typeof value.catalogo_version !== "string" ||
    typeof value.publicado_en !== "string" ||
    typeof value.catalogo_url !== "string" ||
    typeof value.version !== "number" ||
    !Number.isInteger(value.version)
  ) {
    throw new CatalogLoadError("El índice del catálogo tiene un formato inválido.");
  }

  let catalogUrl: URL;
  try {
    catalogUrl = new URL(value.catalogo_url);
  } catch {
    throw new CatalogLoadError("La dirección del catálogo publicado no es válida.");
  }
  if (catalogUrl.protocol !== "https:" || catalogUrl.origin !== expectedOrigin) {
    throw new CatalogLoadError(
      "El catálogo debe estar en HTTPS y en el mismo dominio que su índice.",
    );
  }

  return {
    version: value.version,
    catalogo_version: value.catalogo_version,
    publicado_en: value.publicado_en,
    catalogo_url: value.catalogo_url,
  };
}

function parseCatalog(value: unknown): PublicCatalog {
  if (
    !isRecord(value) ||
    typeof value.version !== "number" ||
    !Number.isInteger(value.version) ||
    typeof value.publicado_en !== "string" ||
    !Array.isArray(value.categorias) ||
    !Array.isArray(value.productos) ||
    !Array.isArray(value.ofertas) ||
    !value.categorias.every(isCatalogCategory) ||
    !value.productos.every(isCatalogProduct) ||
    !value.ofertas.every(isCatalogOffer)
  ) {
    throw new CatalogLoadError("El archivo del catálogo tiene un formato inválido.");
  }

  return {
    version: value.version,
    publicado_en: value.publicado_en,
    categorias: value.categorias,
    productos: value.productos,
    ofertas: value.ofertas,
  };
}

async function getJson(url: string, cache: RequestCache): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, { cache, mode: "cors" });
  } catch {
    throw new CatalogLoadError(
      "No se pudo conectar con el catálogo. Revisá tu conexión e intentá nuevamente.",
    );
  }

  if (!response.ok) {
    throw new CatalogLoadError(
      `No se pudo cargar el catálogo (error ${response.status}). Intentá nuevamente más tarde.`,
    );
  }

  try {
    return await response.json();
  } catch {
    throw new CatalogLoadError("La respuesta del catálogo no contiene JSON válido.");
  }
}

export async function fetchPublicCatalog(pointerUrl: string): Promise<PublicCatalog> {
  let pointer: URL;
  try {
    pointer = new URL(pointerUrl);
  } catch {
    throw new CatalogLoadError(
      "Falta configurar una URL válida para el catálogo público.",
    );
  }

  if (pointer.protocol !== "https:") {
    throw new CatalogLoadError("La URL del catálogo debe comenzar con HTTPS.");
  }

  const currentPointer = parsePointer(
    await getJson(pointer.toString(), "no-cache"),
    pointer.origin,
  );
  const catalog = parseCatalog(
    await getJson(currentPointer.catalogo_url, "force-cache"),
  );

  if (catalog.version !== currentPointer.version) {
    throw new CatalogLoadError(
      "La versión del catálogo no coincide con el índice publicado.",
    );
  }

  return catalog;
}

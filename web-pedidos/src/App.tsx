import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronRight,
  CreditCard,
  Facebook,
  Flame,
  Instagram,
  Leaf,
  LoaderCircle,
  MapPin,
  Minus,
  Plus,
  Phone,
  RefreshCw,
  ShoppingBag,
  SquarePen,
  Sparkles,
  Store,
  Trash2,
} from "lucide-react";
import {
  fetchPublicCatalog,
  type CatalogOffer,
  type CatalogProduct,
  type PublicCatalog,
} from "./catalog";
import appStyles from "./AppShell.module.css";
import checkoutStyles from "./Checkout.module.css";
import menuStyles from "./Menu.module.css";
import offerStyles from "./Offer.module.css";
import pizzaStyles from "./PizzaHalf.module.css";
import productStyles from "./Product.module.css";
import stateStyles from "./States.module.css";

const POINTER_URL = import.meta.env.VITE_CATALOG_POINTER_URL ?? "";
const WHATSAPP_PHONE = import.meta.env.VITE_WHATSAPP_PHONE ?? "";
const FOOTER_WHATSAPP_PHONE = normalizeWhatsAppPhone(WHATSAPP_PHONE);
const INSTAGRAM_URL = getSafeExternalUrl(import.meta.env.VITE_INSTAGRAM_URL);
const FACEBOOK_URL = getSafeExternalUrl(import.meta.env.VITE_FACEBOOK_URL);
const GOOGLE_MAPS_URL = getSafeExternalUrl(import.meta.env.VITE_GOOGLE_MAPS_URL);
const WHATSAPP_URL =
  getSafeExternalUrl(import.meta.env.VITE_WHATSAPP_URL) ??
  (FOOTER_WHATSAPP_PHONE
    ? `https://wa.me/${FOOTER_WHATSAPP_PHONE}`
    : null);
const PHONE_NUMBER = normalizeWhatsAppPhone(
  import.meta.env.VITE_PHONE_NUMBER ?? WHATSAPP_PHONE,
);
const HIDDEN_CATEGORY_NAMES = new Set(
  (import.meta.env.VITE_HIDDEN_CATEGORIES ?? "")
    .split(",")
    .map((name) => name.trim().toLocaleLowerCase("es-AR"))
    .filter(Boolean),
);
const PLACEHOLDER_IMAGE = "/logo.png";
const EMOJI = {
  pizza: String.fromCodePoint(0x1f355),
  cart: String.fromCodePoint(0x1f6d2),
  money: String.fromCodePoint(0x1f4b0),
  scooter: String.fromCodePoint(0x1f6f5),
  cash: String.fromCodePoint(0x1f4b5),
  clipboard: String.fromCodePoint(0x1f4cb),
  person: String.fromCodePoint(0x1f464),
  house: String.fromCodePoint(0x1f3e0),
  card: String.fromCodePoint(0x1f4b3),
  memo: String.fromCodePoint(0x1f4dd),
  pray: String.fromCodePoint(0x1f64f),
  pin: String.fromCodePoint(0x1f4cd),
} as const;

function WhatsAppIcon() {
  return (
    <span className="whatsapp-icon" aria-hidden="true">
      <svg viewBox="0 0 512 512">
        <path
          fill="var(--color-white)"
          d="M500.4,241.8c-0.6,63.4-16.9,113-50.8,156.1c-36.4,46.3-83.8,75.7-141.8,87.6c-44.8,9.1-88.4,5.1-131.2-10.4c-9.5-3.5-18.8-7.6-27.7-12.5c-2.7-1.5-5-1.7-8-0.7c-40.5,13.1-81.1,26.1-121.7,39c-1.8,0.6-4.2,2.3-5.6,1c-1.6-1.6,0.4-4,1-5.9c8.1-24.1,16.2-48.3,24.4-72.4c5-14.7,9.8-29.3,15-43.9c1.4-3.8,0.9-6.7-1.2-10.2c-10.3-17.6-17.9-36.4-23.3-56.1c-10.1-37-11.2-74.4-3.3-111.8c8.6-40.8,26.6-77.2,54.3-108.6c33.5-38,74.8-63.1,123.9-75.2c31.3-7.7,62.9-8.9,94.7-3.7c41.6,6.8,79.1,23.3,111.8,49.9c34,27.7,58.8,62.1,74.4,103.4C493.9,189.7,500.7,226.2,500.4,241.8z M74.6,441.5c24.8-8,48.5-15.6,72-23.3c3.1-1,5.6-0.8,8.3,1c9,6,18.7,10.8,28.7,15c32.5,13.8,66.3,18.8,101.2,14.3c42.8-5.5,80.4-22.7,112-52.6c39.8-37.7,61.1-83.9,63-138.5c1.8-53.5-15.4-100.5-51.3-140.4c-34.1-37.9-76.9-59.5-127.4-64.9c-43.9-4.7-85,4.8-123,27.6c-32.5,19.6-57.4,46.3-74.7,80c-19.1,37.1-25.6,76.5-20.1,117.8c4.1,31.2,15.3,59.9,33.3,85.7c2,2.9,2.6,5.3,1.4,8.7c-3.7,10.2-7,20.5-10.5,30.7C83.3,415.2,79.2,427.8,74.6,441.5z"
        />
        <path
          fill="var(--color-white)"
          d="M141,194.7c0.5-23.8,8.9-41.5,24.8-55.6c5.1-4.6,11.4-6.6,18.5-5.6c3,0.4,6,0.7,9,0.5c5.6-0.3,9.4,2.4,11.3,7.3c6.7,17.4,13.2,34.8,19.7,52.3c2.2,6-1.6,10.7-4.8,15c-3.7,5.1-8.2,9.6-12.6,14.1c-4.5,4.6-5.1,7.2-2,12.8c18.1,32.9,43.5,58.2,78,73.8c1.2,0.5,2.4,1.2,3.6,1.8c4.6,2.1,8.7,1.6,12.2-2.4c6.4-7.5,13.4-14.4,19.3-22.3c3.9-5.2,6.6-6.1,12.5-3.5c17.6,7.6,34.1,17.2,50.9,26.5c3.1,1.7,4.2,4.3,4.1,7.9c-0.9,29.5-17.8,44.9-47.5,51.7c-14.4,3.3-27.7-0.3-40.9-5.1c-27.7-10-54.4-21.8-76.8-41.6c-17.8-15.8-33.5-33.4-46.8-53.1c-10.2-15.2-20.8-30.1-26.7-47.8C143.4,212,140.9,202.4,141,194.7z"
        />
      </svg>
    </span>
  );
}

const PAYMENT_METHODS = ["Efectivo", "Transferencia"] as const;

type CartItem = {
  type: "product";
  key: string;
  productId: number;
  presentation: string;
  count: number;
} | {
  type: "halfPizza";
  key: string;
  leftProductId: number;
  rightProductId: number;
  count: number;
} | {
  type: "offer";
  key: string;
  offerId: number;
  count: number;
  selections: SelectedOfferProduct[];
};

type SelectedOfferProduct = {
  productId: number;
  productName: string;
  quantity: number;
};

type FulfillmentMethod = "delivery" | "pickup";

type OrderForm = {
  name: string;
  fulfillment: FulfillmentMethod | "";
  address: string;
  paymentMethod: string;
  foodNotes: string;
  notes: string;
};

type OrderFormErrors = Partial<Record<keyof OrderForm, string>>;

type ResolvedProductCartItem = Extract<CartItem, { type: "product" }> & {
  product: CatalogProduct;
  subtotalCents: number;
};

type ResolvedOfferCartItem = Extract<CartItem, { type: "offer" }> & {
  offer: CatalogOffer;
  selections: SelectedOfferProduct[];
  subtotalCents: number;
};

type ResolvedHalfPizzaCartItem = Extract<CartItem, { type: "halfPizza" }> & {
  leftProduct: CatalogProduct;
  rightProduct: CatalogProduct;
  subtotalCents: number;
};

type ResolvedCartItem =
  | ResolvedProductCartItem
  | ResolvedHalfPizzaCartItem
  | ResolvedOfferCartItem;

const currencyFormatter = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

function formatCents(cents: number): string {
  return currencyFormatter.format(cents / 100);
}

function formatPercentage(percentage: number): string {
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 }).format(
    percentage,
  );
}

function formatPrice(price: string): string {
  const numericPrice = Number(price);
  return Number.isFinite(numericPrice)
    ? formatCents(Math.round(numericPrice * 100))
    : "Consultar";
}

function getProductUnitPriceCents(product: CatalogProduct): number | null {
  const prices = [...product.precios]
    .map((price) => ({ quantity: Number(price.cantidad), price: Number(price.precio) }))
    .filter((price) => price.quantity > 0 && Number.isFinite(price.price))
    .sort((first, second) => second.quantity - first.quantity);
  if (prices.length === 0) return null;

  let remaining = 1;
  let total = 0;
  for (const price of prices) {
    if (remaining < price.quantity) continue;
    const multiples = Math.floor((remaining + Number.EPSILON) / price.quantity);
    total += price.price * multiples;
    remaining %= price.quantity;
    if (remaining < Number.EPSILON * 10) {
      remaining = 0;
      break;
    }
  }

  if (remaining > 0) {
    const smallestPrice = prices.reduce((smallest, current) =>
      current.quantity < smallest.quantity ? current : smallest,
    );
    total += (smallestPrice.price / smallestPrice.quantity) * remaining;
  }

  return Math.round(total * 100);
}

function isPizzaProduct(
  product: CatalogProduct,
  categories: PublicCatalog["categorias"],
): boolean {
  const categoryName = categories.find(
    (category) => category.id === product.categoria_id,
  )?.nombre.toLocaleLowerCase("es-AR");
  return (
    product.nombre.toLocaleLowerCase("es-AR").includes("pizza") ||
    categoryName === "pizzas"
  );
}

function formatQuantity(quantity: string): string {
  const numericQuantity = Number(quantity);
  if (!Number.isFinite(numericQuantity)) return quantity;
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 }).format(
    numericQuantity,
  );
}

function formatProductPresentation(quantity: string | number): string {
  const numericQuantity = Number(quantity);
  if (!Number.isFinite(numericQuantity)) return String(quantity);
  if (Math.abs(numericQuantity - 1) < 1e-9) return "Unidad";
  if (Math.abs(numericQuantity - 0.5) < 1e-9) return "Porción 1/2";
  if (Math.abs(numericQuantity - 0.25) < 1e-9) return "Porción 1/4";
  if (Math.abs(numericQuantity - 0.125) < 1e-9) return "Porción 1/8";
  if (Math.abs(numericQuantity - 6) < 1e-9) return "1/2 docena";
  if (Math.abs(numericQuantity - 12) < 1e-9) return "Docena";
  return numericQuantity < 1
    ? `Porción ${formatQuantity(String(numericQuantity))}`
    : `${formatQuantity(String(numericQuantity))} unid.`;
}

function formatOfferQuantity(quantity: number): string {
  if (Math.abs(quantity - 0.5) < 1e-9) return "1/2";
  if (Math.abs(quantity - 0.25) < 1e-9) return "1/4";
  if (Math.abs(quantity - 0.125) < 1e-9) return "1/8";
  return formatQuantity(String(quantity));
}

function formatCategoryOfferDescription(
  quantity: number,
  categoryName: string,
): { quantity: string; unit: string; categoryName: string } {
  let quantityLabel: string;
  let unit = "";
  if ([0.125, 0.25, 0.5].some((portion) => Math.abs(quantity - portion) < 1e-9)) {
    quantityLabel = "1";
    unit = "porción";
  } else if (Math.abs(quantity - 6) < 1e-9) {
    quantityLabel = "1/2";
    unit = "Docena";
  } else if (quantity >= 12 && quantity % 12 === 0) {
    const dozens = quantity / 12;
    quantityLabel = formatQuantity(String(dozens));
    unit = dozens === 1 ? "Docena" : "Docenas";
  } else {
    quantityLabel = new Intl.NumberFormat("es-AR", {
      maximumFractionDigits: 6,
    }).format(quantity);
  }
  return {
    quantity: quantityLabel,
    unit,
    categoryName: categoryName.toLocaleLowerCase("es-AR"),
  };
}

function formatOfferSelection(selection: SelectedOfferProduct): string {
  if (selection.quantity < 1) {
    return `${formatProductPresentation(selection.quantity)} de ${selection.productName}`;
  }
  return `${formatOfferQuantity(selection.quantity)} x ${selection.productName}`;
}

function getOfferItemType(item: CatalogOffer["items"][number]): "fixed" | "category" | "options" {
  if (item.categoria_id !== null) return "category";
  if (item.producto_ids.length > 1) return "options";
  return "fixed";
}

function normalizeWhatsAppPhone(value: string): string | null {
  const digits = value.replace(/\D/g, "");
  return /^\d{8,15}$/.test(digits) ? digits : null;
}

function getSafeExternalUrl(value: string | undefined): string | null {
  if (!value?.trim()) return null;

  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:"
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}

function buildWhatsAppMessage(
  items: ResolvedCartItem[],
  order: OrderForm,
  subtotalCents: number,
  surchargeCents: number,
  estimatedTotalCents: number,
  surchargePercentage: number | null,
): string {
  const productLines = items.flatMap((item) => {
    if (item.type === "product") {
      const presentation = Number(item.presentation);
      const portionLabel = presentation > 0 && presentation < 1
        ? ` (${formatProductPresentation(item.presentation)})`
        : "";
      return [
        `-\u00A0${item.count} x ${item.product.nombre}${portionLabel} — ${formatCents(item.subtotalCents)}`,
      ];
    }
    if (item.type === "halfPizza") {
      return [
        `-\u00A0${item.count} x Pizza mitad/mitad: ${item.leftProduct.nombre} / ${item.rightProduct.nombre} — ${formatCents(item.subtotalCents)}`,
      ];
    }
    return [
      `-\u00A0${item.count} x Promo: ${item.offer.nombre} — ${formatCents(item.subtotalCents)}`,
      ...item.selections.map((selection) => `  -\u00A0${formatOfferSelection(selection)}`),
    ];
  });
  const fulfillmentLabel = order.fulfillment === "delivery" ? "Delivery" : "Retiro por el local";
  const deliveryLines =
    order.fulfillment === "delivery"
      ? [`${EMOJI.pin} *Dirección:* ${order.address.trim()}`]
      : [];
  const surchargeLines =
    order.paymentMethod === "Transferencia" && surchargePercentage !== null
      ? [
          `${EMOJI.money} *Recargo por transferencia (${formatPercentage(surchargePercentage)}%):* ${formatCents(surchargeCents)}`,
        ]
      : [];
  const deliveryFeeLines =
    order.fulfillment === "delivery"
      ? [`${EMOJI.scooter} *Envío:* Gratis`]
      : [];
  const estimatedTotalLabel = "Total estimado";

  return [
    `${EMOJI.pizza} *¡Hola, Pizza Fiori!* Quiero hacer este pedido:`,
    "",
    `${EMOJI.cart} *MI PEDIDO*`,
    "",
    ...productLines,
    "",
    `${EMOJI.memo} *Observaciones:* ${order.foodNotes.trim() || "Sin observaciones"}`,
    "",
    `${EMOJI.money} *Subtotal:* ${formatCents(subtotalCents)}`,
    ...surchargeLines,
    ...deliveryFeeLines,
    `${EMOJI.cash} *${estimatedTotalLabel}:* ${formatCents(estimatedTotalCents)}`,
    "",
    "*_Los importes quedan sujetos a confirmación del local._*",
    "",
    `${EMOJI.clipboard} *DATOS DEL PEDIDO*`,
    `${EMOJI.person} *Nombre:* ${order.name.trim()}`,
    `${EMOJI.house} *Entrega:* ${fulfillmentLabel}`,
    ...deliveryLines,
    `${EMOJI.card} *Pago:* ${order.paymentMethod}`,
    `${EMOJI.memo} *Observaciones:* ${order.notes.trim() || "Sin observaciones"}`,
    "",
    `${EMOJI.pray} Quedo atento a la confirmación. ¡Muchas gracias!`,
  ].join("\n");
}

function ProductCard({
  product,
  cart,
  onAdjust,
}: {
  product: CatalogProduct;
  cart: CartItem[];
  onAdjust: (product: CatalogProduct, presentation: string, adjustment: number) => void;
}) {
  const [imageUrl, setImageUrl] = useState(product.imagen_url || PLACEHOLDER_IMAGE);
  const [showPlaceholder, setShowPlaceholder] = useState(!product.imagen_url);

  useEffect(() => {
    setImageUrl(product.imagen_url || PLACEHOLDER_IMAGE);
    setShowPlaceholder(!product.imagen_url);
  }, [product.imagen_url]);

const sortedPrices = [...product.precios].sort(
    (first, second) => {
      const firstQuantity = Number(first.cantidad);
      const secondQuantity = Number(second.cantidad);
      const firstIsUnit = Math.abs(firstQuantity - 1) < 1e-9;
      const secondIsUnit = Math.abs(secondQuantity - 1) < 1e-9;

      if (firstIsUnit !== secondIsUnit) return firstIsUnit ? -1 : 1;
      return firstQuantity - secondQuantity;
    },
  );

  return (
    <article className={`product-card ${productStyles.scope}`}>
      <div className="product-image-wrap">
        <img
          className="product-image"
          src={imageUrl}
          alt={showPlaceholder ? "" : product.nombre}
          loading="lazy"
          onError={() => {
            setImageUrl(PLACEHOLDER_IMAGE);
            setShowPlaceholder(true);
          }}
        />
      </div>
      <div className="product-info">
        <h3>{product.nombre}</h3>
        <div className="price-list" aria-label="Precios por presentación">
          {sortedPrices.map((price) => {
            const count = cart.find(
              (item) =>
                item.type === "product" &&
                item.productId === product.id &&
                item.presentation === price.cantidad,
            )?.count ?? 0;
            return (
              <div className="presentation-row" key={`${price.cantidad}-${price.precio}`}>
                <div className="presentation-price">
                  <span>{formatProductPresentation(price.cantidad)}</span>
                  <strong>{formatPrice(price.precio)}</strong>
                </div>
                {count > 0 ? (
                  <div
                    className="quantity-control presentation-quantity"
                    aria-label={`Cantidad de ${product.nombre}, ${formatProductPresentation(price.cantidad)}`}
                  >
                    <button
                      type="button"
                      aria-label={`Quitar una unidad de ${product.nombre}, ${formatProductPresentation(price.cantidad)}`}
                      onClick={() => onAdjust(product, price.cantidad, -1)}
                    >
                      <Minus size={15} aria-hidden="true" />
                    </button>
                    <span aria-live="polite">{count}</span>
                    <button
                      type="button"
                      aria-label={`Agregar una unidad de ${product.nombre}, ${formatProductPresentation(price.cantidad)}`}
                      onClick={() => onAdjust(product, price.cantidad, 1)}
                    >
                      <Plus size={15} aria-hidden="true" />
                    </button>
                  </div>
                ) : (
                  <button
                    className="action-button product-add-button"
                    type="button"
                    onClick={() => onAdjust(product, price.cantidad, 1)}
                    title="Agregar al pedido"
                    aria-label={`Agregar ${product.nombre}, presentación ${formatProductPresentation(price.cantidad)}, ${formatPrice(price.precio)}`}
                  >
                    <Plus size={15} strokeWidth={3} aria-hidden="true" />
                    <span className="product-add-label">Agregar</span>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </article>
  );
}

function PizzaHalfBuilder({
  products,
  onAdd,
}: {
  products: Array<{ product: CatalogProduct; unitPriceCents: number }>;
  onAdd: (leftProduct: CatalogProduct, rightProduct: CatalogProduct) => void;
}) {
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [firstProductId, setFirstProductId] = useState<number | null>(null);
  const [secondProductId, setSecondProductId] = useState<number | null>(null);
  const [activeSelection, setActiveSelection] = useState<"first" | "second">("first");
  const dialogRef = useRef<HTMLDialogElement>(null);
  const firstProduct = products.find(({ product }) => product.id === firstProductId);
  const secondProduct = products.find(({ product }) => product.id === secondProductId);
  const selectedPrice =
    firstProduct && secondProduct
      ? Math.max(firstProduct.unitPriceCents, secondProduct.unitPriceCents)
      : null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isConfiguring && !dialog.open) dialog.showModal();
    if (!isConfiguring && dialog.open) dialog.close();
  }, [isConfiguring]);

  const closeAndReset = () => {
    setIsConfiguring(false);
    setFirstProductId(null);
    setSecondProductId(null);
    setActiveSelection("first");
  };

  const chooseProduct = (productId: number) => {
    if (activeSelection === "first") {
      setFirstProductId(productId);
      setActiveSelection("second");
      return;
    }
    if (productId === firstProductId) return;
    setSecondProductId(productId);
  };

  return (
    <>
      <article
        className={`product-card half-pizza-product-card ${productStyles.scope} ${pizzaStyles.productScope}`}
      >
        <div className="product-image-wrap">
          <img
            className="product-image"
            src="/pizza-mitad.png"
            alt="Pizza mitad y mitad con dos sabores"
            loading="lazy"
            onError={(event) => {
              event.currentTarget.src = PLACEHOLDER_IMAGE;
            }}
          />
        </div>
        <div className="product-info half-pizza-product-info">
          <h3>Pizza Mitad y Mitad</h3>
          <div className="price-list half-pizza-price-list">
            <div className="presentation-row">
              <p className="half-pizza-description">Combiná dos sabores</p>
              <button
                className="action-button half-pizza-entry-button"
                type="button"
                onClick={() => setIsConfiguring(true)}
              >
                <Plus size={15} aria-hidden="true" />
                <span className="half-pizza-entry-label">Armar</span>
              </button>
            </div>
          </div>
        </div>
      </article>
      <dialog
        ref={dialogRef}
        className={`half-pizza-dialog ${pizzaStyles.dialogScope} ${offerStyles.scope}`}
        aria-labelledby="half-pizza-title"
        onClose={() => {
          if (isConfiguring) setIsConfiguring(false);
        }}
        onCancel={(event) => {
          event.preventDefault();
          closeAndReset();
        }}
        onClick={(event) => {
          if (event.target === event.currentTarget) closeAndReset();
        }}
      >
        <div className="offer-dialog-header">
          <button
            className="offer-dialog-back"
            type="button"
            aria-label="Volver a pizzas"
            onClick={closeAndReset}
          >
            <ArrowLeft size={17} aria-hidden="true" />
          </button>
          <div className="offer-dialog-title">
            <span className="eyebrow">ARMA TU PIZZA</span>
            <h2 id="half-pizza-title">Mitad/Mitad</h2>
          </div>
        </div>
        <p className="offer-dialog-description">
          Elegí dos sabores distintos.
        </p>
        <div className="half-pizza-config">
          <div className="half-pizza-selected">
            <button
              className={`half-pizza-slot${activeSelection === "first" ? " active" : ""}`}
              type="button"
              onClick={() => setActiveSelection("first")}
            >
              <span>Primer sabor</span>
              <strong>{firstProduct?.product.nombre ?? "Elegí un sabor"}</strong>
              {firstProduct && (
                <img
                  src={firstProduct.product.imagen_url || PLACEHOLDER_IMAGE}
                  alt=""
                  onError={(event) => {
                    event.currentTarget.src = PLACEHOLDER_IMAGE;
                  }}
                />
              )}
            </button>
            <button
              className={`half-pizza-slot${activeSelection === "second" ? " active" : ""}`}
              type="button"
              disabled={!firstProduct}
              onClick={() => setActiveSelection("second")}
            >
              <span>Segundo sabor</span>
              <strong>{secondProduct?.product.nombre ?? "Elegí otro sabor"}</strong>
              {secondProduct && (
                <img
                  src={secondProduct.product.imagen_url || PLACEHOLDER_IMAGE}
                  alt=""
                  onError={(event) => {
                    event.currentTarget.src = PLACEHOLDER_IMAGE;
                  }}
                />
              )}
            </button>
          </div>
          <h3 className="half-pizza-step-title">
            {activeSelection === "first" ? "Elegí el primer sabor" : "Elegí el segundo sabor"}
          </h3>
          <div className="half-pizza-options">
            {products.map(({ product, unitPriceCents }) => {
              const isSelected =
                product.id === firstProductId || product.id === secondProductId;
              const isFirstSelected = product.id === firstProductId;
              const isUnavailable =
                (activeSelection === "first" && product.id === secondProductId) ||
                (activeSelection === "second" && product.id === firstProductId);
              return (
                <button
                  className={`half-pizza-option${isSelected ? ` selected ${isFirstSelected ? "selected-first" : "selected-second"}` : ""}`}
                  key={product.id}
                  type="button"
                  disabled={isUnavailable}
                  aria-pressed={isSelected}
                  onClick={() => chooseProduct(product.id)}
                >
                  <img
                    src={product.imagen_url || PLACEHOLDER_IMAGE}
                    alt=""
                    loading="lazy"
                    onError={(event) => {
                      event.currentTarget.src = PLACEHOLDER_IMAGE;
                    }}
                  />
                  <span className="half-pizza-option-info">
                    <strong>{product.nombre}</strong>
                    <small>{formatCents(unitPriceCents)}</small>
                  </span>
                  {isSelected && (
                    <span
                      className={`half-pizza-option-check${isFirstSelected ? " first" : " second"}`}
                    >
                      <Check size={16} aria-hidden="true" />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
        <div className="offer-dialog-footer half-pizza-dialog-footer">
          <strong>
            {selectedPrice === null
              ? "El precio será el de la pizza más cara."
              : formatCents(selectedPrice)}
          </strong>
          <div className="offer-config-actions">
            <button
              className="action-button offer-config-cancel-button"
              type="button"
              onClick={closeAndReset}
            >
              Cancelar
            </button>
            <button
              className="action-button offer-config-confirm-button"
              type="button"
              disabled={!firstProduct || !secondProduct}
              onClick={() => {
                if (!firstProduct || !secondProduct) return;
                onAdd(firstProduct.product, secondProduct.product);
                closeAndReset();
              }}
            >
              <Plus size={15} aria-hidden="true" />
              Agregar al pedido
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}

function CartAndCheckout({
  catalog,
  cart,
  setCart,
  order,
  setOrder,
  isOpen,
  onClose,
}: {
  catalog: PublicCatalog;
  cart: CartItem[];
  setCart: (cart: CartItem[]) => void;
  order: OrderForm;
  setOrder: (order: OrderForm) => void;
  isOpen: boolean;
  onClose: () => void;
}) {
  const [errors, setErrors] = useState<OrderFormErrors>({});
  const [validated, setValidated] = useState(false);
  const [checkoutStep, setCheckoutStep] = useState<"cart" | "details" | "confirm">("cart");
  const [showAllReviewDetails, setShowAllReviewDetails] = useState(false);
  const [showAllReviewProducts, setShowAllReviewProducts] = useState(false);
  const [expandedOfferSelections, setExpandedOfferSelections] = useState<Set<string>>(
    () => new Set(),
  );
  const whatsappPhone = normalizeWhatsAppPhone(WHATSAPP_PHONE);
  const products = new Map(catalog.productos.map((product) => [product.id, product]));
  const offers = new Map(catalog.ofertas.map((offer) => [offer.id, offer]));
  const resolvedCart = cart.flatMap<ResolvedCartItem>((item): ResolvedCartItem[] => {
    if (item.type === "product") {
      const product = products.get(item.productId);
      const price = product?.precios.find(
        (entry) => entry.cantidad === item.presentation,
      );
      if (!product || !price) return [];
      return [{
        ...item,
        product,
        subtotalCents: Math.round(Number(price.precio) * 100) * item.count,
      }];
    }

    if (item.type === "halfPizza") {
      const leftProduct = products.get(item.leftProductId);
      const rightProduct = products.get(item.rightProductId);
      if (!leftProduct || !rightProduct) return [];
      const leftPrice = getProductUnitPriceCents(leftProduct);
      const rightPrice = getProductUnitPriceCents(rightProduct);
      if (leftPrice === null || rightPrice === null) return [];
      return [{
        ...item,
        leftProduct,
        rightProduct,
        subtotalCents: Math.max(leftPrice, rightPrice) * item.count,
      }];
    }

    const offer = offers.get(item.offerId);
    if (!offer) return [];
    return [{
      ...item,
      offer,
      selections: item.selections.map((selection) => ({
        ...selection,
        productName: products.get(selection.productId)?.nombre ?? selection.productName,
      })),
      subtotalCents: Math.round(Number(offer.precio) * 100) * item.count,
    }];
  });
  const totalCents = resolvedCart.reduce((sum, item) => sum + item.subtotalCents, 0);
  const deliveryMinimumCents =
    catalog.monto_minimo_delivery === null
      ? null
      : Math.round(Number(catalog.monto_minimo_delivery) * 100);
  const isDeliveryEligible =
    deliveryMinimumCents !== null && totalCents >= deliveryMinimumCents;
  const deliveryAmountRemainingCents =
    deliveryMinimumCents === null
      ? null
      : Math.max(0, deliveryMinimumCents - totalCents);
  const surchargePercentage =
    catalog.porcentaje_recargo_transferencia === null
      ? null
      : Number(catalog.porcentaje_recargo_transferencia);
  const isTransferPayment = order.paymentMethod === "Transferencia";
  const surchargeCents =
    isTransferPayment && surchargePercentage !== null
      ? Math.round((totalCents * surchargePercentage) / 100)
      : 0;
  const estimatedTotalCents = totalCents + surchargeCents;
  const whatsappMessage = validated
    ? buildWhatsAppMessage(
        resolvedCart,
        order,
        totalCents,
        surchargeCents,
        estimatedTotalCents,
        surchargePercentage,
      )
    : "";
  const encodedWhatsAppMessage = encodeURIComponent(whatsappMessage).replace(/\*/g, "%2A");
  const whatsappUrl = whatsappPhone
    ? `https://api.whatsapp.com/send?phone=${whatsappPhone}&text=${encodedWhatsAppMessage}`
    : null;

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (isDeliveryEligible || order.fulfillment !== "delivery") return;
    setOrder({ ...order, fulfillment: "", address: "" });
    setErrors((current) => ({ ...current, fulfillment: undefined, address: undefined }));
    setValidated(false);
  }, [isDeliveryEligible, order, setOrder]);

  const updateCount = (target: CartItem, adjustment: number) => {
    setCart(cart.flatMap((item) => {
      if (item.key !== target.key) return [item];
      const count = item.count + adjustment;
      return count > 0 ? [{ ...item, count }] : [];
    }));
    setValidated(false);
  };

  const removeItem = (target: CartItem) => {
    setCart(cart.filter((item) => item.key !== target.key));
    setValidated(false);
  };

  const clearCart = () => {
    setCart([]);
    setValidated(false);
  };

  const updateField = <Field extends keyof OrderForm>(
    field: Field,
    value: OrderForm[Field],
  ) => {
    setOrder({ ...order, [field]: value });
    setErrors({ ...errors, [field]: undefined });
    setValidated(false);
  };

  const validateOrder = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors: OrderFormErrors = {};
    if (!order.name.trim()) nextErrors.name = "Ingresá tu nombre.";
    if (!order.fulfillment) {
      nextErrors.fulfillment = "Elegí delivery o retiro por el local.";
    }
    if (order.fulfillment === "delivery" && !isDeliveryEligible) {
      nextErrors.fulfillment = deliveryMinimumCents === null
        ? "El mínimo de delivery todavía no está publicado. Elegí Retiro o pedí que actualicen el catálogo."
        : `El delivery gratis está disponible a partir de ${formatCents(deliveryMinimumCents)}. ` +
          `Te faltan ${formatCents(deliveryAmountRemainingCents ?? 0)}.`;
    }
    if (order.fulfillment === "delivery" && !order.address.trim()) {
      nextErrors.address = "Ingresá la dirección para el delivery.";
    }
    if (!order.paymentMethod) {
      nextErrors.paymentMethod = "Elegí un medio de pago.";
    } else if (order.paymentMethod === "Transferencia" && surchargePercentage === null) {
      nextErrors.paymentMethod =
        "El recargo de transferencia no está publicado. Pedí que actualicen el catálogo.";
    }
    setErrors(nextErrors);
    const isValid = Object.keys(nextErrors).length === 0;
    setValidated(isValid);
    if (isValid) {
      setCheckoutStep("confirm");
      requestAnimationFrame(() => {
        document.getElementById("pedido")?.scrollTo({
          top: 0,
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "instant"
            : "smooth",
        });
      });
    }
  };

  const changeCheckoutStep = (step: "cart" | "details" | "confirm") => {
    setCheckoutStep(step);
    requestAnimationFrame(() => {
      document.getElementById("pedido")?.scrollTo({
        top: 0,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
    });
  };

  const closeCheckout = () => {
    setCheckoutStep("cart");
    onClose();
  };

  const navigateFromCheckout = (targetId: string) => {
    closeCheckout();
    requestAnimationFrame(() => {
      document.getElementById(targetId)?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
    });
  };

  const returnToMenu = () => navigateFromCheckout("menu");

  if (!isOpen) return null;

  return (
    <section
      className={`order-section checkout-fullscreen ${checkoutStyles.scope}${checkoutStep === "cart" ? " checkout-cart-step" : ""}`}
      id="pedido"
      aria-labelledby="order-title"
    >
      <div className="checkout-topbar">
        <div className="checkout-topbar-inner">
          <a
            className="brand checkout-brand"
            href="#inicio"
            aria-label="PIZZA FIORI, inicio"
            onClick={(event) => {
              event.preventDefault();
              navigateFromCheckout("inicio");
            }}
          >
            <img className="brand-logo" src="/logo.png" alt="" />
            <span className="brand-name">
              <span className="brand-pizza">PIZZA</span>{" "}
              <strong className="brand-fiori">FIORI</strong>
            </span>
          </a>
          <button className="checkout-exit" type="button" onClick={returnToMenu}>
            <ArrowLeft size={17} aria-hidden="true" />
            Volver al menú
          </button>
        </div>
      </div>
      <div className="section-heading order-heading">
        <div>
          <span className="eyebrow">
            {checkoutStep === "cart"
              ? "PASO 1 DE 3"
              : checkoutStep === "details"
                ? "PASO 2 DE 3"
                : "PASO 3 DE 3"}
          </span>
          <h2 id="order-title">
            {checkoutStep === "cart"
              ? "Tu pedido"
              : checkoutStep === "details"
                ? "Datos de entrega"
                : "Confirmación"}
          </h2>
        </div>
        {checkoutStep === "cart" && (
          <button
            className="clear-cart-button"
            type="button"
            onClick={clearCart}
          >
            <Trash2 size={15} aria-hidden="true" />
            Vaciar carrito
          </button>
        )}
      </div>

      {resolvedCart.length === 0 ? (
        <div className="empty-cart">
          <span className="state-icon">
            <ShoppingBag size={23} aria-hidden="true" />
          </span>
          <h3>Tu pedido está vacío</h3>
          <p>Agrega un producto del menú para empezar.</p>
          <a
            className="text-link"
            href="#menu"
            onClick={(event) => {
              event.preventDefault();
              returnToMenu();
            }}
          >
            Volver al menú
          </a>
        </div>
      ) : (
        <>
          <nav
            className={`checkout-steps${checkoutStep === "cart" ? " checkout-stepper-cart" : ""}`}
            aria-label="Pasos del pedido"
          >
            <div
              className={`checkout-step${checkoutStep === "cart" ? " active" : " complete"}`}
              aria-current={checkoutStep === "cart" ? "step" : undefined}
            >
              <span>{checkoutStep !== "cart" ? <Check size={15} aria-hidden="true" /> : "1"}</span>
              <strong>Carrito</strong>
            </div>
            <div className="checkout-step-divider" aria-hidden="true" />
            <div
              className={`checkout-step${checkoutStep === "details" ? " active" : checkoutStep === "confirm" ? " complete" : ""}`}
              aria-current={checkoutStep === "details" ? "step" : undefined}
            >
              <span>{checkoutStep === "confirm" ? <Check size={15} aria-hidden="true" /> : "2"}</span>
              <strong>Entrega y pago</strong>
            </div>
            <div className="checkout-step-divider" aria-hidden="true" />
            <div
              className={`checkout-step${checkoutStep === "confirm" ? " active" : ""}`}
              aria-current={checkoutStep === "confirm" ? "step" : undefined}
            >
              <span>3</span>
              <strong>Confirmación</strong>
            </div>
          </nav>

          {checkoutStep === "cart" ? (
            <div className="cart-stage">
              <div className="cart-card">
                <ul className="cart-list">
                  {resolvedCart.map((item) => {
                    const title =
                      item.type === "product"
                        ? item.product.nombre
                        : item.type === "halfPizza"
                          ? "Pizza mitad/mitad"
                          : item.offer.nombre;
                    return (
                      <li
                        className={`cart-row${item.type === "product" ? " cart-row-product" : ""}`}
                        key={item.key}
                      >
                        {item.type === "product" && (
                          <img
                            className="cart-row-image"
                            src={item.product.imagen_url || PLACEHOLDER_IMAGE}
                            alt=""
                            onError={(event) => {
                              event.currentTarget.src = PLACEHOLDER_IMAGE;
                            }}
                          />
                        )}
                        <div className="cart-row-main">
                          <h4>{title}</h4>
                          <strong className="cart-row-price">
                            {formatCents(item.subtotalCents)}
                          </strong>
                          <div className="cart-row-detail">
                            {item.type === "product" ? (
                              <p>{formatProductPresentation(item.presentation)}</p>
                            ) : item.type === "halfPizza" ? (
                              <p>
                                {item.leftProduct.nombre.replace(/^Pizza\s+/i, "")} /{" "}
                                {item.rightProduct.nombre.replace(/^Pizza\s+/i, "")}
                              </p>
                            ) : (
                              <ul
                                className="cart-offer-selections"
                                id={`cart-offer-selections-${item.key}`}
                              >
                                {item.selections
                                  .slice(
                                    0,
                                    item.selections.length > 4 &&
                                      !expandedOfferSelections.has(item.key)
                                      ? 3
                                      : undefined,
                                  )
                                  .map((selection, index) => (
                                    <li key={`${selection.productId}-${index}`}>
                                      {formatOfferSelection(selection)}
                                    </li>
                                  ))}
                                {item.selections.length > 4 && (
                                  <li>
                                    <button
                                      className="cart-selections-toggle"
                                      type="button"
                                      aria-expanded={expandedOfferSelections.has(item.key)}
                                      aria-controls={`cart-offer-selections-${item.key}`}
                                      onClick={() => {
                                        setExpandedOfferSelections((current) => {
                                          const next = new Set(current);
                                          if (next.has(item.key)) {
                                            next.delete(item.key);
                                          } else {
                                            next.add(item.key);
                                          }
                                          return next;
                                        });
                                      }}
                                    >
                                      {expandedOfferSelections.has(item.key)
                                        ? "Mostrar menos"
                                        : `+ ${item.selections.length - 3} más`}
                                    </button>
                                  </li>
                                )}
                              </ul>
                            )}
                          </div>
                          <div
                            className="cart-qty"
                            role="group"
                            aria-label={`Cantidad de ${title}`}
                          >
                            <button
                              type="button"
                              className={`cart-qty-button${item.count === 1 ? " is-remove" : ""}`}
                              aria-label={
                                item.count === 1
                                  ? `Eliminar ${title} del pedido`
                                  : `Quitar una unidad de ${title}`
                              }
                              onClick={() =>
                                item.count === 1 ? removeItem(item) : updateCount(item, -1)
                              }
                            >
                              {item.count === 1 ? (
                                <Trash2 size={16} aria-hidden="true" />
                              ) : (
                                <Minus size={16} aria-hidden="true" />
                              )}
                            </button>
                            <span aria-live="polite">{item.count}</span>
                            <button
                              type="button"
                              className="cart-qty-button"
                              aria-label={`Agregar una unidad de ${title}`}
                              onClick={() => updateCount(item, 1)}
                            >
                              <Plus size={16} aria-hidden="true" />
                            </button>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
                <div className="form-field cart-food-notes">
                  <label htmlFor="food-notes">
                    Observaciones{" "}
                    <span className="optional-label">Opcional</span>
                  </label>
                  <textarea
                    id="food-notes"
                    rows={3}
                    value={order.foodNotes}
                    onChange={(event) => updateField("foodNotes", event.target.value)}
                    placeholder="Extras, sustituciones o detalles de preparación"
                  />
                </div>
              </div>
              <div className="cart-stage-actions">
                <a
                  className="back-to-menu"
                  href="#menu"
                  onClick={(event) => {
                    event.preventDefault();
                    returnToMenu();
                  }}
                >
                  <ArrowLeft size={16} aria-hidden="true" />
                  Seguir mirando
                </a>
                <div className="cart-action-total">
                  <span>Total estimado</span>
                  <strong>{formatCents(totalCents)}</strong>
                </div>
                <button
                  className="continue-button"
                  type="button"
                  onClick={() => changeCheckoutStep("details")}
                >
                  Continuar
                  <ArrowRight size={17} aria-hidden="true" />
                </button>
              </div>
            </div>
          ) : checkoutStep === "details" ? (
            <div className="details-stage">
              <form className="order-form" onSubmit={validateOrder} noValidate>
            <div className="form-field">
              <label htmlFor="customer-name">Tu nombre <span>*</span></label>
              <input
                id="customer-name"
                autoComplete="name"
                value={order.name}
                onChange={(event) => updateField("name", event.target.value)}
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? "customer-name-error" : undefined}
                placeholder="¿Cómo te llamás?"
              />
              {errors.name && <span className="field-error" id="customer-name-error">{errors.name}</span>}
            </div>

            <fieldset className="form-field fulfillment-field">
              <legend>¿Cómo lo recibís? <span>*</span></legend>
              <div className="fulfillment-options">
                <label
                  className={`${order.fulfillment === "delivery" ? "selected" : ""}${!isDeliveryEligible ? " disabled" : ""}`}
                >
                  <input
                    type="radio"
                    name="fulfillment"
                    value="delivery"
                    checked={order.fulfillment === "delivery"}
                    disabled={!isDeliveryEligible}
                    onChange={() => updateField("fulfillment", "delivery")}
                  />
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="m18.16 14.12-2.927-8.447A1 1 0 0 0 14.288 5H13" />
                    <path d="M19 10a7 7 0 0 0-6.928 6" />
                    <path d="M2 10h5.5a3 3 0 0 1 2.747 1.795l1.669 3.803A1 1 0 0 1 11.01 17H8" />
                    <circle cx="19" cy="17" r="3" />
                    <circle cx="5" cy="17" r="3" />
                  </svg>
                  Delivery
                </label>
                <label className={order.fulfillment === "pickup" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="fulfillment"
                    value="pickup"
                    checked={order.fulfillment === "pickup"}
                    onChange={() => updateField("fulfillment", "pickup")}
                  />
                  <Store size={18} aria-hidden="true" />
                  Retiro
                </label>
              </div>
              <p className="fulfillment-note" role="status">
                {deliveryMinimumCents === null
                  ? "El mínimo de delivery todavía no está publicado. Por ahora podés elegir Retiro."
                  : isDeliveryEligible
                    ? `Delivery gratis desde ${formatCents(deliveryMinimumCents)}.`
                    : `Delivery gratis desde ${formatCents(deliveryMinimumCents)}. Te faltan ${formatCents(deliveryAmountRemainingCents ?? 0)} para habilitarlo.`}
              </p>
              {errors.fulfillment && (
                <span className="field-error" id="fulfillment-error">
                  {errors.fulfillment}
                </span>
              )}
            </fieldset>

            {order.fulfillment === "delivery" && (
              <div className="form-field">
                <label htmlFor="delivery-address">
                  Dirección <span>*</span>
                </label>
                <div className="input-with-icon">
                  <MapPin size={17} aria-hidden="true" />
                  <input
                    id="delivery-address"
                    autoComplete="street-address"
                    value={order.address}
                    onChange={(event) => updateField("address", event.target.value)}
                    aria-invalid={Boolean(errors.address)}
                    aria-describedby={errors.address ? "delivery-address-error" : undefined}
                    placeholder="Calle, número y referencias"
                  />
                </div>
                {errors.address && (
                  <span className="field-error" id="delivery-address-error">{errors.address}</span>
                )}
              </div>
            )}

            <div className="form-field">
              <label htmlFor="payment-method">
                Medio de pago <span>*</span>
              </label>
              <div className="input-with-icon">
                <CreditCard size={17} aria-hidden="true" />
                <select
                  id="payment-method"
                  value={order.paymentMethod}
                  onChange={(event) => updateField("paymentMethod", event.target.value)}
                  aria-invalid={Boolean(errors.paymentMethod)}
                  aria-describedby={errors.paymentMethod ? "payment-method-error" : undefined}
                >
                  <option value="">Elegí un medio de pago</option>
                  {PAYMENT_METHODS.map((method) => (
                    <option key={method} value={method}>
                      {method === "Transferencia" && surchargePercentage !== null
                        ? `${method} (+${formatPercentage(surchargePercentage)}%)`
                        : method}
                    </option>
                  ))}
                </select>
              </div>
              {order.paymentMethod === "Transferencia" &&
                surchargePercentage !== null && (
                  <p className="payment-surcharge-note">
                    Se sumará un recargo del {formatPercentage(surchargePercentage)}%.
                  </p>
                )}
              {errors.paymentMethod && (
                <span className="field-error" id="payment-method-error" role="alert">
                  {errors.paymentMethod}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="order-notes">
                Observaciones{" "}
                <span className="optional-label">Opcional</span>
              </label>
              <textarea
                id="order-notes"
                rows={3}
                value={order.notes}
                onChange={(event) => updateField("notes", event.target.value)}
                placeholder="Referencias para encontrar el domicilio u otra indicación"
              />
            </div>

            <div className="details-navigation">
              <button
                className="back-to-cart-button"
                type="button"
                onClick={() => changeCheckoutStep("cart")}
              >
                <ArrowLeft size={16} aria-hidden="true" />
                Volver
              </button>
              <button className="continue-button" type="submit">
                Revisar pedido <ArrowRight size={17} aria-hidden="true" />
              </button>
            </div>
            <p className="form-footnote">
              No se solicitan datos de tarjeta ni se realizan pagos en línea.
            </p>
              </form>
            </div>
          ) : (
            <div className="details-stage">
              <section className="order-review" aria-label="Confirmación del pedido">
                <div className="review-products-wrap">
                  <ul className="review-products" id="order-review-products">
                    {(showAllReviewProducts
                      ? resolvedCart
                      : resolvedCart.slice(0, 3)
                    ).map((item) => (
                      <li key={item.key}>
                        <span>
                          {item.type === "product"
                            ? `${item.count} x ${item.product.nombre}`
                            : item.type === "halfPizza"
                              ? `${item.count} x Pizza mitad/mitad`
                              : `${item.count} x Promo: ${item.offer.nombre}`}
                          {item.type === "product" ? (
                            <small>{formatProductPresentation(item.presentation)}</small>
                          ) : item.type === "halfPizza" ? (
                            <small>
                              {item.leftProduct.nombre} / {item.rightProduct.nombre}
                            </small>
                          ) : (
                            <ul
                              className="cart-offer-selections review-offer-selections"
                              id={`review-offer-selections-${item.key}`}
                            >
                              {item.selections
                                .slice(
                                  0,
                                  item.selections.length > 4 &&
                                    !expandedOfferSelections.has(item.key)
                                    ? 3
                                    : undefined,
                                )
                                .map((selection, index) => (
                                  <li key={`${selection.productId}-${index}`}>
                                    {formatOfferSelection(selection)}
                                  </li>
                                ))}
                              {item.selections.length > 4 && (
                                <li>
                                  <button
                                    className="cart-selections-toggle"
                                    type="button"
                                    aria-expanded={expandedOfferSelections.has(item.key)}
                                    aria-controls={`review-offer-selections-${item.key}`}
                                    onClick={() => {
                                      setExpandedOfferSelections((current) => {
                                        const next = new Set(current);
                                        if (next.has(item.key)) {
                                          next.delete(item.key);
                                        } else {
                                          next.add(item.key);
                                        }
                                        return next;
                                      });
                                    }}
                                  >
                                    {expandedOfferSelections.has(item.key)
                                      ? "Mostrar menos"
                                      : `+ ${item.selections.length - 3} más`}
                                  </button>
                                </li>
                              )}
                            </ul>
                          )}
                        </span>
                        <strong>{formatCents(item.subtotalCents)}</strong>
                      </li>
                    ))}
                  </ul>
                  {resolvedCart.length > 3 && (
                    <button
                      className="review-details-toggle review-products-toggle"
                      type="button"
                      aria-expanded={showAllReviewProducts}
                      aria-controls="order-review-products"
                      onClick={() =>
                        setShowAllReviewProducts((expanded) => !expanded)
                      }
                    >
                      {showAllReviewProducts
                        ? "Ver menos"
                        : `Ver ${resolvedCart.length - 3} más`}
                    </button>
                  )}
                </div>
                <div className="review-details-wrap">
                  <button
                    className="review-details-edit"
                    type="button"
                    aria-label="Editar datos del pedido"
                    title="Editar datos del pedido"
                    onClick={() => {
                      setValidated(false);
                      changeCheckoutStep("details");
                    }}
                  >
                    <SquarePen size={17} aria-hidden="true" />
                  </button>
                  <dl className="review-details">
                    <div>
                      <dt>Nombre</dt>
                      <dd>{order.name.trim()}</dd>
                    </div>
                    <div>
                      <dt>Medio de pago</dt>
                      <dd className="review-details-payment">
                        <span>{order.paymentMethod}</span>
                        {!showAllReviewDetails && (
                          <button
                            className="review-details-toggle"
                            type="button"
                            aria-expanded={false}
                            onClick={() => setShowAllReviewDetails(true)}
                          >
                            Ver más
                          </button>
                        )}
                      </dd>
                    </div>
                    {showAllReviewDetails && (
                      <>
                        <div>
                          <dt>Entrega</dt>
                          <dd>
                            {order.fulfillment === "delivery"
                              ? `Delivery · ${order.address.trim()}`
                              : "Retiro por el local"}
                          </dd>
                        </div>
                        <div>
                          <dt>Observaciones de la comida</dt>
                          <dd>{order.foodNotes.trim() || "Sin indicaciones"}</dd>
                        </div>
                        <div>
                          <dt>Observaciones de entrega o pago</dt>
                          <dd>{order.notes.trim() || "Sin indicaciones"}</dd>
                        </div>
                      </>
                    )}
                  </dl>
                  {showAllReviewDetails && (
                    <button
                      className="review-details-toggle review-details-collapse"
                      type="button"
                      aria-expanded={true}
                      onClick={() => setShowAllReviewDetails(false)}
                    >
                      Ver menos
                    </button>
                  )}
                </div>
              <div className="order-review-totals">
                <div><span>Subtotal</span><strong>{formatCents(totalCents)}</strong></div>
                {isTransferPayment && surchargePercentage !== null && (
                  <div>
                    <span>
                      Recargo por transferencia ({formatPercentage(surchargePercentage)}%)
                    </span>
                    <strong>{formatCents(surchargeCents)}</strong>
                  </div>
                )}
                {order.fulfillment === "delivery" && (
                  <div><span>Envío</span><strong>Gratis</strong></div>
                )}
                <div className="review-total">
                  <span>
                    Total estimado
                  </span>
                  <strong>{formatCents(estimatedTotalCents)}</strong>
                </div>
              </div>
              {whatsappUrl ? (
                <a
                  className="whatsapp-button"
                  href={whatsappUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => {
                    setCart([]);
                    setValidated(false);
                    navigateFromCheckout("inicio");
                  }}
                >
                  <WhatsAppIcon />
                  Enviar pedido por WhatsApp
                </a>
              ) : (
                <p className="whatsapp-config-error" role="alert">
                  Falta configurar un número de WhatsApp válido en{" "}
                  <code>VITE_WHATSAPP_PHONE</code> para habilitar el envío.
                </p>
              )}
              <button
                className="back-to-cart-button"
                type="button"
                onClick={() => changeCheckoutStep("cart")}
              >
                <ArrowLeft size={16} aria-hidden="true" />
                Volver al carrito
              </button>
              </section>
            </div>
          )}
        </>
      )}
    </section>
  );
}

function OfferCard({
  offer,
  catalog,
  onAddOffer,
}: {
  offer: CatalogOffer;
  catalog: PublicCatalog;
  onAddOffer: (offer: CatalogOffer, selections: SelectedOfferProduct[]) => void;
}) {
  const [isConfiguring, setIsConfiguring] = useState(false);
  const configDialogRef = useRef<HTMLDialogElement>(null);
  const [categorySelections, setCategorySelections] = useState<
    Map<number, Map<number, number>>
  >(() => new Map());
  const [optionSelections, setOptionSelections] = useState<Map<number, number>>(
    () => new Map(),
  );
  const productNames = new Map(
    catalog.productos.map((product) => [product.id, product.nombre]),
  );
  const categoryNames = new Map(
    catalog.categorias.map((category) => [category.id, category.nombre]),
  );
  useEffect(() => {
    const dialog = configDialogRef.current;
    if (!dialog) return;
    if (isConfiguring && !dialog.open) dialog.showModal();
    if (!isConfiguring && dialog.open) dialog.close();
  }, [isConfiguring]);

  const configurableItems = offer.items
    .map((item, index) => ({ item, index, type: getOfferItemType(item) }))
    .filter(({ type }) => type !== "fixed");
  const hasRequiredSelections = configurableItems.every(({ item, index, type }) => {
    if (type === "category") {
      const selections = categorySelections.get(index);
      const selectedTotal = selections
        ? Array.from(selections.values()).reduce((sum, quantity) => sum + quantity, 0)
        : 0;
      return Math.abs(selectedTotal - Number(item.cantidad)) < 1e-9;
    }
    return optionSelections.has(index);
  });

  const handleCategoryQuantity = (
    itemIndex: number,
    productId: number,
    adjustment: number,
    requiredQuantity: number,
  ) => {
    setCategorySelections((current) => {
      const currentSelections = current.get(itemIndex) ?? new Map<number, number>();
      const currentQuantity = currentSelections.get(productId) ?? 0;
      const nextQuantity = Math.max(0, currentQuantity + adjustment);
      const selectedTotal = Array.from(currentSelections.values()).reduce(
        (sum, quantity) => sum + quantity,
        0,
      );
      if (selectedTotal - currentQuantity + nextQuantity > requiredQuantity) {
        return current;
      }

      const nextSelections = new Map(currentSelections);
      if (nextQuantity === 0) nextSelections.delete(productId);
      else nextSelections.set(productId, nextQuantity);
      const next = new Map(current);
      next.set(itemIndex, nextSelections);
      return next;
    });
  };

  const selectionsForCart = (): SelectedOfferProduct[] => {
    const selected: SelectedOfferProduct[] = [];
    offer.items.forEach((item, index) => {
      const type = getOfferItemType(item);
      if (type === "fixed") {
        const productId = item.producto_ids[0];
        const productName = productNames.get(productId);
        if (productName) {
          selected.push({
            productId,
            productName,
            quantity: Number(item.cantidad),
          });
        }
      } else if (type === "category") {
        categorySelections.get(index)?.forEach((quantity, productId) => {
          const productName = productNames.get(productId);
          if (productName) selected.push({ productId, productName, quantity });
        });
      } else {
        const productId = optionSelections.get(index);
        const productName = productId === undefined ? undefined : productNames.get(productId);
        if (productId !== undefined && productName) {
          selected.push({
            productId,
            productName,
            quantity: Number(item.cantidad),
          });
        }
      }
    });
    return selected;
  };

  const confirmOffer = () => {
    const selections = selectionsForCart();
    if (hasRequiredSelections && selections.length > 0) {
      onAddOffer(offer, selections);
      setIsConfiguring(false);
      setCategorySelections(new Map());
      setOptionSelections(new Map());
    }
  };

  return (
    <article className={`offer-card ${offerStyles.scope}`}>
      <Flame
        className="offer-corner-flame"
        size={32}
        aria-hidden="true"
      />
      <h3>{offer.nombre}</h3>
      {offer.items.length > 0 && (
        <ul
          className={`offer-items${offer.items.length > 3 ? " offer-items--many" : ""}`}
        >
          {offer.items.map((item, index) => {
            const type = getOfferItemType(item);
            const categoryDescription = type === "category"
              ? formatCategoryOfferDescription(
                  Number(item.cantidad),
                  categoryNames.get(item.categoria_id ?? -1) ?? "la categoría",
                )
              : null;
            const itemDescription = type === "category"
              ? null
              : type === "options"
                ? `Elegí entre ${item.producto_ids
                    .map((productId) => productNames.get(productId))
                    .filter((name): name is string => Boolean(name))
                    .join(" o ")}`
                : productNames.get(item.producto_ids[0]) ?? "Producto";
            return (
              <li key={`${offer.id}-${index}`}>
                {type !== "category" && (
                  <>
                    <span>{formatOfferQuantity(Number(item.cantidad))} ×</span>{" "}
                  </>
                )}
                {categoryDescription ? (
                  <>
                    <span>{categoryDescription.quantity}</span>
                    {categoryDescription.unit && ` ${categoryDescription.unit}`}
                    {" de "}
                    {categoryDescription.categoryName}
                    {" a elección"}
                  </>
                ) : (
                  itemDescription
                )}
              </li>
            );
          })}
        </ul>
      )}
      <div className="offer-footer">
        <strong className="offer-price">{formatPrice(offer.precio)}</strong>
        <button
          className="action-button offer-card-add-button"
          type="button"
          onClick={() => {
            if (configurableItems.length > 0) {
              setIsConfiguring(true);
              return;
            }
            const selections = selectionsForCart();
            if (selections.length > 0) onAddOffer(offer, selections);
          }}
        >
          <Plus size={15} aria-hidden="true" />
          Agregar promo
        </button>
      </div>
      {configurableItems.length > 0 && (
        <dialog
          ref={configDialogRef}
          className="offer-config-dialog"
          aria-labelledby={`offer-dialog-title-${offer.id}`}
          onClose={() => setIsConfiguring(false)}
          onCancel={(event) => {
            event.preventDefault();
            setIsConfiguring(false);
          }}
          onClick={(event) => {
            if (event.target === event.currentTarget) setIsConfiguring(false);
          }}
        >
          <div className="offer-dialog-header">
            <button
              className="offer-dialog-back"
              type="button"
              aria-label="Volver a las promociones"
              onClick={() => setIsConfiguring(false)}
            >
              <ArrowLeft size={17} aria-hidden="true" />
            </button>
            <div className="offer-dialog-title">
              <span className="eyebrow">ARMA TU PROMO</span>
              <h2 id={`offer-dialog-title-${offer.id}`}>{offer.nombre}</h2>
            </div>
          </div>
          <div className="offer-config">
            {configurableItems.map(({ item, index, type }) => {
              if (type === "category") {
                const categoryProducts = catalog.productos.filter(
                  (product) => product.categoria_id === item.categoria_id,
                );
                const selections = categorySelections.get(index);
                const selectedTotal = selections
                  ? Array.from(selections.values()).reduce((sum, quantity) => sum + quantity, 0)
                  : 0;
                const requiredQuantity = Number(item.cantidad);
                const progress = requiredQuantity > 0
                  ? Math.min(100, (selectedTotal / requiredQuantity) * 100)
                  : 0;
                const categoryName =
                  categoryNames.get(item.categoria_id ?? -1) ?? "la categoría";
                return (
                  <fieldset className="offer-config-group" key={index}>
                    <legend>
                      <span>{categoryName}</span>
                      <small className="offer-selection-count">
                        <strong>{selectedTotal}</strong> de{" "}
                        {formatOfferQuantity(requiredQuantity)}
                      </small>
                    </legend>
                    <div
                      className="offer-selection-progress"
                      role="progressbar"
                      aria-label={`Cantidad seleccionada de ${categoryName}`}
                      aria-valuemin={0}
                      aria-valuemax={requiredQuantity}
                      aria-valuenow={selectedTotal}
                    >
                      <span style={{ width: `${progress}%` }} />
                    </div>
                    {categoryProducts.map((product) => {
                      const quantity = selections?.get(product.id) ?? 0;
                      return (
                        <div
                          className={`offer-choice-row${quantity > 0 ? " has-quantity" : ""}`}
                          key={product.id}
                        >
                          <span className="offer-choice-product">{product.nombre}</span>
                          <div className="offer-choice-quantity">
                            <button
                              type="button"
                              aria-label={`Quitar ${product.nombre} de la promo`}
                              disabled={quantity === 0}
                              onClick={() => handleCategoryQuantity(index, product.id, -1, Number(item.cantidad))}
                            >
                              <Minus size={14} aria-hidden="true" />
                            </button>
                            <span aria-live="polite">{quantity}</span>
                            <button
                              type="button"
                              aria-label={`Agregar ${product.nombre} a la promo`}
                              disabled={selectedTotal >= Number(item.cantidad)}
                              onClick={() => handleCategoryQuantity(index, product.id, 1, Number(item.cantidad))}
                            >
                              <Plus size={14} aria-hidden="true" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </fieldset>
                );
              }

              const optionProducts = item.producto_ids
                .map((productId) => catalog.productos.find((product) => product.id === productId))
                .filter((product): product is CatalogProduct => Boolean(product));
              return (
                <fieldset className="offer-config-group" key={index}>
                  <legend>
                    Elegí una opción
                  </legend>
                  {optionProducts.map((product) => (
                    <label className="offer-option-choice" key={product.id}>
                      <input
                        type="radio"
                        name={`offer-${offer.id}-item-${index}`}
                        value={product.id}
                        checked={optionSelections.get(index) === product.id}
                        onChange={() => setOptionSelections((current) => {
                          const next = new Map(current);
                          next.set(index, product.id);
                          return next;
                        })}
                      />
                      <span>{product.nombre}</span>
                    </label>
                  ))}
                </fieldset>
              );
            })}
          </div>
          <div className="offer-dialog-footer">
            <strong>{formatPrice(offer.precio)}</strong>
            <div className="offer-config-actions">
              <button
                className="action-button offer-config-cancel-button"
                type="button"
                onClick={() => setIsConfiguring(false)}
              >
                Cancelar
              </button>
              <button
                className="action-button offer-config-confirm-button"
                type="button"
                disabled={!hasRequiredSelections}
                onClick={confirmOffer}
              >
                <Plus size={15} aria-hidden="true" />
                Agregar promo
              </button>
            </div>
          </div>
        </dialog>
      )}
    </article>
  );
}

function LoadingState() {
  return (
    <section
      className={`menu-section ${menuStyles.scope} ${stateStyles.loadingScope}`}
      aria-label="Cargando menú"
      aria-busy="true"
    >
      <div className="section-heading">
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-caption" />
      </div>
      <div className="product-grid">
        {Array.from({ length: 6 }, (_, index) => (
          <div className="skeleton-card" key={index}>
            <div className="skeleton skeleton-image" />
            <div className="skeleton-body">
              <div className="skeleton skeleton-line title-line" />
              <div className="skeleton skeleton-line short" />
              <div className="skeleton-presentation">
                <div className="skeleton skeleton-line price-line" />
                <div className="skeleton skeleton-action" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [catalog, setCatalog] = useState<PublicCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [order, setOrder] = useState<OrderForm>({
    name: "",
    fulfillment: "",
    address: "",
    paymentMethod: "",
    foodNotes: "",
    notes: "",
  });
  const productsByCategory = useMemo(() => {
    if (!catalog) return new Map<number, CatalogProduct[]>();
    return catalog.productos.reduce((grouped, product) => {
      const products = grouped.get(product.categoria_id) ?? [];
      products.push(product);
      grouped.set(product.categoria_id, products);
      return grouped;
    }, new Map<number, CatalogProduct[]>());
  }, [catalog]);
  const visibleCategories = catalog?.categorias.filter(
    (category) =>
      productsByCategory.has(category.id) &&
      !HIDDEN_CATEGORY_NAMES.has(category.nombre.trim().toLocaleLowerCase("es-AR")),
  ) ?? [];
  const visibleCategoryIds = new Set(visibleCategories.map((category) => category.id));
  const halfPizzaProducts = catalog?.productos.flatMap((product) => {
    if (!visibleCategoryIds.has(product.categoria_id) || !catalog) return [];
    if (!isPizzaProduct(product, catalog.categorias)) return [];
    const unitPriceCents = getProductUnitPriceCents(product);
    return unitPriceCents === null
      ? []
      : [{ product, unitPriceCents }];
  }) ?? [];
  const halfPizzaCategoryId =
    halfPizzaProducts.length < 2
      ? undefined
      : visibleCategories.find(
          (category) => category.nombre.trim().toLocaleLowerCase("es-AR") === "pizzas",
        )?.id ??
        visibleCategories.find((category) =>
          halfPizzaProducts.some(({ product }) => product.categoria_id === category.id),
        )?.id;

  useEffect(() => {
    document.documentElement.dataset.theme = "dark";
    document.documentElement.style.colorScheme = "dark";
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      "#0d0d0d",
    );
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadCatalog() {
      setIsLoading(true);
      setError(null);
      try {
        const loadedCatalog = await fetchPublicCatalog(POINTER_URL);
        if (!cancelled) setCatalog(loadedCatalog);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "No se pudo cargar el menú. Intentá nuevamente.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void loadCatalog();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const hasProducts = visibleCategories.length > 0 || Boolean(catalog?.ofertas.length);
  const cartItemCount = cart.reduce((count, item) => count + item.count, 0);
  const cartTotalCents = cart.reduce((total, item) => {
    if (!catalog) return total;
    if (item.type === "offer") {
      const offer = catalog.ofertas.find((entry) => entry.id === item.offerId);
      return offer
        ? total + Math.round(Number(offer.precio) * 100) * item.count
        : total;
    }
    if (item.type === "halfPizza") {
      const leftProduct = catalog.productos.find(
        (entry) => entry.id === item.leftProductId,
      );
      const rightProduct = catalog.productos.find(
        (entry) => entry.id === item.rightProductId,
      );
      const leftPrice = leftProduct ? getProductUnitPriceCents(leftProduct) : null;
      const rightPrice = rightProduct ? getProductUnitPriceCents(rightProduct) : null;
      return leftPrice !== null && rightPrice !== null
        ? total + Math.max(leftPrice, rightPrice) * item.count
        : total;
    }
    const product = catalog.productos.find((entry) => entry.id === item.productId);
    const price = product?.precios.find(
      (entry) => entry.cantidad === item.presentation,
    );
    return price ? total + Math.round(Number(price.precio) * 100) * item.count : total;
  }, 0);

  const adjustProductCount = (
    product: CatalogProduct,
    presentation: string,
    adjustment: number,
  ) => {
    setCart((currentCart) => {
      const existing = currentCart.find(
        (item) =>
          item.type === "product" &&
          item.productId === product.id &&
          item.presentation === presentation,
      );
      if (!existing) {
        return adjustment > 0
          ? [...currentCart, {
              type: "product",
              key: crypto.randomUUID(),
              productId: product.id,
              presentation,
              count: adjustment,
            }]
          : currentCart;
      }
      const count = existing.count + adjustment;
      return count > 0
        ? currentCart.map((item) =>
            item === existing ? { ...item, count } : item,
          )
        : currentCart.filter((item) => item !== existing);
    });
  };

  const addOfferToCart = (offer: CatalogOffer, selections: SelectedOfferProduct[]) => {
    setCart((currentCart) => [
      ...currentCart,
      {
        type: "offer",
        key: crypto.randomUUID(),
        offerId: offer.id,
        count: 1,
        selections,
      },
    ]);
  };

  const addHalfPizzaToCart = (
    leftProduct: CatalogProduct,
    rightProduct: CatalogProduct,
  ) => {
    setCart((currentCart) => [
      ...currentCart,
      {
        type: "halfPizza",
        key: crypto.randomUUID(),
        leftProductId: leftProduct.id,
        rightProductId: rightProduct.id,
        count: 1,
      },
    ]);
  };

  const goToCart = () => {
    setIsCheckoutOpen(true);
  };

  return (
    <div
      className={`site-shell ${appStyles.scope}${cartItemCount > 0 ? " has-cart" : ""}`}
    >
      <header className="site-header">
        <a className="brand" href="#inicio" aria-label="PIZZA FIORI, inicio">
          <img className="brand-logo" src="/logo.png" alt="" />
          <span className="brand-name">
            <span className="brand-pizza">PIZZA</span>{" "}
            <strong className="brand-fiori">FIORI</strong>
          </span>
        </a>
        <div className="header-actions">
          {/* Selector de tema deshabilitado temporalmente: la web queda solo en modo oscuro.
          <button
            className="theme-toggle"
            type="button"
            aria-label="Activar modo claro"
            title="Modo claro"
            onClick={() => setTheme("light")}
          >
            <Sun size={18} aria-hidden="true" />
          </button>
          */}
          <button className="header-cart" type="button" onClick={goToCart}>
            <ShoppingBag size={17} aria-hidden="true" />
            Pedido <span>{cartItemCount}</span>
          </button>
        </div>
      </header>

      <main id="inicio">
        <section className="hero">
          <div className="hero-content">
            <h1>
              Pedí algo rico.
              <br />
              <em>Compartilo.</em>
            </h1>
            <p>Elegí del menú y armá tu pedido por WhatsApp.</p>
            <a className="hero-cta" href="#menu">
              Ver menú <ArrowDown size={17} aria-hidden="true" />
            </a>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="hero-brand-seal">
              <div className="hero-seal-name">
                <span>PIZZA</span>
                <strong>FIORI</strong>
              </div>
              <span className="hero-seal-bottom">FRESCO · CASERO · FIORI</span>
            </div>
            <Sparkles className="hero-seal-spark spark-one" />
            <Sparkles className="hero-seal-spark spark-two" />
          </div>
        </section>

        <section className={`menu-section ${menuStyles.scope}`} id="menu">
          <div className="section-heading">
            <h2>Menú</h2>
          </div>

          {isLoading && <LoadingState />}

          {!isLoading && error && (
            <div
              className={`state-panel error-panel ${stateStyles.panelScope}`}
              role="alert"
            >
              <span className="state-icon">
                <AlertCircle size={24} aria-hidden="true" />
              </span>
              <h3>No pudimos cargar el menú</h3>
              <p>{error}</p>
              <button
                className="retry-button"
                type="button"
                onClick={() => setAttempt((value) => value + 1)}
              >
                <RefreshCw size={16} aria-hidden="true" />
                Reintentar
              </button>
            </div>
          )}

          {!isLoading && !error && !hasProducts && (
            <div className={`state-panel ${stateStyles.panelScope}`}>
              <span className="state-icon">
                <Leaf size={24} aria-hidden="true" />
              </span>
              <h3>Estamos preparando el menú</h3>
              <p>Volvé pronto para descubrir los sabores de Pizza Fiori.</p>
            </div>
          )}

          {!isLoading && !error && hasProducts && catalog && (
            <>
              <nav className="category-nav" aria-label="Categorías del menú">
                {catalog.ofertas.length > 0 && (
                  <a className="promos-nav-link" href="#promos">
                    <Flame className="promos-nav-flame" size={16} aria-hidden="true" />
                    Promos
                  </a>
                )}
                {visibleCategories.map((category) => (
                  <a key={category.id} href={`#categoria-${category.id}`}>
                    {category.nombre}
                  </a>
                ))}
              </nav>
              {catalog.ofertas.length > 0 && (
                <section
                  className="offers-section"
                  id="promos"
                  aria-labelledby="offers-title"
                >
                  <div className="category-heading offers-heading">
                    <Flame
                      className="category-flower category-flame"
                      aria-hidden="true"
                    />
                    <h3 id="offers-title">Promos para compartir</h3>
                  </div>
                  <div className="offers-grid">
                    {catalog.ofertas.map((offer) => (
                      <OfferCard
                        key={offer.id}
                        offer={offer}
                        catalog={catalog}
                        onAddOffer={addOfferToCart}
                      />
                    ))}
                  </div>
                </section>
              )}
              <div className="category-list">
                {visibleCategories.map((category) => (
                  <section
                    className="category-section"
                    id={`categoria-${category.id}`}
                    key={category.id}
                  >
                    <div className="category-heading">
                      <Sparkles
                        className="category-flower category-sparkle"
                        aria-hidden="true"
                      />
                      <h3>{category.nombre}</h3>
                      <span className="category-count">
                {productsByCategory.get(category.id)?.length ?? 0}{" "}
                {productsByCategory.get(category.id)?.length === 1
                  ? "opción"
                  : "opciones"}
                      </span>
                    </div>
                    <div className="product-grid">
                      {category.id === halfPizzaCategoryId && (
                        <PizzaHalfBuilder
                          products={halfPizzaProducts}
                          onAdd={addHalfPizzaToCart}
                        />
                      )}
                      {productsByCategory.get(category.id)?.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  cart={cart}
                  onAdjust={adjustProductCount}
                />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
              <p className="price-disclaimer">
                Precios sujetos a confirmación.
              </p>
            </>
          )}
        </section>

        {!isLoading && !error && catalog && hasProducts && (
          <CartAndCheckout
            catalog={catalog}
            cart={cart}
            setCart={setCart}
            order={order}
            setOrder={setOrder}
            isOpen={isCheckoutOpen}
            onClose={() => setIsCheckoutOpen(false)}
          />
        )}

        <section className="closing-note">
          <Sparkles className="closing-flower" aria-hidden="true" />
          <p>Hecho para compartir.</p>
          <Sparkles className="closing-flower" aria-hidden="true" />
        </section>
      </main>

      <footer className="site-footer">
        <a className="footer-brand" href="#inicio">
          <span className="brand-pizza">PIZZA</span>{" "}
          <strong className="brand-fiori">FIORI</strong>
        </a>
        <span>Pedidos por WhatsApp</span>
        <nav className="footer-socials" aria-label="Redes sociales y contacto">
          {GOOGLE_MAPS_URL && (
            <a
              href={GOOGLE_MAPS_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Ubicación de Pizza Fiori en Google Maps"
              title="Ubicación"
            >
              <MapPin aria-hidden="true" />
            </a>
          )}
          {INSTAGRAM_URL && (
            <a
              href={INSTAGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Instagram de Pizza Fiori"
              title="Instagram"
            >
              <Instagram aria-hidden="true" />
            </a>
          )}
          {FACEBOOK_URL && (
            <a
              href={FACEBOOK_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Facebook de Pizza Fiori"
              title="Facebook"
            >
              <Facebook aria-hidden="true" />
            </a>
          )}
          {WHATSAPP_URL && (
            <a
              href={WHATSAPP_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="WhatsApp de Pizza Fiori"
              title="WhatsApp"
            >
              <WhatsAppIcon />
            </a>
          )}
          {PHONE_NUMBER && (
            <a
              href={`tel:+${PHONE_NUMBER}`}
              aria-label="Llamar a Pizza Fiori"
              title="Teléfono"
            >
              <Phone aria-hidden="true" />
            </a>
          )}
        </nav>
      </footer>

      {isLoading && (
        <span className="sr-only" role="status">
          <LoaderCircle aria-hidden="true" /> Cargando catálogo
        </span>
      )}

      {cartItemCount > 0 && (
        <button className="sticky-cart" type="button" onClick={goToCart}>
          <span className="sticky-cart-icon">
            <ShoppingBag size={18} aria-hidden="true" />
            <span>{cartItemCount}</span>
          </span>
          <strong className="sticky-cart-price">{formatCents(cartTotalCents)}</strong>
          <ChevronRight className="sticky-cart-chevron" size={21} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}

export default App;

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Check,
  Clock3,
  CreditCard,
  Flame,
  Leaf,
  LoaderCircle,
  MapPin,
  MessageCircle,
  Moon,
  Minus,
  Plus,
  RefreshCw,
  ShoppingBag,
  Store,
  Sun,
  Trash2,
  Truck,
  X,
} from "lucide-react";
import {
  fetchPublicCatalog,
  type CatalogOffer,
  type CatalogProduct,
  type PublicCatalog,
} from "./catalog";

const POINTER_URL = import.meta.env.VITE_CATALOG_POINTER_URL ?? "";
const WHATSAPP_PHONE = import.meta.env.VITE_WHATSAPP_PHONE ?? "";
const HIDDEN_CATEGORY_NAMES = new Set(
  (import.meta.env.VITE_HIDDEN_CATEGORIES ?? "")
    .split(",")
    .map((name) => name.trim().toLocaleLowerCase("es-AR"))
    .filter(Boolean),
);
const PLACEHOLDER_IMAGE = "/logo.png";
const THEME_STORAGE_KEY = "pizza-fiori-theme";
type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return "dark";
}

const configuredPaymentMethods = (
  import.meta.env.VITE_ORDER_PAYMENT_METHODS || "Efectivo,Transferencia"
)
  .split(",")
  .map((method) => method.trim())
  .filter((method, index, methods) => method.length > 0 && methods.indexOf(method) === index);
const PAYMENT_METHODS = configuredPaymentMethods.length
  ? configuredPaymentMethods
  : ["Efectivo", "Transferencia"];

type CartItem = {
  type: "product";
  key: string;
  productId: number;
  presentation: string;
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

type ResolvedCartItem = ResolvedProductCartItem | ResolvedOfferCartItem;

const currencyFormatter = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

function formatCents(cents: number): string {
  return currencyFormatter.format(cents / 100);
}

function formatPrice(price: string): string {
  const numericPrice = Number(price);
  return Number.isFinite(numericPrice)
    ? formatCents(Math.round(numericPrice * 100))
    : "Consultar";
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

function formatPublishDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Catálogo actualizado";
  return new Intl.DateTimeFormat("es-AR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

function normalizeWhatsAppPhone(value: string): string | null {
  const digits = value.replace(/\D/g, "");
  return /^\d{8,15}$/.test(digits) ? digits : null;
}

function buildWhatsAppMessage(
  items: ResolvedCartItem[],
  order: OrderForm,
  totalCents: number,
): string {
  const productLines = items.flatMap((item) => {
    if (item.type === "product") {
      return [
        `- ${item.count} x ${item.product.nombre} (${formatProductPresentation(item.presentation)}) — ${formatCents(item.subtotalCents)}`,
      ];
    }
    return [
      `- ${item.count} x Promo: ${item.offer.nombre} — ${formatCents(item.subtotalCents)}`,
      ...item.selections.map((selection) => `  - ${formatOfferSelection(selection)}`),
    ];
  });
  const fulfillmentLabel = order.fulfillment === "delivery" ? "Delivery" : "Retiro por el local";
  const deliveryLines =
    order.fulfillment === "delivery"
      ? [`\u{1F4CD} *Dirección:* ${order.address.trim()}`]
      : [];

  return [
    "\u{1F355} *¡Hola, Pizza Fiori!* Quiero hacer este pedido:",
    "",
    "\u{1F6D2} *MI PEDIDO*",
    "",
    ...productLines,
    "",
    `\u{1F4B0} *Subtotal:* ${formatCents(totalCents)}`,
    "\u{1F6F5} *Envío:* A confirmar",
    `\u{1F4B5} *Total estimado:* ${formatCents(totalCents)}`,
    "",
    "*_Los importes y el envío quedan sujetos a confirmación del local._*",
    "",
    "\u{1F4CB} *DATOS DEL PEDIDO*",
    `\u{1F464} *Nombre:* ${order.name.trim()}`,
    `\u{1F3E0} *Entrega:* ${fulfillmentLabel}`,
    ...deliveryLines,
    `\u{1F4B3} *Pago:* ${order.paymentMethod}`,
    `\u{1F4DD} *Observaciones:* ${order.notes.trim() || "Sin observaciones"}`,
    "",
    "\u{1F64F} Quedo atento a la confirmación. ¡Muchas gracias!",
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
    (first, second) => Number(first.cantidad) - Number(second.cantidad),
  );

  return (
    <article className="product-card">
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
        {showPlaceholder && (
          <span className="image-note">
            <Leaf size={14} aria-hidden="true" />
            Hecho con cariño
          </span>
        )}
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
                    className="add-to-cart-button"
                    type="button"
                    onClick={() => onAdjust(product, price.cantidad, 1)}
                    title="Agregar al pedido"
                    aria-label={`Agregar ${product.nombre}, presentación ${formatProductPresentation(price.cantidad)}, ${formatPrice(price.precio)}`}
                  >
                    <Plus size={15} aria-hidden="true" />
                    Agregar
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
  const totalItems = resolvedCart.reduce((sum, item) => sum + item.count, 0);
  const whatsappMessage = validated
    ? buildWhatsAppMessage(resolvedCart, order, totalCents)
    : "";
  const encodedWhatsAppMessage = encodeURIComponent(whatsappMessage).replace(/\*/g, "%2A");
  const whatsappUrl = whatsappPhone
    ? `https://wa.me/${whatsappPhone}?text=${encodedWhatsAppMessage}`
    : null;

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

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
    if (order.fulfillment === "delivery" && !order.address.trim()) {
      nextErrors.address = "Ingresá la dirección para el delivery.";
    }
    if (!order.paymentMethod) {
      nextErrors.paymentMethod = "Elegí un medio de pago.";
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
      className="order-section checkout-fullscreen"
      id="pedido"
      aria-labelledby="order-title"
    >
      <div className="checkout-topbar">
        <div className="checkout-topbar-inner">
          <a
            className="checkout-brand"
            href="#inicio"
            onClick={(event) => {
              event.preventDefault();
              navigateFromCheckout("inicio");
            }}
          >
            <span className="brand-pizza">PIZZA</span>{" "}
            <strong className="brand-fiori">FIORI</strong>
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
        {totalItems > 0 && (
          <span className="order-item-count">
            {totalItems} {totalItems === 1 ? "producto" : "productos"}
          </span>
        )}
      </div>

      {resolvedCart.length === 0 ? (
        <div className="empty-cart">
          <span className="state-icon">
            <ShoppingBag size={23} aria-hidden="true" />
          </span>
          <h3>Tu pedido está vacío</h3>
          <p>Elegí una presentación del menú para empezar.</p>
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
          <nav className="checkout-steps" aria-label="Pasos del pedido">
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
            <div className="cart-card-heading">
              <h3>Tu carrito</h3>
              <a
                className="text-link"
                href="#menu"
                onClick={(event) => {
                  event.preventDefault();
                  returnToMenu();
                }}
              >
                Seguir mirando
              </a>
            </div>
            <div className="cart-lines">
              {resolvedCart.map((item) => (
                <article
                  className={`cart-line cart-line-${item.type}`}
                  key={item.key}
                >
                  {item.type === "product" && (
                    <img
                      src={item.product.imagen_url || PLACEHOLDER_IMAGE}
                      alt=""
                      onError={(event) => {
                        event.currentTarget.src = PLACEHOLDER_IMAGE;
                      }}
                    />
                  )}
                  <div className="cart-line-details">
                    <h4>{item.type === "product" ? item.product.nombre : item.offer.nombre}</h4>
                    {item.type === "product" ? (
                      <p>{formatProductPresentation(item.presentation)}</p>
                    ) : (
                      <ul className="cart-offer-selections">
                        {item.selections.map((selection, index) => (
                          <li key={`${selection.productId}-${index}`}>
                            {formatOfferSelection(selection)}
                          </li>
                        ))}
                      </ul>
                    )}
                    <strong>{formatCents(item.subtotalCents)}</strong>
                  </div>
                  <div className="cart-line-actions">
                    <div
                      className="quantity-control"
                      aria-label={`Cantidad de ${item.type === "product" ? item.product.nombre : item.offer.nombre}`}
                    >
                      <button
                        type="button"
                        aria-label={`Quitar una unidad de ${item.type === "product" ? item.product.nombre : item.offer.nombre}`}
                        onClick={() => updateCount(item, -1)}
                      >
                        <Minus size={14} aria-hidden="true" />
                      </button>
                      <span aria-live="polite">{item.count}</span>
                      <button
                        type="button"
                        aria-label={`Agregar una unidad de ${item.type === "product" ? item.product.nombre : item.offer.nombre}`}
                        onClick={() => updateCount(item, 1)}
                      >
                        <Plus size={14} aria-hidden="true" />
                      </button>
                    </div>
                    <button
                      className="remove-item"
                      type="button"
                      aria-label={`Eliminar ${item.type === "product" ? item.product.nombre : item.offer.nombre}, del pedido`}
                      onClick={() => removeItem(item)}
                    >
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </div>
                </article>
              ))}
            </div>
            <div className="cart-totals">
              <div>
                <span>Subtotal estimado</span>
                <strong>{formatCents(totalCents)}</strong>
              </div>
              <div>
                <span>Envío</span>
                <strong>A confirmar</strong>
              </div>
              <div className="estimated-total">
                <span>Total estimado</span>
                <strong>{formatCents(totalCents)}</strong>
              </div>
              <p>Envío y total final a confirmar por el local.</p>
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
              <div className="checkout-summary">
                <ShoppingBag size={18} aria-hidden="true" />
                <span>
                  {totalItems} {totalItems === 1 ? "producto" : "productos"} en tu pedido
                </span>
                <strong>{formatCents(totalCents)}</strong>
              </div>

              <form className="order-form" onSubmit={validateOrder} noValidate>
            <div className="form-title">
              <span className="state-icon">
                <Truck size={22} aria-hidden="true" />
              </span>
              <div>
                <h3>Datos para tu pedido</h3>
              </div>
            </div>

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
                <label className={order.fulfillment === "delivery" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="fulfillment"
                    value="delivery"
                    checked={order.fulfillment === "delivery"}
                    onChange={() => updateField("fulfillment", "delivery")}
                  />
                  <Truck size={18} aria-hidden="true" />
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
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
              </div>
              {errors.paymentMethod && (
                <span className="field-error" id="payment-method-error">
                  {errors.paymentMethod}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="order-notes">Observaciones <span className="optional-label">Opcional</span></label>
              <textarea
                id="order-notes"
                rows={3}
                value={order.notes}
                onChange={(event) => updateField("notes", event.target.value)}
                placeholder="Algún detalle para tener en cuenta"
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
              <div className="checkout-summary">
                <ShoppingBag size={18} aria-hidden="true" />
                <span>
                  {totalItems} {totalItems === 1 ? "producto" : "productos"} en tu pedido
                </span>
                <strong>{formatCents(totalCents)}</strong>
              </div>
              <section className="order-review" aria-labelledby="order-review-title">
              <div className="form-title">
                <span className="state-icon">
                  <Check size={22} aria-hidden="true" />
                </span>
                <div>
                  <h3 id="order-review-title">Revisá y confirmá tu pedido</h3>
                </div>
              </div>
              <ul className="review-products">
                {resolvedCart.map((item) => (
                  <li key={item.key}>
                    <span>
                      {item.type === "product"
                        ? `${item.count} x ${item.product.nombre}`
                        : `${item.count} x Promo: ${item.offer.nombre}`}
                      {item.type === "product" ? (
                        <small>{formatProductPresentation(item.presentation)}</small>
                      ) : (
                        <small>
                          {item.selections.map(formatOfferSelection).join(", ")}
                        </small>
                      )}
                    </span>
                    <strong>{formatCents(item.subtotalCents)}</strong>
                  </li>
                ))}
              </ul>
              <dl className="review-details">
                <div>
                  <dt>Nombre</dt>
                  <dd>{order.name.trim()}</dd>
                </div>
                <div>
                  <dt>Entrega</dt>
                  <dd>
                    {order.fulfillment === "delivery"
                      ? `Delivery · ${order.address.trim()}`
                      : "Retiro por el local"}
                  </dd>
                </div>
                <div>
                  <dt>Medio de pago</dt>
                  <dd>{order.paymentMethod}</dd>
                </div>
                <div>
                  <dt>Observaciones</dt>
                  <dd>{order.notes.trim() || "Sin observaciones"}</dd>
                </div>
              </dl>
              <div className="order-review-totals">
                <div><span>Subtotal</span><strong>{formatCents(totalCents)}</strong></div>
                <div><span>Envío</span><strong>A confirmar</strong></div>
                <div className="review-total">
                  <span>Total estimado</span>
                  <strong>{formatCents(totalCents)}</strong>
                </div>
              </div>
              {whatsappUrl ? (
                <a
                  className="whatsapp-button"
                  href={whatsappUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <MessageCircle size={19} aria-hidden="true" />
                  Enviar pedido por WhatsApp
                </a>
              ) : (
                <p className="whatsapp-config-error" role="alert">
                  Falta configurar un número de WhatsApp válido en{" "}
                  <code>VITE_WHATSAPP_PHONE</code> para habilitar el envío.
                </p>
              )}
              <p className="whatsapp-disclaimer" role="note">
                Se abrirá WhatsApp. Tocá «Enviar» para hacer el pedido; el local
                confirmará disponibilidad y envío.
              </p>
              <button
                className="edit-order-button"
                type="button"
                onClick={() => {
                  setValidated(false);
                  changeCheckoutStep("details");
                }}
              >
                Editar datos
              </button>
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
    <article className="offer-card">
      <div className="offer-label">
        <Flame className="promo-flame" size={14} aria-hidden="true" />
        PROMO DEL LOCAL
      </div>
      <h3>{offer.nombre}</h3>
      {offer.descripcion && <p className="offer-description">{offer.descripcion}</p>}
      {offer.items.length > 0 && (
        <ul className="offer-items">
          {offer.items.map((item, index) => {
            const type = getOfferItemType(item);
            const itemDescription = type === "category"
              ? `a elección en ${categoryNames.get(item.categoria_id ?? -1) ?? "la categoría"}`
              : type === "options"
                ? `elegí entre ${item.producto_ids
                    .map((productId) => productNames.get(productId))
                    .filter((name): name is string => Boolean(name))
                    .join(" / ")}`
                : productNames.get(item.producto_ids[0]) ?? "Producto";
            return (
              <li key={`${offer.id}-${index}`}>
                <span>{formatOfferQuantity(Number(item.cantidad))} ×</span>{" "}
                {itemDescription}
              </li>
            );
          })}
        </ul>
      )}
      <div className="offer-footer">
        <strong className="offer-price">{formatPrice(offer.precio)}</strong>
        {configurableItems.length > 0 ? (
          <button
            className="offer-add-button"
            type="button"
            onClick={() => setIsConfiguring(true)}
          >
            <Plus size={15} aria-hidden="true" />
            Agregar promo
          </button>
        ) : (
          <button
            className="offer-add-button"
            type="button"
            onClick={() => {
              const selections = selectionsForCart();
              if (selections.length > 0) onAddOffer(offer, selections);
            }}
          >
            <Plus size={15} aria-hidden="true" />
            Agregar promo
          </button>
        )}
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
            <div>
              <span className="eyebrow">CONFIGURÁ TU PROMO</span>
              <h2 id={`offer-dialog-title-${offer.id}`}>{offer.nombre}</h2>
            </div>
            <button
              className="offer-dialog-close"
              type="button"
              aria-label="Cerrar selección de promo"
              onClick={() => setIsConfiguring(false)}
            >
              <X size={20} aria-hidden="true" />
            </button>
          </div>
          {offer.descripcion && (
            <p className="offer-dialog-description">{offer.descripcion}</p>
          )}
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
                return (
                  <fieldset className="offer-config-group" key={index}>
                    <legend>
                      Elegí {formatOfferQuantity(Number(item.cantidad))} en{" "}
                      {categoryNames.get(item.categoria_id ?? -1) ?? "la categoría"}
                      <small>{selectedTotal} de {formatOfferQuantity(Number(item.cantidad))}</small>
                    </legend>
                    {categoryProducts.map((product) => {
                      const quantity = selections?.get(product.id) ?? 0;
                      return (
                        <div className="offer-choice-row" key={product.id}>
                          <span>{product.nombre}</span>
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
                    Elegí una opción · {formatOfferQuantity(Number(item.cantidad))}
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
                className="offer-cancel-button"
                type="button"
                onClick={() => setIsConfiguring(false)}
              >
                Cancelar
              </button>
              <button
                className="offer-add-button"
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
    <section className="menu-section" aria-label="Cargando menú" aria-busy="true">
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
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
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

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#0d0d0d" : "#fffaf1",
    );
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

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

  const goToCart = () => {
    setIsCheckoutOpen(true);
  };

  return (
    <div className={cartItemCount > 0 ? "site-shell has-cart" : "site-shell"}>
      <header className="site-header">
        <a className="brand" href="#inicio" aria-label="PIZZA FIORI, inicio">
          <img className="brand-logo" src="/logo.png" alt="" />
          <span className="brand-name">
            <span className="brand-pizza">PIZZA</span>{" "}
            <strong className="brand-fiori">FIORI</strong>
          </span>
        </a>
        <div className="header-actions">
          <a className="header-link" href="#menu">
            Menú <ArrowDown size={16} aria-hidden="true" />
          </a>
          <button
            className="theme-toggle"
            type="button"
            aria-label={theme === "dark" ? "Activar modo claro" : "Activar modo oscuro"}
            aria-pressed={theme === "dark"}
            title={theme === "dark" ? "Modo claro" : "Modo oscuro"}
            onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          >
            {theme === "dark"
              ? <Sun size={18} aria-hidden="true" />
              : <Moon size={18} aria-hidden="true" />}
          </button>
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
            <span className="hero-seal-spark spark-one">✳</span>
            <span className="hero-seal-spark spark-two">✳</span>
          </div>
        </section>

        <section className="menu-section" id="menu">
          <div className="section-heading">
            <div>
              <h2>Menú</h2>
            </div>
            {catalog && (
              <p className="catalog-date">
                <Clock3 size={15} aria-hidden="true" />
                Actualizado {formatPublishDate(catalog.publicado_en)}
              </p>
            )}
          </div>

          {isLoading && <LoadingState />}

          {!isLoading && error && (
            <div className="state-panel error-panel" role="alert">
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
            <div className="state-panel">
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
                    <Flame className="promo-flame" size={16} aria-hidden="true" />
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
                    <span className="category-flower" aria-hidden="true">
                      ✳
                    </span>
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
                      <span className="category-flower" aria-hidden="true">
                ✳
                      </span>
                      <h3>{category.nombre}</h3>
                      <span className="category-count">
                {productsByCategory.get(category.id)?.length ?? 0}{" "}
                {productsByCategory.get(category.id)?.length === 1
                  ? "opción"
                  : "opciones"}
                      </span>
                    </div>
                    <div className="product-grid">
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
          <span className="closing-flower" aria-hidden="true">✳</span>
          <p>Hecho para compartir.</p>
          <span className="closing-flower" aria-hidden="true">✳</span>
        </section>
      </main>

      <footer className="site-footer">
        <a className="footer-brand" href="#inicio">
          <span className="brand-pizza">PIZZA</span>{" "}
          <strong className="brand-fiori">FIORI</strong>
        </a>
        <span>Pedidos por WhatsApp</span>
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
          <span>Ver pedido</span>
          <strong>{formatCents(cartTotalCents)}</strong>
        </button>
      )}
    </div>
  );
}

export default App;

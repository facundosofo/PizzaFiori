/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CATALOG_POINTER_URL: string;
  readonly VITE_HIDDEN_CATEGORIES?: string;
  readonly VITE_ORDER_PAYMENT_METHODS?: string;
  readonly VITE_WHATSAPP_PHONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

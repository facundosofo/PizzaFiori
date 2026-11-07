/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CATALOG_POINTER_URL: string;
  readonly VITE_FACEBOOK_URL?: string;
  readonly VITE_GOOGLE_MAPS_URL?: string;
  readonly VITE_HIDDEN_CATEGORIES?: string;
  readonly VITE_INSTAGRAM_URL?: string;
  readonly VITE_PHONE_NUMBER?: string;
  readonly VITE_WHATSAPP_PHONE?: string;
  readonly VITE_WHATSAPP_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

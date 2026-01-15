const env = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
};

if (!env.API_BASE_URL) {
  throw new Error("❌ API_BASE_URL no está definida");
}

export default env;

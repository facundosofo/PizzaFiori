import { useEffect, useState } from "react";

const readStorageValue = <T,>(key: string, fallback: T): T => {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
};

export const usePersistentState = <T,>(key: string, fallback: T) => {
  const [value, setValue] = useState<T>(() => readStorageValue(key, fallback));

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore storage failures (e.g., private mode or full storage).
    }
  }, [key, value]);

  return [value, setValue] as const;
};

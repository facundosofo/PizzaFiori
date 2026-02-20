import { useCallback, useState } from "react";
import axios from "axios";
import {
  generateSalesReport,
  type ReportRequest,
} from "../services/reportService";
import { formatDateYMD } from "../utils/formatters";

const buildFallbackFilename = (request: ReportRequest): string => {
  if (request.dateFrom && request.dateTo) {
    return `reporte_ventas_${formatDateYMD(request.dateFrom)}_${formatDateYMD(request.dateTo)}.pdf`;
  }

  if (request.dateFrom) {
    return `reporte_ventas_desde_${formatDateYMD(request.dateFrom)}.pdf`;
  }

  if (request.dateTo) {
    return `reporte_ventas_hasta_${formatDateYMD(request.dateTo)}.pdf`;
  }

  return "reporte_ventas.pdf";
};

const extractErrorMessage = async (error: unknown): Promise<string> => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;

    if (status === 404) {
      return "No hay ventas en el periodo seleccionado.";
    }

    if (status === 500) {
      return "Error al generar el reporte. Intenta nuevamente.";
    }

    const data = error.response?.data;

    if (data instanceof Blob) {
      const text = await data.text();
      if (text) {
        try {
          const parsed = JSON.parse(text);
          if (parsed?.detail) {
            return typeof parsed.detail === "string" ? parsed.detail : "Error al generar reporte.";
          }
          if (parsed?.message) {
            return parsed.message;
          }
        } catch {
          return text;
        }
      }
    }

    if (data && typeof data === "object") {
      const detail = (data as { detail?: string; message?: string }).detail ||
        (data as { detail?: string; message?: string }).message;
      if (detail) return detail;
    }

    if (error.message) return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Error desconocido al generar reporte.";
};

export const useGenerateReport = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = useCallback(async (request: ReportRequest) => {
    setLoading(true);
    setError(null);

    try {
      const { blob, filename } = await generateSalesReport(request);
      const fileNameToUse = filename ?? buildFallbackFilename(request);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileNameToUse;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return true;
    } catch (err) {
      const message = await extractErrorMessage(err);
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = () => setError(null);

  return { generateReport, loading, error, clearError };
};

export default useGenerateReport;

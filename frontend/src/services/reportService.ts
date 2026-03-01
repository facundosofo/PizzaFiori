import api from "./http";
import { formatDateYMD } from "../utils/formatters";

export type ReportMode = "light" | "dark";
export type ReportType = "general" | "balance" | "ventas" | "costo";
export type DateRangeMode = "rango" | "mes" | "anio";

export type ReportSections = {
  resumenPeriodo: boolean;
  resumenDia: boolean;
  resumenCategoria: boolean;
  resumenProductos: boolean;
  detalleVentas: boolean;
};

export type ReportRequest = {
  reportType: ReportType;
  dateRangeMode: DateRangeMode;
  dateFrom: Date | null;
  dateTo: Date | null;
  selectedMonth: number;
  selectedYear: number;
  mode: ReportMode;
  sections: ReportSections;
};

export type ReportFile = {
  blob: Blob;
  filename: string | null;
};

const parseFilenameFromHeader = (contentDisposition?: string): string | null => {
  if (!contentDisposition) return null;

  const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  if (!match?.[1]) return null;

  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
};

export const generateSalesReport = async (request: ReportRequest): Promise<ReportFile> => {
  const params: Record<string, string> = {
    modo: request.mode,
    mostrar_resumen_periodo: String(request.sections.resumenPeriodo),
    mostrar_resumen_dia: String(request.sections.resumenDia),
    mostrar_resumen_categoria: String(request.sections.resumenCategoria),
    mostrar_resumen_productos: String(request.sections.resumenProductos),
    mostrar_detalle_ventas: String(request.sections.detalleVentas),
  };

  let dateFrom: Date | null = null;
  let dateTo: Date | null = null;

  if (request.dateRangeMode === "rango") {
    dateFrom = request.dateFrom;
    dateTo = request.dateTo;
  } else if (request.dateRangeMode === "mes") {
    dateFrom = new Date(request.selectedYear, request.selectedMonth, 1);
    dateTo = new Date(request.selectedYear, request.selectedMonth + 1, 0);
  } else if (request.dateRangeMode === "anio") {
    dateFrom = new Date(request.selectedYear, 0, 1);
    dateTo = new Date(request.selectedYear, 11, 31);
  }

  if (dateFrom) {
    params.fecha_desde = formatDateYMD(dateFrom);
  }

  if (dateTo) {
    params.fecha_hasta = formatDateYMD(dateTo);
  }

  const response = await api.get<Blob>("/ventas/reporte/pdf", {
    params,
    responseType: "blob",
  });

  const filename = parseFilenameFromHeader(response.headers["content-disposition"]);

  return { blob: response.data, filename };
};

export const getAvailableYears = async (): Promise<number[]> => {
  const response = await api.get<number[]>("/ventas/anios-disponibles");
  return response.data;
};

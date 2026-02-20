import api from "./http";
import { formatDateYMD } from "../utils/formatters";

export type ReportMode = "light" | "dark";

export type ReportSections = {
  resumenPeriodo: boolean;
  resumenDia: boolean;
  resumenCategoria: boolean;
  resumenProductos: boolean;
  detalleVentas: boolean;
};

export type ReportRequest = {
  dateFrom: Date | null;
  dateTo: Date | null;
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

  if (request.dateFrom) {
    params.fecha_desde = formatDateYMD(request.dateFrom);
  }

  if (request.dateTo) {
    params.fecha_hasta = formatDateYMD(request.dateTo);
  }

  const response = await api.get<Blob>("/ventas/reporte/pdf", {
    params,
    responseType: "blob",
  });

  const filename = parseFilenameFromHeader(response.headers["content-disposition"]);

  return { blob: response.data, filename };
};

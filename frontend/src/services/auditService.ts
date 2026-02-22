import api from "./http";
import { formatDateAPI } from "../utils/formatters";

export interface AuditLog {
  id: number;
  timestamp: string;
  username: string;
  entity_type: string;
  entity_id: number;
  action: string;
  changes: Record<string, any>;
}

export interface AuditSearchResponse {
  total: number;
  limit: number;
  offset: number;
  records: AuditLog[];
}

export interface AuditSearchParams {
  startDate?: Date | null;
  endDate?: Date | null;
  entityType?: string;
  username?: string;
  action?: string;
  limit?: number;
  offset?: number;
}

export const searchAuditLogs = async (
  params: AuditSearchParams
): Promise<AuditSearchResponse> => {
  try {
    const query: Record<string, string | number> = {};

    if (params.startDate) {
      query.start_date = formatDateAPI(params.startDate);
    }

    if (params.endDate) {
      query.end_date = formatDateAPI(params.endDate);
    }

    if (params.entityType) {
      query.entity_type = params.entityType;
    }

    if (params.username) {
      query.username = params.username;
    }

    if (params.action) {
      query.action = params.action;
    }

    if (typeof params.limit === "number") {
      query.limit = params.limit;
    }

    if (typeof params.offset === "number") {
      query.offset = params.offset;
    }

    const response = await api.get<AuditSearchResponse>("/audit/search", {
      params: query,
    });

    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

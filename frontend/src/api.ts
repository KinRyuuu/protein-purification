/**
 * HTTP client for the protein purification backend API.
 * All endpoints return updated SessionState for frontend sync.
 */

import type { SessionState } from "./state";

const BASE = "/api";

function snakeToCamel(s: string): string {
  return s.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase());
}

function convertKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(convertKeys);
  if (obj !== null && typeof obj === "object") {
    const o = obj as Record<string, unknown>;
    return Object.fromEntries(
      Object.entries(o).map(([k, v]) => [snakeToCamel(k), convertKeys(v)]),
    );
  }
  return obj;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  const json = await res.json();
  return convertKeys(json) as T;
}

export function initApi(): void {
  // No initialization needed
}

export async function createSession(): Promise<SessionState> {
  return request<SessionState>("POST", "/sessions");
}

export async function loadSession(file: File): Promise<SessionState> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/sessions/load`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail || res.statusText);
  }
  const json = await res.json();
  return convertKeys(json) as SessionState;
}

export async function getSessionState(
  sessionId: string,
): Promise<SessionState> {
  return request<SessionState>("GET", `/sessions/${sessionId}/state`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  return request<void>("DELETE", `/sessions/${sessionId}`);
}

export async function chooseMixture(
  sessionId: string,
  name: string,
): Promise<SessionState> {
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/choose-mixture`,
    { name },
  );
}

export async function chooseEnzyme(
  sessionId: string,
  enzymeIndex: number,
): Promise<SessionState> {
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/choose-enzyme`,
    { enzyme_index: enzymeIndex },
  );
}

export interface SeparationParams {
  type: string;
  saturation?: number;
  temperature?: number;
  duration?: number;
  matrix?: string;
  media?: string;
  ph?: number;
  gradientType?: string;
  startGrad?: number;
  endGrad?: number;
  medium?: string;
  ligand?: string;
  elution?: string;
  confirmed?: boolean;
}

export async function runSeparation(
  sessionId: string,
  params: SeparationParams,
): Promise<SessionState> {
  const body: Record<string, unknown> = { type: params.type };
  if (params.saturation !== undefined) body.saturation = params.saturation;
  if (params.temperature !== undefined) body.temperature = params.temperature;
  if (params.duration !== undefined) body.duration = params.duration;
  if (params.matrix !== undefined) body.matrix = params.matrix;
  if (params.media !== undefined) body.media = params.media;
  if (params.ph !== undefined) body.ph = params.ph;
  if (params.gradientType !== undefined)
    body.gradient_type = params.gradientType;
  if (params.startGrad !== undefined) body.start_grad = params.startGrad;
  if (params.endGrad !== undefined) body.end_grad = params.endGrad;
  if (params.medium !== undefined) body.medium = params.medium;
  if (params.ligand !== undefined) body.ligand = params.ligand;
  if (params.elution !== undefined) body.elution = params.elution;
  if (params.confirmed !== undefined) body.confirmed = params.confirmed;
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/separate`,
    body,
  );
}

export async function asChoice(
  sessionId: string,
  choice: "soluble" | "insoluble",
): Promise<SessionState> {
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/as-choice`,
    { choice },
  );
}

export async function abandonStep(
  sessionId: string,
): Promise<SessionState> {
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/abandon-step`,
  );
}

export async function runAssay(sessionId: string): Promise<SessionState> {
  return request<SessionState>("POST", `/sessions/${sessionId}/assay`);
}

export async function dilute(sessionId: string): Promise<SessionState> {
  return request<SessionState>("POST", `/sessions/${sessionId}/dilute`);
}

export async function poolFractions(
  sessionId: string,
  start: number,
  end: number,
): Promise<SessionState> {
  return request<SessionState>("POST", `/sessions/${sessionId}/pool`, {
    start,
    end,
  });
}

export async function run1dPage(
  sessionId: string,
  fractions: number[],
): Promise<SessionState> {
  return request<SessionState>("POST", `/sessions/${sessionId}/page-1d`, {
    fractions,
  });
}

export async function run2dPage(
  sessionId: string,
  fraction: number,
): Promise<SessionState> {
  return request<SessionState>("POST", `/sessions/${sessionId}/page-2d`, {
    fraction,
  });
}

export async function toggleStain(
  sessionId: string,
): Promise<SessionState> {
  return request<SessionState>(
    "POST",
    `/sessions/${sessionId}/toggle-stain`,
  );
}

export async function downloadSave(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/save`);
  if (!res.ok) throw new ApiError(res.status, "Failed to save");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "session.ppmixture";
  const disposition = res.headers.get("Content-Disposition");
  if (disposition) {
    const match = disposition.match(/filename="(.+)"/);
    if (match) a.download = match[1];
  }
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function listMixtures(): Promise<string[]> {
  const result = await request<{ mixtures: string[] }>("GET", "/mixtures");
  return result.mixtures;
}

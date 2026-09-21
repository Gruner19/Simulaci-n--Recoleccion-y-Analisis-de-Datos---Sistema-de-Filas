export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type Experiment = { id: number; status: string; hypothesis_id: number | null; created_at: string };
export type Run = {
  run_id: number; cell: number; replica: number; factor_a: number; factor_b: number; factor_c: number;
  servers: number; arrival_rate: number; service: string; rho: number; spawn_key: number;
  execution_order: number; response: number | null; elapsed_s: number | null; state: string; error: string | null;
};
export type Progress = { running: boolean; completed: number; total: number; error?: string | null };
export type Verification = { cells: Array<{ cell: number; servers: number; arrival_rate: number; service: string; simulated: number; theoretical: number | null; relative_error_pct: number | null; status: string }>; max_relative_error_pct: number | null; passed: boolean };
export type Pilot = { pilot_only: boolean; factorial_eligible: boolean; summary: { mean: number; sd: number; cv_pct: number; shapiro_p: number; log_shapiro_p: number; lag1_correlation: number | null; theoretical_mean: number; relative_error_pct: number; normality_warning: string }; individual_waits: { acf: number[] }; welch: { replicas: number; window: number; n_points: number }; run_length: Array<{ n_clients: number; cv_pct: number; ci_half_width_pct: number; mean_time_s: number }>; figures: string[] };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Erro HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  createExperiment: (body: object) => request<Experiment>("/api/experiments", { method: "POST", body: JSON.stringify(body) }),
  saveHypothesis: (id: number, text: string) => request<Experiment>(`/api/experiments/${id}/hypothesis`, { method: "POST", body: JSON.stringify({ text }) }),
  createPlan: (id: number) => request<Run[]>(`/api/experiments/${id}/plan`, { method: "POST" }),
  getPlan: (id: number) => request<Run[]>(`/api/experiments/${id}/plan`),
  start: (id: number, workers: number) => request<{ status: string }>(`/api/experiments/${id}/run?workers=${workers}`, { method: "POST" }),
  cancel: (id: number) => request<{ status: string }>(`/api/experiments/${id}/cancel`, { method: "POST" }),
  retry: (id: number, workers: number) => request<{ status: string }>(`/api/experiments/${id}/retry?workers=${workers}`, { method: "POST" }),
  verify: (body: object) => request<Verification>("/api/verificacao", { method: "POST", body: JSON.stringify(body) }),
  pilot: (body: object) => request<Pilot>("/api/piloto", { method: "POST", body: JSON.stringify(body) }),
};
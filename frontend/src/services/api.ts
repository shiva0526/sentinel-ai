/**
 * api.ts — Orchestrator API client service.
 * 
 * All API calls go through this service. No direct axios calls in components.
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 120_000, // 2 minutes (pipeline can take a while)
  headers: {
    'Content-Type': 'application/json',
  },
});


export interface HuntRequest {
  repo_url: string;
  email?: string;
  scan_mode?: string;
}

export interface HuntResponse {
  status: string;
  mode?: string;
  repo_stats?: { file_count: number; total_lines: number; recommended_mode: string };
  vulnerability_found?: string | null;
  secure_patch?: string | null;
  test_status?: string | null;
  total_vulnerabilities?: number;
  vulnerabilities?: any[];
  patched_files?: number;
  pr_url?: string | null;
  error?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}


/**
 * Trigger the full SentinelAI pipeline.
 */
export async function launchHunt(repoUrl: string, scanMode: string = "auto", email: string = ""): Promise<HuntResponse> {
  const response = await apiClient.post<HuntResponse>('/hunt', { repo_url: repoUrl, email: email || undefined, scan_mode: scanMode });
  return response.data;
}

/**
 * Check if the orchestrator is healthy.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

export default apiClient;

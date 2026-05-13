import type { Site, Scan, SitemapUrl } from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  sites: {
    list: () => request<Site[]>("/sites"),
    create: (data: { name: string; base_url: string; sitemap_url?: string }) =>
      request<Site>("/sites", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number) => request<Site>(`/sites/${id}`),
    delete: (id: number) => request<void>(`/sites/${id}`, { method: "DELETE" }),
  },
  sitemaps: {
    getUrls: (siteId: number) => request<SitemapUrl[]>(`/sites/${siteId}/urls`),
  },
  scans: {
    create: (data: { site_id: number; route_url: string }) =>
      request<Scan>("/scans", { method: "POST", body: JSON.stringify(data) }),
    list: (siteId?: number) =>
      request<Scan[]>(`/scans${siteId ? `?site_id=${siteId}` : ""}`),
    get: (id: number) =>
      request<Scan>(`/scans/${id}?include=results`),
    cancel: (id: number) =>
      request<Scan>(`/scans/${id}`, { method: "DELETE" }),
  },
};
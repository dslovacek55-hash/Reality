import type {
  PropertyListResponse,
  PropertyDetail,
  PriceHistoryEntry,
  Stats,
  MapMarker,
  CityCount,
  PropertyFilters,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchApi<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getProperties(filters: PropertyFilters = {}): Promise<PropertyListResponse> {
  return fetchApi<PropertyListResponse>('/api/properties', filters as Record<string, string | number | undefined>);
}

export async function getProperty(id: number): Promise<PropertyDetail> {
  return fetchApi<PropertyDetail>(`/api/properties/${id}`);
}

export async function getPriceHistory(id: number): Promise<PriceHistoryEntry[]> {
  return fetchApi<PriceHistoryEntry[]>(`/api/properties/${id}/price-history`);
}

export async function getStats(): Promise<Stats> {
  return fetchApi<Stats>('/api/stats');
}

export async function getMapMarkers(filters?: Partial<PropertyFilters>): Promise<MapMarker[]> {
  return fetchApi<MapMarker[]>('/api/properties/geo/markers', filters as Record<string, string | number | undefined>);
}

export async function getCities(): Promise<CityCount[]> {
  return fetchApi<CityCount[]>('/api/stats/cities');
}

// SWR fetcher
export const fetcher = (url: string) => fetch(`${API_BASE}${url}`).then(r => r.json());

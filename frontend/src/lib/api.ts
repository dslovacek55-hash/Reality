import type {
  PropertyListResponse,
  PropertyDetail,
  PriceHistoryEntry,
  Stats,
  MapMarker,
  CityCount,
  PropertyFilters,
  AvgPriceM2Map,
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

export async function getAvgPriceM2(params?: {
  property_type?: string;
  transaction_type?: string;
  disposition?: string;
}): Promise<AvgPriceM2Map> {
  return fetchApi<AvgPriceM2Map>('/api/stats/avg-price-m2', params as Record<string, string | number | undefined>);
}

export async function getFavoriteIds(sessionId: string): Promise<number[]> {
  return fetchApi<number[]>(`/api/favorites/${sessionId}/ids`);
}

export async function addFavorite(sessionId: string, propertyId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/favorites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, property_id: propertyId }),
  });
  if (!res.ok && res.status !== 409) {
    throw new Error(`API error: ${res.status}`);
  }
}

export async function removeFavorite(sessionId: string, propertyId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/favorites/${sessionId}/${propertyId}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 404) {
    throw new Error(`API error: ${res.status}`);
  }
}

export function getExportUrl(filters?: Partial<PropertyFilters>): string {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'per_page' && key !== 'sort') {
        params.set(key, String(value));
      }
    });
  }
  const qs = params.toString();
  return `${API_BASE}/api/export/csv${qs ? `?${qs}` : ''}`;
}

// SWR fetcher with error handling
export const fetcher = async (url: string) => {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
};

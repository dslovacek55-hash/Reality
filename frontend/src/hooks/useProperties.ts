'use client';

import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { PropertyListResponse, Stats, MapMarker, CityCount, PropertyFilters, AvgPriceM2Map } from '@/lib/types';

function buildQuery(filters: PropertyFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value));
    }
  });
  return params.toString();
}

export function useProperties(filters: PropertyFilters = {}) {
  const query = buildQuery({ per_page: 20, ...filters });
  const { data, error, isLoading, mutate } = useSWR<PropertyListResponse>(
    `/api/properties?${query}`,
    fetcher,
    { refreshInterval: 60000 }
  );

  return { data, error, isLoading, mutate };
}

export function useStats() {
  const { data, error, isLoading } = useSWR<Stats>(
    '/api/stats',
    fetcher,
    { refreshInterval: 60000 }
  );

  return { stats: data, error, isLoading };
}

export function useMapMarkers(filters?: Partial<PropertyFilters>) {
  const query = filters ? buildQuery(filters as PropertyFilters) : '';
  const { data, error, isLoading } = useSWR<MapMarker[]>(
    `/api/properties/geo/markers?${query}`,
    fetcher,
    { refreshInterval: 120000 }
  );

  return { markers: data || [], error, isLoading };
}

export function useCities() {
  const { data, error, isLoading } = useSWR<CityCount[]>(
    '/api/stats/cities',
    fetcher,
    { refreshInterval: 300000 }
  );

  return { cities: data || [], error, isLoading };
}

export function useAvgPriceM2(filters?: Partial<PropertyFilters>) {
  const params = new URLSearchParams();
  if (filters?.property_type) params.set('property_type', filters.property_type);
  if (filters?.transaction_type) params.set('transaction_type', filters.transaction_type);
  if (filters?.disposition) params.set('disposition', filters.disposition);
  const qs = params.toString();

  const { data, error, isLoading } = useSWR<AvgPriceM2Map>(
    `/api/stats/avg-price-m2${qs ? `?${qs}` : ''}`,
    fetcher,
    {
      refreshInterval: 300000,
      shouldRetryOnError: false,
      onError: () => {},
    }
  );

  return { avgPrices: data || {}, error, isLoading };
}

export function useFavoriteIds(sessionId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<number[]>(
    sessionId ? `/api/favorites/${sessionId}/ids` : null,
    fetcher,
    { refreshInterval: 60000, shouldRetryOnError: false }
  );

  return { favoriteIds: data || [], error, isLoading, mutate };
}

export interface Property {
  id: number;
  source: string;
  external_id: string;
  url: string | null;
  title: string | null;
  description: string | null;
  property_type: string | null;
  transaction_type: string | null;
  disposition: string | null;
  price: number | null;
  price_currency: string;
  size_m2: number | null;
  rooms: number | null;
  latitude: number | null;
  longitude: number | null;
  city: string | null;
  district: string | null;
  address: string | null;
  images: string[];
  status: string;
  duplicate_of: number | null;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyDetail extends Property {
  price_history: PriceHistoryEntry[];
  raw_data: Record<string, unknown>;
}

export interface PriceHistoryEntry {
  id: number;
  price: number;
  price_per_m2: number | null;
  recorded_at: string;
}

export interface PropertyListResponse {
  items: Property[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Stats {
  total_active: number;
  new_today: number;
  price_drops_today: number;
  removed_today: number;
  by_source: Record<string, number>;
  by_type: Record<string, number>;
  by_transaction: Record<string, number>;
}

export interface MapMarker {
  id: number;
  lat: number;
  lng: number;
  price: number | null;
  disposition: string | null;
  title: string | null;
  source: string;
}

export interface CityCount {
  city: string;
  label: string;
  count: number;
}

export interface PropertyFilters {
  property_type?: string;
  transaction_type?: string;
  city?: string;
  disposition?: string;
  price_min?: number;
  price_max?: number;
  size_min?: number;
  size_max?: number;
  status?: string;
  source?: string;
  sort?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

export interface AvgPriceM2 {
  avg_price_m2: number;
  count: number;
  czso_price_m2?: number;
  czso_region?: string;
  by_disposition?: {
    avg_price_m2: number;
    count: number;
  };
}

export type AvgPriceM2Map = Record<string, AvgPriceM2>;

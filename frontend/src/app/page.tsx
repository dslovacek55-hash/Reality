'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import StatsBar from '@/components/StatsBar';
import FilterSidebar from '@/components/FilterSidebar';
import PropertyList from '@/components/PropertyList';
import PropertyMap from '@/components/PropertyMap';
import { useProperties, useMapMarkers, useAvgPriceM2 } from '@/hooks/useProperties';
import { useFavorites } from '@/hooks/useFavorites';
import { getExportUrl } from '@/lib/api';
import type { PropertyFilters } from '@/lib/types';

export default function Dashboard() {
  const [filters, setFilters] = useState<PropertyFilters>({
    page: 1,
    per_page: 20,
    sort: 'newest',
  });
  const [view, setView] = useState<'list' | 'map' | 'both'>('both');

  const { data, isLoading } = useProperties(filters);
  const { markers, isLoading: markersLoading } = useMapMarkers(filters);
  const { avgPrices } = useAvgPriceM2(filters);
  const { toggleFavorite, isFavorite, favoriteIds } = useFavorites();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <StatsBar />

        {/* View toggle + Export */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {(['list', 'map', 'both'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  view === v
                    ? 'bg-primary-50 border-primary-300 text-primary-700'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {v === 'list' ? 'Seznam' : v === 'map' ? 'Mapa' : 'Oboji'}
              </button>
            ))}
          </div>
          <a
            href={getExportUrl(filters)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </a>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <aside className="w-full lg:w-72 flex-shrink-0">
            <FilterSidebar filters={filters} onChange={setFilters} />
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0 space-y-6">
            {(view === 'map' || view === 'both') && (
              <PropertyMap markers={markers} isLoading={markersLoading} />
            )}
            {(view === 'list' || view === 'both') && (
              <PropertyList
                properties={data?.items || []}
                isLoading={isLoading}
                total={data?.total || 0}
                page={data?.page || 1}
                pages={data?.pages || 0}
                onPageChange={(page) => setFilters({ ...filters, page })}
                avgPrices={avgPrices}
                favoriteIds={favoriteIds}
                onToggleFavorite={toggleFavorite}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

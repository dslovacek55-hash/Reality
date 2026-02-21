'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import StatsBar from '@/components/StatsBar';
import FilterSidebar from '@/components/FilterSidebar';
import PropertyList from '@/components/PropertyList';
import PropertyMap from '@/components/PropertyMap';
import { useProperties, useMapMarkers } from '@/hooks/useProperties';
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <StatsBar />

        {/* View toggle */}
        <div className="flex items-center gap-2 mb-4">
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
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

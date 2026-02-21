'use client';

import PropertyCard from './PropertyCard';
import type { Property } from '@/lib/types';

interface Props {
  properties: Property[];
  isLoading: boolean;
  total: number;
  page: number;
  pages: number;
  onPageChange: (page: number) => void;
}

export default function PropertyList({ properties, isLoading, total, page, pages, onPageChange }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 overflow-hidden animate-pulse">
            <div className="h-48 bg-gray-200" />
            <div className="p-4 space-y-2">
              <div className="h-5 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded w-48" />
              <div className="h-3 bg-gray-200 rounded w-32" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (properties.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">Zadne nemovitosti</h3>
        <p className="text-sm text-gray-500">Zkuste zmenit filtry nebo pockejte na dalsi aktualizaci dat.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          {total.toLocaleString('cs-CZ')} vysledku
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {properties.map((property) => (
          <PropertyCard key={property.id} property={property} />
        ))}
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Predchozi
          </button>
          <span className="text-sm text-gray-500 px-3">
            {page} / {pages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= pages}
            className="px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Dalsi
          </button>
        </div>
      )}
    </div>
  );
}

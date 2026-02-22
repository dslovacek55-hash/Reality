'use client';

import { useCities } from '@/hooks/useProperties';
import type { PropertyFilters } from '@/lib/types';

interface Props {
  filters: PropertyFilters;
  onChange: (filters: PropertyFilters) => void;
}

const DISPOSITIONS = ['1+kk', '1+1', '2+kk', '2+1', '3+kk', '3+1', '4+kk', '4+1', '5+kk', '5+1'];

export default function FilterSidebar({ filters, onChange }: Props) {
  const { cities } = useCities();

  const update = (key: keyof PropertyFilters, value: string | number | undefined) => {
    onChange({ ...filters, [key]: value || undefined, page: 1 });
  };

  const reset = () => {
    onChange({ page: 1, per_page: 20, sort: 'newest' });
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Filtry</h2>
        <button onClick={reset} className="text-xs text-primary-600 hover:text-primary-700 font-medium">
          Resetovat
        </button>
      </div>

      {/* Search */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Hledani</label>
        <input
          type="text"
          placeholder="Nazev, adresa..."
          value={filters.search || ''}
          onChange={(e) => update('search', e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Transaction type */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Typ transakce</label>
        <div className="grid grid-cols-3 gap-1.5">
          {[
            { value: '', label: 'Vse' },
            { value: 'prodej', label: 'Prodej' },
            { value: 'pronajem', label: 'Pronajem' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => update('transaction_type', value)}
              className={`px-2 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                (filters.transaction_type || '') === value
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Property type */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Typ nemovitosti</label>
        <div className="grid grid-cols-2 gap-1.5">
          {[
            { value: '', label: 'Vse' },
            { value: 'byt', label: 'Byt' },
            { value: 'dum', label: 'Dum' },
            { value: 'pozemek', label: 'Pozemek' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => update('property_type', value)}
              className={`px-2 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                (filters.property_type || '') === value
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* City */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Mesto</label>
        <select
          value={filters.city || ''}
          onChange={(e) => update('city', e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
        >
          <option value="">Vsechna mesta</option>
          {cities.map((c) => (
            <option key={c.city} value={c.city}>
              {c.label || c.city} ({c.count})
            </option>
          ))}
        </select>
      </div>

      {/* Disposition (multi-select, backend supports CSV) */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Dispozice</label>
        <div className="flex flex-wrap gap-1.5">
          {DISPOSITIONS.map((d) => {
            const selected = (filters.disposition || '').split(',').filter(Boolean);
            const isSelected = selected.includes(d);
            return (
              <button
                key={d}
                onClick={() => {
                  let next: string[];
                  if (isSelected) {
                    next = selected.filter((s) => s !== d);
                  } else {
                    next = [...selected, d];
                  }
                  update('disposition', next.join(','));
                }}
                className={`px-2 py-1 text-xs font-medium rounded-md border transition-colors ${
                  isSelected
                    ? 'bg-primary-50 border-primary-300 text-primary-700'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {d}
              </button>
            );
          })}
        </div>
      </div>

      {/* Price range */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Cena (CZK)</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Od"
            value={filters.price_min || ''}
            onChange={(e) => update('price_min', e.target.value ? Number(e.target.value) : undefined)}
            className="w-1/2 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <input
            type="number"
            placeholder="Do"
            value={filters.price_max || ''}
            onChange={(e) => update('price_max', e.target.value ? Number(e.target.value) : undefined)}
            className="w-1/2 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Size range */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Plocha (m²)</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Od"
            value={filters.size_min || ''}
            onChange={(e) => update('size_min', e.target.value ? Number(e.target.value) : undefined)}
            className="w-1/2 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <input
            type="number"
            placeholder="Do"
            value={filters.size_max || ''}
            onChange={(e) => update('size_max', e.target.value ? Number(e.target.value) : undefined)}
            className="w-1/2 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Source */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Zdroj</label>
        <div className="grid grid-cols-2 gap-1.5">
          {[
            { value: '', label: 'Vse' },
            { value: 'sreality', label: 'Sreality' },
            { value: 'bezrealitky', label: 'Bezrealitky' },
            { value: 'idnes', label: 'iDNES' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => update('source', value)}
              className={`px-2 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                (filters.source || '') === value
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Sort */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Razeni</label>
        <select
          value={filters.sort || 'newest'}
          onChange={(e) => update('sort', e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
        >
          <option value="newest">Nejnovejsi</option>
          <option value="price_asc">Cena vzestupne</option>
          <option value="price_desc">Cena sestupne</option>
          <option value="size_asc">Plocha vzestupne</option>
          <option value="size_desc">Plocha sestupne</option>
        </select>
      </div>
    </div>
  );
}

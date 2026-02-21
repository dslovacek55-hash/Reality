'use client';

import { useStats } from '@/hooks/useProperties';

export default function StatsBar() {
  const { stats, isLoading } = useStats();

  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-20 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    { label: 'Aktivnich inzeratu', value: stats.total_active.toLocaleString('cs-CZ'), color: 'text-blue-600', bg: 'bg-blue-50', icon: '🏠' },
    { label: 'Novych dnes', value: stats.new_today.toLocaleString('cs-CZ'), color: 'text-green-600', bg: 'bg-green-50', icon: '✨' },
    { label: 'Poklesu cen', value: stats.price_drops_today.toLocaleString('cs-CZ'), color: 'text-orange-600', bg: 'bg-orange-50', icon: '📉' },
    { label: 'Odstranenych', value: stats.removed_today.toLocaleString('cs-CZ'), color: 'text-red-600', bg: 'bg-red-50', icon: '🗑' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {statCards.map((card) => (
        <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-2 mb-1">
            <span className={`${card.bg} ${card.color} w-8 h-8 rounded-lg flex items-center justify-center text-sm`}>
              {card.icon}
            </span>
            <span className="text-sm text-gray-500">{card.label}</span>
          </div>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
      {stats.by_source && Object.keys(stats.by_source).length > 0 && (
        <div className="col-span-2 md:col-span-4 flex flex-wrap gap-2">
          {Object.entries(stats.by_source).map(([source, count]) => (
            <span key={source} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
              {source}: {count.toLocaleString('cs-CZ')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

'use client';

import Link from 'next/link';
import type { Property, AvgPriceM2 } from '@/lib/types';
import { SOURCE_COLORS, formatPrice, timeAgo } from '@/lib/utils';

interface Props {
  property: Property;
  avgPriceM2?: AvgPriceM2;
  isFavorite?: boolean;
  onToggleFavorite?: (id: number) => void;
}

function PriceBadge({ label, color, icon }: { label: string; color: string; icon?: 'up' | 'down' }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {icon === 'down' && (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
      )}
      {icon === 'up' && (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
      )}
      {label}
    </span>
  );
}

function getDiffInfo(pricePerM2: number, avgPrice: number) {
  const pct = Math.round(((pricePerM2 - avgPrice) / avgPrice) * 100);
  if (pct < -5) return { label: `${pct}%`, color: 'text-green-600 bg-green-50', icon: 'down' as const };
  if (pct > 5) return { label: `+${pct}%`, color: 'text-red-600 bg-red-50', icon: 'up' as const };
  return { label: 'prumer', color: 'text-gray-600 bg-gray-100', icon: undefined };
}

export default function PropertyCard({ property, avgPriceM2, isFavorite, onToggleFavorite }: Props) {
  const imgSrc = property.images?.[0];
  const pricePerM2 = property.price && property.size_m2 && property.size_m2 > 0
    ? Math.round(property.price / property.size_m2)
    : null;

  // Internal avg comparison (disposition-specific preferred, then city-wide)
  const internalAvg = avgPriceM2?.by_disposition?.avg_price_m2 || avgPriceM2?.avg_price_m2;
  const internalCount = avgPriceM2?.by_disposition?.count || avgPriceM2?.count;
  const internalDiff = pricePerM2 && internalAvg && internalAvg > 0
    ? getDiffInfo(pricePerM2, internalAvg)
    : null;

  // CZSO external reference
  const czsoDiff = pricePerM2 && avgPriceM2?.czso_price_m2 && avgPriceM2.czso_price_m2 > 0
    ? getDiffInfo(pricePerM2, avgPriceM2.czso_price_m2)
    : null;

  return (
    <div className="relative group">
      {/* Favorite button */}
      {onToggleFavorite && (
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleFavorite(property.id);
          }}
          className="absolute top-2 right-2 z-10 p-1.5 rounded-full bg-white/80 backdrop-blur-sm hover:bg-white transition-colors shadow-sm"
          aria-label={isFavorite ? 'Odebrat z oblibenych' : 'Pridat do oblibenych'}
        >
          <svg
            className={`w-5 h-5 transition-colors ${isFavorite ? 'text-red-500 fill-red-500' : 'text-gray-400 hover:text-red-400'}`}
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            fill={isFavorite ? 'currentColor' : 'none'}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </button>
      )}

      <Link href={`/properties/${property.id}`} className="block">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all hover:-translate-y-0.5">
          <div className="relative h-48 bg-gray-100">
            {imgSrc ? (
              <img
                src={imgSrc}
                alt={property.title || 'Property'}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
            )}
            <div className="absolute top-2 left-2 flex gap-1.5">
              <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${SOURCE_COLORS[property.source] || 'bg-gray-100 text-gray-700'}`}>
                {property.source}
              </span>
              {property.transaction_type && (
                <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${property.transaction_type === 'pronajem' ? 'bg-purple-100 text-purple-700' : 'bg-indigo-100 text-indigo-700'}`}>
                  {property.transaction_type === 'prodej' ? 'Prodej' : 'Pronajem'}
                </span>
              )}
            </div>
            <div className="absolute bottom-2 right-2">
              <span className="text-xs text-white bg-black/50 px-2 py-0.5 rounded-md backdrop-blur-sm">
                {timeAgo(property.first_seen_at)}
              </span>
            </div>
          </div>
          <div className="p-4">
            <div className="flex items-start justify-between gap-2 mb-1">
              <p className="text-lg font-bold text-primary-600">{formatPrice(property.price)}</p>
              {pricePerM2 && (
                <span className="text-xs text-gray-500 whitespace-nowrap mt-1">
                  {new Intl.NumberFormat('cs-CZ').format(pricePerM2)} CZK/m²
                </span>
              )}
            </div>

            {/* Price comparison badges */}
            {(internalDiff || czsoDiff) && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {internalDiff && (
                  <PriceBadge
                    label={`${internalDiff.label} lokalita`}
                    color={internalDiff.color}
                    icon={internalDiff.icon}
                  />
                )}
                {czsoDiff && (
                  <PriceBadge
                    label={`${czsoDiff.label} ${avgPriceM2?.czso_region || 'ref.'}`}
                    color={czsoDiff.color}
                    icon={czsoDiff.icon}
                  />
                )}
              </div>
            )}

            <h3 className="text-sm font-medium text-gray-900 line-clamp-1 mb-2">
              {property.title || 'Bez nazvu'}
            </h3>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              {property.disposition && (
                <span className="flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                  {property.disposition}
                </span>
              )}
              {property.size_m2 && (
                <span className="flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                  {property.size_m2} m²
                </span>
              )}
              {property.city && (
                <span className="flex items-center gap-1 truncate">
                  <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  {property.city}
                </span>
              )}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
}

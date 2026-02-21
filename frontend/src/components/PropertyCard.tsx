'use client';

import Link from 'next/link';
import type { Property } from '@/lib/types';

const sourceColors: Record<string, string> = {
  sreality: 'bg-blue-100 text-blue-700',
  bazos: 'bg-yellow-100 text-yellow-700',
  bezrealitky: 'bg-green-100 text-green-700',
};

function formatPrice(price: number | null): string {
  if (!price) return 'Cena na dotaz';
  return new Intl.NumberFormat('cs-CZ', { style: 'currency', currency: 'CZK', maximumFractionDigits: 0 }).format(price);
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return 'Pred chvili';
  if (hours < 24) return `Pred ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Vcera';
  return `Pred ${days} dny`;
}

export default function PropertyCard({ property }: { property: Property }) {
  const imgSrc = property.images?.[0];

  return (
    <Link href={`/properties/${property.id}`} className="block">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all hover:-translate-y-0.5 group">
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
            <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${sourceColors[property.source] || 'bg-gray-100 text-gray-700'}`}>
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
          <p className="text-lg font-bold text-primary-600 mb-1">{formatPrice(property.price)}</p>
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
  );
}

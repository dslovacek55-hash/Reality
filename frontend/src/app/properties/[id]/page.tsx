'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Header from '@/components/Header';
import PriceChart from '@/components/PriceChart';
import { getProperty, getAvgPriceM2 } from '@/lib/api';
import { useFavorites } from '@/hooks/useFavorites';
import type { PropertyDetail, AvgPriceM2 } from '@/lib/types';
import { SOURCE_COLORS, formatPrice } from '@/lib/utils';

export default function PropertyDetailPage() {
  const params = useParams();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeImg, setActiveImg] = useState(0);
  const [cityAvg, setCityAvg] = useState<AvgPriceM2 | null>(null);
  const { isFavorite, toggleFavorite } = useFavorites();

  useEffect(() => {
    const id = Number(params.id);
    if (!id) return;

    getProperty(id)
      .then((p) => {
        setProperty(p);
        // Fetch average price with disposition for finer comparison + CZSO reference
        if (p.city) {
          getAvgPriceM2({
            property_type: p.property_type || undefined,
            transaction_type: p.transaction_type || undefined,
            disposition: p.disposition || undefined,
          }).then((avgMap) => {
            if (p.city && avgMap[p.city]) {
              setCityAvg(avgMap[p.city]);
            }
          }).catch(() => {});
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-screen-xl mx-auto px-4 py-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-64" />
            <div className="h-96 bg-gray-200 rounded-xl" />
            <div className="h-48 bg-gray-200 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-screen-xl mx-auto px-4 py-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Nemovitost nenalezena</h1>
          <Link href="/" className="text-primary-600 hover:text-primary-700">Zpet na dashboard</Link>
        </div>
      </div>
    );
  }

  const pricePerM2 = property.price && property.size_m2 && property.size_m2 > 0
    ? Math.round(property.price / property.size_m2)
    : null;

  // Internal average comparison (disposition-specific preferred)
  const internalAvg = cityAvg?.by_disposition?.avg_price_m2 || cityAvg?.avg_price_m2;
  const internalCount = cityAvg?.by_disposition?.count || cityAvg?.count;
  const internalLabel = cityAvg?.by_disposition ? `${property.disposition} v ${property.city}` : property.city || '';
  let internalDiffPct: number | null = null;
  if (pricePerM2 && internalAvg && internalAvg > 0) {
    internalDiffPct = Math.round(((pricePerM2 - internalAvg) / internalAvg) * 100);
  }

  // CZSO reference comparison
  let czsoDiffPct: number | null = null;
  if (pricePerM2 && cityAvg?.czso_price_m2 && cityAvg.czso_price_m2 > 0) {
    czsoDiffPct = Math.round(((pricePerM2 - cityAvg.czso_price_m2) / cityAvg.czso_price_m2) * 100);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
          <Link href="/" className="hover:text-primary-600">Dashboard</Link>
          <span>/</span>
          <span className="text-gray-900">{property.title || `#${property.id}`}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Images + Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image gallery */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="relative h-80 md:h-[450px] bg-gray-100">
                {property.images && property.images.length > 0 ? (
                  <img
                    src={property.images[activeImg] || property.images[0]}
                    alt={property.title || 'Property'}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <svg className="w-20 h-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                  </div>
                )}
                {/* Favorite button on image */}
                <button
                  onClick={() => toggleFavorite(property.id)}
                  className="absolute top-3 right-3 p-2 rounded-full bg-white/80 backdrop-blur-sm hover:bg-white transition-colors shadow"
                >
                  <svg
                    className={`w-6 h-6 transition-colors ${isFavorite(property.id) ? 'text-red-500 fill-red-500' : 'text-gray-400 hover:text-red-400'}`}
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                    fill={isFavorite(property.id) ? 'currentColor' : 'none'}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </button>
              </div>
              {property.images && property.images.length > 1 && (
                <div className="flex gap-2 p-3 overflow-x-auto">
                  {property.images.map((img, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveImg(i)}
                      className={`flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${
                        i === activeImg ? 'border-primary-500' : 'border-transparent'
                      }`}
                    >
                      <img src={img} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Description */}
            {property.description && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Popis</h3>
                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                  {property.description}
                </p>
              </div>
            )}

            {/* Price history chart */}
            <PriceChart history={property.price_history || []} />
          </div>

          {/* Right column - Info panel */}
          <div className="space-y-6">
            {/* Price card */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${SOURCE_COLORS[property.source] || 'bg-gray-100 text-gray-700'}`}>
                  {property.source}
                </span>
                <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${property.transaction_type === 'pronajem' ? 'bg-purple-100 text-purple-700' : 'bg-indigo-100 text-indigo-700'}`}>
                  {property.transaction_type === 'prodej' ? 'Prodej' : 'Pronajem'}
                </span>
                <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${property.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {property.status === 'active' ? 'Aktivni' : 'Odstranen'}
                </span>
              </div>

              <h1 className="text-xl font-bold text-gray-900 mb-2">
                {property.title || 'Bez nazvu'}
              </h1>

              <p className="text-3xl font-bold text-primary-600 mb-1">
                {formatPrice(property.price)}
              </p>
              {pricePerM2 && (
                <p className="text-sm text-gray-500 mb-3">
                  {new Intl.NumberFormat('cs-CZ').format(pricePerM2)} CZK/m²
                </p>
              )}

              {/* Price comparison: internal avg */}
              {internalDiffPct !== null && internalAvg && (
                <div className={`rounded-lg border p-3 ${
                  internalDiffPct < -5 ? 'text-green-700 bg-green-50 border-green-200' :
                  internalDiffPct > 5 ? 'text-red-700 bg-red-50 border-red-200' :
                  'text-gray-700 bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    {internalDiffPct < -5 && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
                    )}
                    {internalDiffPct > 5 && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
                    )}
                    <span className="text-sm font-medium">
                      {internalDiffPct < -5 ? `${internalDiffPct}%` : internalDiffPct > 5 ? `+${internalDiffPct}%` : 'Na prumeru'} vs. lokalita
                    </span>
                  </div>
                  <p className="text-xs opacity-75">
                    Prumer {internalLabel}: {new Intl.NumberFormat('cs-CZ').format(Math.round(internalAvg))} CZK/m²
                    ({internalCount} nemovitosti)
                  </p>
                </div>
              )}

              {/* Price comparison: CZSO reference */}
              {czsoDiffPct !== null && cityAvg?.czso_price_m2 && (
                <div className={`rounded-lg border p-3 ${
                  czsoDiffPct < -5 ? 'text-green-700 bg-green-50 border-green-200' :
                  czsoDiffPct > 5 ? 'text-red-700 bg-red-50 border-red-200' :
                  'text-gray-700 bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    {czsoDiffPct < -5 && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
                    )}
                    {czsoDiffPct > 5 && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
                    )}
                    <span className="text-sm font-medium">
                      {czsoDiffPct < -5 ? `${czsoDiffPct}%` : czsoDiffPct > 5 ? `+${czsoDiffPct}%` : 'Na prumeru'} vs. {cityAvg.czso_region}
                    </span>
                  </div>
                  <p className="text-xs opacity-75">
                    Prumer {cityAvg.czso_region}: {new Intl.NumberFormat('cs-CZ').format(cityAvg.czso_price_m2)} CZK/m²
                  </p>
                </div>
              )}
            </div>

            {/* Attributes */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Parametry</h3>
              <dl className="space-y-3">
                {[
                  { label: 'Dispozice', value: property.disposition },
                  { label: 'Plocha', value: property.size_m2 ? `${property.size_m2} m²` : null },
                  { label: 'Typ', value: property.property_type },
                  { label: 'Mesto', value: property.city },
                  { label: 'Okres', value: property.district },
                  { label: 'Adresa', value: property.address },
                  { label: 'Prvni videt', value: new Date(property.first_seen_at).toLocaleDateString('cs-CZ') },
                  { label: 'Posledne videt', value: new Date(property.last_seen_at).toLocaleDateString('cs-CZ') },
                ].filter(item => item.value).map(({ label, value }) => (
                  <div key={label} className="flex justify-between text-sm">
                    <dt className="text-gray-500">{label}</dt>
                    <dd className="text-gray-900 font-medium text-right">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Link to source */}
            {property.url && (
              <a
                href={property.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 transition-colors"
              >
                Zobrazit na {property.source}
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

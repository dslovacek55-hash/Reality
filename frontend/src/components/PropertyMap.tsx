'use client';

import { useEffect, useRef } from 'react';
import type { MapMarker } from '@/lib/types';

interface Props {
  markers: MapMarker[];
  isLoading: boolean;
}

function formatPrice(price: number | null): string {
  if (!price) return 'N/A';
  if (price >= 1_000_000) return `${(price / 1_000_000).toFixed(1)} M`;
  if (price >= 1_000) return `${(price / 1_000).toFixed(0)} tis.`;
  return price.toString();
}

export default function PropertyMap({ markers, isLoading }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const clusterRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapRef.current) return;

    const initMap = async () => {
      const L = (await import('leaflet')).default;
      await import('leaflet.markercluster');

      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
      }

      // Center on Czech Republic
      const map = L.map(mapRef.current!, {
        center: [49.8, 15.5],
        zoom: 8,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;

      // Create marker cluster group
      // @ts-ignore
      const cluster = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
      });
      clusterRef.current = cluster;
      map.addLayer(cluster);
    };

    initMap();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !clusterRef.current) return;

    const updateMarkers = async () => {
      const L = (await import('leaflet')).default;
      const cluster = clusterRef.current;
      cluster.clearLayers();

      markers.forEach((m) => {
        if (!m.lat || !m.lng) return;

        const icon = L.divIcon({
          className: 'custom-marker',
          html: `<div style="
            background: #2563eb;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            border: 2px solid white;
          ">${formatPrice(m.price)}</div>`,
          iconSize: [0, 0],
          iconAnchor: [30, 15],
        });

        const marker = L.marker([m.lat, m.lng], { icon });
        marker.bindPopup(`
          <div style="padding: 8px; min-width: 180px;">
            <p style="font-weight: 600; margin: 0 0 4px 0; font-size: 14px;">${m.title || 'Nemovitost'}</p>
            <p style="color: #2563eb; font-weight: 700; margin: 0 0 4px 0;">${m.price ? new Intl.NumberFormat('cs-CZ').format(m.price) + ' CZK' : 'Cena na dotaz'}</p>
            <p style="color: #666; font-size: 12px; margin: 0;">${m.disposition || ''} | ${m.source}</p>
            <a href="/properties/${m.id}" style="color: #2563eb; font-size: 12px; text-decoration: none;">Detail &rarr;</a>
          </div>
        `);
        cluster.addLayer(marker);
      });
    };

    updateMarkers();
  }, [markers]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="font-semibold text-gray-900 text-sm">Mapa nemovitosti</h2>
        <span className="text-xs text-gray-400">{markers.length} oznacenych</span>
      </div>
      <div ref={mapRef} style={{ height: '450px' }} className="relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-[1000]">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}

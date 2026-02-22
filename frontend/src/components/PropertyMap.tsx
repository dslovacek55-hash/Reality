'use client';

import { useEffect, useRef, useState } from 'react';
import type { MapMarker } from '@/lib/types';
import { formatPriceShort } from '@/lib/utils';

interface Props {
  markers: MapMarker[];
  isLoading: boolean;
}

export default function PropertyMap({ markers, isLoading }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const clusterRef = useRef<any>(null);
  const heatLayerRef = useRef<any>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);

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
          ">${formatPriceShort(m.price)}</div>`,
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

  // Heatmap layer toggle
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    if (showHeatmap) {
      // Hide cluster markers
      if (clusterRef.current) {
        map.removeLayer(clusterRef.current);
      }

      // Create simple CSS-based heatmap overlay using circles
      const updateHeatmap = async () => {
        const L = (await import('leaflet')).default;

        if (heatLayerRef.current) {
          map.removeLayer(heatLayerRef.current);
        }

        const heatGroup = L.layerGroup();

        // Calculate price range for color mapping
        const prices = markers
          .filter((m) => m.price && m.lat && m.lng)
          .map((m) => m.price!);
        if (prices.length === 0) return;

        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const range = maxPrice - minPrice || 1;

        markers.forEach((m) => {
          if (!m.lat || !m.lng || !m.price) return;

          // Normalize price to 0-1 range
          const normalized = (m.price - minPrice) / range;
          // Green (cheap) -> Yellow -> Red (expensive)
          const hue = 120 - normalized * 120; // 120=green, 0=red
          const color = `hsl(${hue}, 80%, 50%)`;

          const circle = L.circleMarker([m.lat, m.lng], {
            radius: 8,
            fillColor: color,
            fillOpacity: 0.6,
            stroke: true,
            color: color,
            weight: 1,
            opacity: 0.8,
          });

          circle.bindPopup(`
            <div style="padding: 4px; font-size: 12px;">
              <strong>${m.price ? new Intl.NumberFormat('cs-CZ').format(m.price) + ' CZK' : ''}</strong>
              <br/>${m.title || ''}
            </div>
          `);

          heatGroup.addLayer(circle);
        });

        heatLayerRef.current = heatGroup;
        map.addLayer(heatGroup);
      };

      updateHeatmap();
    } else {
      // Show cluster markers, hide heatmap
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
      if (clusterRef.current) {
        map.addLayer(clusterRef.current);
      }
    }
  }, [showHeatmap, markers]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="font-semibold text-gray-900 text-sm">Mapa nemovitosti</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border transition-colors ${
              showHeatmap
                ? 'bg-orange-50 border-orange-300 text-orange-700'
                : 'border-gray-200 text-gray-500 hover:bg-gray-50'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            </svg>
            Cenova mapa
          </button>
          <span className="text-xs text-gray-400">{markers.length} oznacenych</span>
        </div>
      </div>
      {showHeatmap && (
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-100 text-xs text-gray-500">
          <span className="inline-block w-3 h-3 rounded-full" style={{ background: 'hsl(120, 80%, 50%)' }} />
          Levne
          <span className="inline-block w-3 h-3 rounded-full" style={{ background: 'hsl(60, 80%, 50%)' }} />
          Prumer
          <span className="inline-block w-3 h-3 rounded-full" style={{ background: 'hsl(0, 80%, 50%)' }} />
          Drahe
        </div>
      )}
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

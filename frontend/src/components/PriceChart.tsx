'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { PriceHistoryEntry } from '@/lib/types';
import { formatPriceShort } from '@/lib/utils';

interface Props {
  history: PriceHistoryEntry[];
}

export default function PriceChart({ history }: Props) {
  if (history.length < 2) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Cenova historie</h3>
        <p className="text-sm text-gray-500 text-center py-8">
          Nedostatek dat pro zobrazeni grafu. Cenova historie bude dostupna po dalsich aktualizacich.
        </p>
      </div>
    );
  }

  const data = history.map((h) => ({
    date: new Date(h.recorded_at).toLocaleDateString('cs-CZ', { day: 'numeric', month: 'short' }),
    price: h.price,
    pricePerM2: h.price_per_m2,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Cenova historie</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <YAxis tickFormatter={formatPriceShort} tick={{ fontSize: 12 }} stroke="#9ca3af" width={60} />
          <Tooltip
            formatter={(value: number) => [
              new Intl.NumberFormat('cs-CZ').format(value) + ' CZK',
              'Cena',
            ]}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
            }}
          />
          <Line
            type="stepAfter"
            dataKey="price"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 4, fill: '#2563eb' }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

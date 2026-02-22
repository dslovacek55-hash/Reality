export const SOURCE_COLORS: Record<string, string> = {
  sreality: 'bg-blue-100 text-blue-700',
  bezrealitky: 'bg-green-100 text-green-700',
  idnes: 'bg-orange-100 text-orange-700',
};

export function formatPrice(price: number | null): string {
  if (!price) return 'Cena na dotaz';
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency: 'CZK',
    maximumFractionDigits: 0,
  }).format(price);
}

export function formatPriceShort(price: number | null): string {
  if (!price) return 'N/A';
  if (price >= 1_000_000) return `${(price / 1_000_000).toFixed(1)} M`;
  if (price >= 1_000) return `${(price / 1_000).toFixed(0)} tis.`;
  return price.toString();
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return 'Pred chvili';
  if (hours < 24) return `Pred ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Vcera';
  return `Pred ${days} dny`;
}

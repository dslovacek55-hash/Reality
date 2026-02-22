'use client';

import { useCallback, useEffect, useState } from 'react';
import { useFavoriteIds } from './useProperties';
import { addFavorite, removeFavorite } from '@/lib/api';

function getSessionId(): string {
  if (typeof window === 'undefined') return '';
  let id = localStorage.getItem('session_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('session_id', id);
  }
  return id;
}

export function useFavorites() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  const { favoriteIds, mutate } = useFavoriteIds(sessionId);

  const toggleFavorite = useCallback(
    async (propertyId: number) => {
      if (!sessionId) return;
      const isFav = favoriteIds.includes(propertyId);

      // Optimistic update
      const newIds = isFav
        ? favoriteIds.filter((id) => id !== propertyId)
        : [...favoriteIds, propertyId];
      mutate(newIds, false);

      try {
        if (isFav) {
          await removeFavorite(sessionId, propertyId);
        } else {
          await addFavorite(sessionId, propertyId);
        }
        mutate();
      } catch {
        mutate(); // Revert on error
      }
    },
    [sessionId, favoriteIds, mutate]
  );

  const isFavorite = useCallback(
    (propertyId: number) => favoriteIds.includes(propertyId),
    [favoriteIds]
  );

  return { favoriteIds, toggleFavorite, isFavorite, sessionId };
}

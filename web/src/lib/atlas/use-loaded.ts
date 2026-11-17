"use client";

import { useEffect, useState } from "react";

/**
 * Load something once per key. Returns null until the value for the current key has
 * arrived, so a stale value for a previous key is never shown.
 */
export function useLoaded<T>(loader: (() => Promise<T>) | null, key: string): T | null {
  const [state, setState] = useState<{ key: string; value: T } | null>(null);
  useEffect(() => {
    if (!loader) {
      return;
    }
    let cancelled = false;
    loader()
      .then((value) => {
        if (!cancelled) {
          setState({ key, value });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
    // The key identifies the loader; loader functions are recreated on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state?.key === key ? state.value : null;
}

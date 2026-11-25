// ── usePagination ─────────────────────────────────────────
// Paginates an array and provides page navigation controls.

import { useState, useMemo } from 'react';

/**
 * @template T
 * @param {T[]} data - full data array
 * @param {number} [pageSize=8] - items per page
 * @returns {{ page: number, totalPages: number, paginatedData: T[], goTo: (n: number) => void, prev: () => void, next: () => void, setPageSize: (n: number) => void, pageSize: number }}
 */
export function usePagination(data, pageSize = 8) {
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(pageSize);

  const totalPages = Math.max(1, Math.ceil(data.length / size));

  const paginatedData = useMemo(() => {
    const start = (page - 1) * size;
    return data.slice(start, start + size);
  }, [data, page, size]);

  const goTo = (n) => setPage(Math.min(Math.max(1, n), totalPages));
  const prev = () => goTo(page - 1);
  const next = () => goTo(page + 1);

  const setPageSize = (n) => {
    setSize(n);
    setPage(1);
  };

  return { page, totalPages, paginatedData, goTo, prev, next, pageSize: size, setPageSize };
}

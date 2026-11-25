// ── useModal ──────────────────────────────────────────────
// Controls open/close state for a modal, plus an optional payload.

import { useState, useCallback } from 'react';

/**
 * @returns {{ isOpen: boolean, payload: any, open: (data?: any) => void, close: () => void }}
 */
export function useModal() {
  const [state, setState] = useState({ isOpen: false, payload: null });

  const open = useCallback((payload = null) => {
    setState({ isOpen: true, payload });
  }, []);

  const close = useCallback(() => {
    setState({ isOpen: false, payload: null });
  }, []);

  return {
    isOpen: state.isOpen,
    payload: state.payload,
    open,
    close,
  };
}

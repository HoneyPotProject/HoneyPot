
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...options.headers,
      ...(options.body instanceof FormData
        ? {}
        : { 'Content-Type': 'application/json' }),
    },
  });

  if (!response.ok) {
    let message = 'Something went wrong';

    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch {
      // Response was not JSON.
    }

    throw new Error(message);
  }

  if (response.status === 204) return null;

  return response.json();
}

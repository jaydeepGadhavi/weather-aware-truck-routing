/**
 * API service for communication with Django Backend.
 */

export async function analyzeRoutes(payload) {
  const response = await fetch('/api/routes/analyze/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || 'Failed to analyze routes');
  }

  return response.json();
}

export async function fetchFreightHubs() {
  const response = await fetch('/api/hubs/');
  if (!response.ok) {
    return [];
  }
  return response.json();
}

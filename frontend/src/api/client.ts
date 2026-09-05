import type { SearchResponse } from '../types/product'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function searchProducts(query: string): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!response.ok) {
    throw new Error(`Search failed with status ${response.status}`)
  }
  return response.json()
}


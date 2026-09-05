import type { ParsedQuery } from '../types/product'

const LABELS: Record<string, string> = {
  brand: 'Brand',
  model: 'Model',
  category: 'Category',
  gender: 'Gender',
  size: 'Size',
  color: 'Color',
  sku: 'SKU',
  max_price: 'Max price',
}

export default function ParsedQueryChips({ parsedQuery }: { parsedQuery: ParsedQuery }) {
  const entries = (Object.keys(LABELS) as (keyof typeof LABELS)[])
    .map((key) => {
      const raw = parsedQuery[key as keyof ParsedQuery]
      if (raw === null || raw === undefined) return null
      const value = key === 'max_price' ? `$${raw}` : String(raw)
      return { label: LABELS[key], value }
    })
    .filter((entry): entry is { label: string; value: string } => entry !== null)

  if (entries.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-slate-500">Understood as:</span>
      {entries.map((entry) => (
        <span
          key={entry.label}
          className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
        >
          <span className="font-medium">{entry.label}:</span> {entry.value}
        </span>
      ))}
      {parsedQuery.parse_method === 'ai' && (
        <span className="rounded-full bg-purple-100 px-3 py-1 text-sm text-purple-700">
          AI-assisted parsing
        </span>
      )}
    </div>
  )
}

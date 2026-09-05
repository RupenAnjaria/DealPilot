import type { SearchResponse } from '../types/product'
import { providerLabel } from '../utils/listings'

interface Props {
  response: SearchResponse
}

/** A 10-second-glance recap of the AI pipeline: understand → search → match → compare → recommend. */
export default function PipelineSummary({ response }: Props) {
  const { parsed_query, providers_searched, groups, ranking } = response
  const understood = [parsed_query.brand, parsed_query.model].filter(Boolean).join(' ') || 'your request'
  const bestDeal = groups.flatMap((g) => g.listings).find((l) => l.listing_id === ranking.best_deal_listing_id)
  const matchedCount = groups.length

  const steps = [
    { icon: '🧠', label: 'Understood', detail: understood },
    { icon: '🏬', label: 'Searched', detail: `${providers_searched.length} retailers` },
    {
      icon: '🔗',
      label: 'Matched',
      detail: matchedCount > 0 ? `${matchedCount} product${matchedCount === 1 ? '' : 's'}` : 'no matches',
    },
    { icon: '⚖️', label: 'Compared', detail: 'true delivered cost' },
    { icon: '🏆', label: 'Recommended', detail: bestDeal ? providerLabel(bestDeal.provider) : '—' },
  ]

  return (
    <ol className="flex w-full flex-wrap items-center gap-x-2 gap-y-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-slate-300 sm:text-sm">
      {steps.map((step, index) => (
        <li key={step.label} className="flex items-center gap-2">
          {index > 0 && <span className="text-slate-600">→</span>}
          <span className="flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-1">
            <span aria-hidden="true">{step.icon}</span>
            <span className="font-semibold text-white">{step.label}:</span>
            <span>{step.detail}</span>
          </span>
        </li>
      ))}
    </ol>
  )
}

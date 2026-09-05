import type { SearchResponse } from '../types/product'
import MatchingSummary from './MatchingSummary'
import ParsedQueryChips from './ParsedQueryChips'
import ProviderSelectionList from './ProviderSelectionList'

export default function SearchInsights({ response }: { response: SearchResponse }) {
  return (
    <details className="group rounded-xl border border-slate-200 bg-white shadow-sm">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-3 text-sm font-semibold text-slate-700">
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true">🧭</span> How DealPilot searched
        </span>
        <span className="text-slate-400 transition group-open:rotate-180">⌄</span>
      </summary>
      <div className="space-y-5 border-t border-slate-100 px-5 py-4">
        <div>
          <h4 className="mb-2 text-sm font-semibold text-slate-700">🧠 Interpreted product</h4>
          <ParsedQueryChips parsedQuery={response.parsed_query} />
        </div>
        <ProviderSelectionList selections={response.provider_selection} />
        <MatchingSummary groups={response.groups} />
      </div>
    </details>
  )
}

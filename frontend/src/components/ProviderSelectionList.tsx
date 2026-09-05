import type { ProviderSelection } from '../types/product'
import { providerLabel } from '../utils/listings'

export default function ProviderSelectionList({ selections }: { selections: ProviderSelection[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-700">🏬 Providers searched</h4>
      <ul className="mt-2 space-y-2">
        {selections
          .slice()
          .sort((a, b) => a.priority - b.priority)
          .map((selection) => (
            <li key={selection.provider} className="flex items-start gap-3 text-sm">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[11px] font-bold text-slate-600">
                {selection.priority}
              </span>
              <div>
                <span className="font-medium text-slate-900">{providerLabel(selection.provider)}</span>
                <p className="text-slate-500">{selection.reason}</p>
              </div>
            </li>
          ))}
      </ul>
    </div>
  )
}

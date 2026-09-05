import type { ProductGroup } from '../types/product'
import { confidencePercent } from '../utils/listings'

export default function MatchingSummary({ groups }: { groups: ProductGroup[] }) {
  if (groups.length === 0) return null

  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-700">🔗 Matching information</h4>
      <ul className="mt-2 space-y-2">
        {groups.map((group) => (
          <li key={group.group_id} className="text-sm">
            <span className="font-medium text-slate-900">{group.canonical_title}</span>{' '}
            <span className="text-slate-500">
              — {group.listings.length} listing{group.listings.length === 1 ? '' : 's'} matched at{' '}
              {confidencePercent(group.match_confidence)} confidence ({group.match_method})
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

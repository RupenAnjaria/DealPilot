import type { ProductGroup, ProviderListing, RankingResult } from '../types/product'
import { availabilityLabel, availabilityStyle, confidencePercent, formatMoney, providerLabel } from '../utils/listings'

interface Props {
  listing: ProviderListing
  group: ProductGroup | undefined
  ranking: RankingResult
}

export default function BestDealCard({ listing, group, ranking }: Props) {
  const confidence = group?.match_confidence ?? listing.match_confidence

  return (
    <div className="relative overflow-hidden rounded-2xl border border-emerald-400/40 bg-gradient-to-br from-emerald-500/10 via-slate-900 to-slate-900 p-6 shadow-xl shadow-emerald-950/40 ring-1 ring-emerald-400/20 sm:p-8">
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400 px-3 py-1 text-xs font-bold uppercase tracking-wide text-slate-900">
        🏆 Best Deal
      </span>

      <div className="mt-4 flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-white sm:text-3xl">{providerLabel(listing.provider)}</h2>
        <p className="text-slate-300">{listing.title}</p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat icon="💵" label="Item price" value={formatMoney(listing.price)} />
        <Stat icon="🚚" label="Shipping" value={listing.shipping === 0 ? 'Free' : formatMoney(listing.shipping)} />
        <Stat icon="💰" label="Total delivered" value={formatMoney(listing.total_price)} highlight />
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-400">📦 Availability</div>
          <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${availabilityStyle(listing.availability)}`}>
            {availabilityLabel(listing.availability)}
          </span>
        </div>
      </div>

      {group && (
        <p className="mt-4 text-xs text-slate-400">
          🔗 Match confidence: <span className="font-semibold text-slate-200">{confidencePercent(confidence)}</span>{' '}
          ({group.listings.length} retailer{group.listings.length === 1 ? '' : 's'} matched
          {group.match_method === 'ai' ? ' via AI' : ' deterministically'})
        </p>
      )}

      <div className="mt-5 rounded-xl bg-white/5 p-4 text-sm leading-relaxed text-slate-200">
        <span className="font-semibold text-white">💡 Why DealPilot picked this: </span>
        {ranking.explanation}
      </div>
    </div>
  )
}

function Stat({ icon, label, value, highlight }: { icon: string; label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-400">
        <span aria-hidden="true">{icon}</span> {label}
      </div>
      <div className={highlight ? 'text-xl font-bold text-emerald-300' : 'text-lg font-semibold text-white'}>
        {value}
      </div>
    </div>
  )
}

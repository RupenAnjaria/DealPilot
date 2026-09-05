import type { ProviderListing, RankingResult } from '../types/product'
import { availabilityLabel, availabilityStyle, formatMoney, providerLabel } from '../utils/listings'

interface Props {
  listing: ProviderListing
  ranking: RankingResult
  bestDealTotal: number
}

export default function AlternativeCard({ listing, ranking, bestDealTotal }: Props) {
  const isCheapest = listing.listing_id === ranking.cheapest_listing_id
  const isOfficial = listing.listing_id === ranking.official_listing_id
  const delta = listing.total_price - bestDealTotal

  return (
    <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div>
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-semibold text-slate-900">{providerLabel(listing.provider)}</h3>
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${availabilityStyle(listing.availability)}`}>
            {availabilityLabel(listing.availability)}
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-500">{listing.title}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {isCheapest && <Tag label="Cheapest" style="bg-emerald-100 text-emerald-800" />}
          {isOfficial && <Tag label="Official store" style="bg-amber-100 text-amber-800" />}
        </div>
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div className="text-xs text-slate-500">
          {formatMoney(listing.price)} + {listing.shipping === 0 ? 'free shipping' : `${formatMoney(listing.shipping)} shipping`}
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-slate-900">{formatMoney(listing.total_price)}</div>
          {delta > 0.005 && <div className="text-[11px] text-slate-400">+{formatMoney(delta)} vs best deal</div>}
        </div>
      </div>
    </div>
  )
}

function Tag({ label, style }: { label: string; style: string }) {
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${style}`}>{label}</span>
}


import type { ProviderListing, RankingResult } from '../types/product'
import AlternativeCard from './AlternativeCard'

interface Props {
  listings: ProviderListing[]
  ranking: RankingResult
  bestDealTotal: number
}

export default function AlternativesList({ listings, ranking, bestDealTotal }: Props) {
  if (listings.length === 0) return null

  return (
    <div>
      <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-slate-500">
        <span aria-hidden="true">🛒</span> Other retailers ({listings.length})
      </h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {listings.map((listing) => (
          <AlternativeCard key={listing.listing_id} listing={listing} ranking={ranking} bestDealTotal={bestDealTotal} />
        ))}
      </div>
    </div>
  )
}


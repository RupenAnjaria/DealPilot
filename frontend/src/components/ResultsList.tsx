import type { SearchResponse } from '../types/product'
import { allListingsSortedByTotalPrice, findGroup, findListing } from '../utils/listings'
import AlternativesList from './AlternativesList'
import BestDealCard from './BestDealCard'
import PipelineSummary from './PipelineSummary'
import SearchInsights from './SearchInsights'

export default function ResultsList({ response }: { response: SearchResponse }) {
  const { groups, ranking } = response
  const bestDealListing = findListing(groups, ranking.best_deal_listing_id)

  if (!bestDealListing) {
    return (
      <div className="w-full max-w-4xl animate-[fadeIn_0.3s_ease-out] space-y-6">
        <PipelineSummary response={response} />
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-200">
          <div className="text-3xl">🔍</div>
          <p className="mt-3 font-semibold text-white">No matching products found</p>
          <p className="mt-1 text-sm text-slate-400">{ranking.explanation}</p>
        </div>
        <SearchInsights response={response} />
      </div>
    )
  }

  const bestDealGroup = findGroup(groups, ranking.best_deal_listing_id)
  const alternatives = allListingsSortedByTotalPrice(groups).filter(
    (listing) => listing.listing_id !== bestDealListing.listing_id,
  )

  return (
    <div className="w-full max-w-4xl animate-[fadeIn_0.3s_ease-out] space-y-6">
      <PipelineSummary response={response} />
      <BestDealCard listing={bestDealListing} group={bestDealGroup} ranking={ranking} />
      <AlternativesList listings={alternatives} ranking={ranking} bestDealTotal={bestDealListing.total_price} />
      <SearchInsights response={response} />
    </div>
  )
}



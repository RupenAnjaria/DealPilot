export type Availability = 'in_stock' | 'out_of_stock' | 'limited'

export interface ParsedQuery {
  raw_query: string
  brand: string | null
  model: string | null
  category: string | null
  gender: string | null
  size: string | null
  color: string | null
  sku: string | null
  max_price: number | null
  keywords: string[]
  parse_method: 'rule_based' | 'ai'
}

export interface ProviderListing {
  listing_id: string
  provider: string
  title: string
  brand: string | null
  model: string | null
  sku: string | null
  category: string | null
  gender: string | null
  size: string | null
  color: string | null
  price: number
  shipping: number
  total_price: number
  currency: string
  availability: Availability
  product_url: string
  official_store: boolean
  match_confidence: number
  rating: number | null
}

export interface ProductGroup {
  group_id: string
  canonical_title: string
  listings: ProviderListing[]
  match_confidence: number
  match_method: 'deterministic' | 'ai'
}

export interface DecisionFacts {
  cheapest_item_listing_id: string | null
  cheapest_item_price: number | null
  cheapest_listing_id: string | null
  cheapest_total: number | null
  best_deal_listing_id: string | null
  best_deal_total: number | null
  best_deal_reason: string | null
  official_listing_id: string | null
  official_total: number | null
  price_delta_vs_cheapest: number | null
  shipping_included: boolean
  attributes_matched: string[]
}

export interface RankingResult {
  cheapest_listing_id: string | null
  best_deal_listing_id: string | null
  official_listing_id: string | null
  decision_facts: DecisionFacts
  explanation: string
}

export interface ProviderSelection {
  provider: string
  priority: number
  reason: string
}

export interface SearchResponse {
  parsed_query: ParsedQuery
  provider_selection: ProviderSelection[]
  providers_searched: string[]
  groups: ProductGroup[]
  ranking: RankingResult
}

export interface ProviderInfo {
  name: string
}

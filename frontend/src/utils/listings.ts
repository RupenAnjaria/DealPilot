import type { Availability, ProductGroup, ProviderListing } from '../types/product'

export function findListing(groups: ProductGroup[], listingId: string | null): ProviderListing | undefined {
  if (!listingId) return undefined
  for (const group of groups) {
    const match = group.listings.find((listing) => listing.listing_id === listingId)
    if (match) return match
  }
  return undefined
}

export function findGroup(groups: ProductGroup[], listingId: string | null): ProductGroup | undefined {
  if (!listingId) return undefined
  return groups.find((group) => group.listings.some((listing) => listing.listing_id === listingId))
}

export function allListingsSortedByTotalPrice(groups: ProductGroup[]): ProviderListing[] {
  return groups
    .flatMap((group) => group.listings)
    .slice()
    .sort((a, b) => a.total_price - b.total_price)
}

export function formatMoney(value: number): string {
  return `$${value.toFixed(2)}`
}

export function providerLabel(provider: string): string {
  return provider.charAt(0).toUpperCase() + provider.slice(1)
}

export function confidencePercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

const AVAILABILITY_LABELS: Record<Availability, string> = {
  in_stock: 'In stock',
  limited: 'Limited stock',
  out_of_stock: 'Out of stock',
}

const AVAILABILITY_STYLES: Record<Availability, string> = {
  in_stock: 'bg-emerald-100 text-emerald-800',
  limited: 'bg-amber-100 text-amber-800',
  out_of_stock: 'bg-red-100 text-red-700',
}

export function availabilityLabel(availability: Availability): string {
  return AVAILABILITY_LABELS[availability]
}

export function availabilityStyle(availability: Availability): string {
  return AVAILABILITY_STYLES[availability]
}

import { request } from './request'
import { cachedFetch } from '@/utils/memoryCache'
import { QUOTA_TTL_MS } from './cacheConfig'
import type { QuotaLedgerItem, QuotaSummary } from '@/types'

export interface QuotaEstimateResponse {
  estimated_units: number
  price_cents: number
  plan_code: string
}

export function getQuotaSummary(options?: { force?: boolean }) {
  return cachedFetch(
    'quota:summary',
    QUOTA_TTL_MS,
    () => request<QuotaSummary>({ url: '/quota/summary' }),
    options,
  )
}

export function estimateQuota(payload: {
  category_id?: string
  style_id?: string
  source_asset_id?: string
  prompt_hint?: string
}) {
  return request<QuotaEstimateResponse>({
    url: '/quota/estimate',
    method: 'POST',
    data: payload,
  })
}

export function listQuotaLedger(offset = 0, limit = 100) {
  return request<QuotaLedgerItem[]>({
    url: `/quota/admin/quota-ledger?offset=${offset}&limit=${limit}`,
  })
}

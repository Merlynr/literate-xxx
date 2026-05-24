import { request } from './request'
import type { QuotaLedgerItem, QuotaSummary } from '@/types'

export interface QuotaEstimateResponse {
  estimated_units: number
  price_cents: number
  plan_code: string
}

export function getQuotaSummary() {
  return request<QuotaSummary>({ url: '/quota/summary' })
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

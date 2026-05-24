import { request } from '../request'
import type { PromoRule, Term } from '@/types'

export function listTerms(includeInactive = true) {
  const active = includeInactive ? '' : 'is_active=true&'
  return request<Term[]>({ url: `/terms/?${active}limit=500` })
}

export function createTerm(data: {
  type: string
  content: string
  weight?: number
  sort_order?: number
  scope?: Record<string, unknown> | null
  is_active?: boolean
}) {
  return request<Term>({ url: '/terms/', method: 'POST', data })
}

export function updateTerm(
  id: string,
  data: Partial<{
    type: string
    content: string
    weight: number
    sort_order: number
    scope: Record<string, unknown> | null
    is_active: boolean
  }>,
) {
  return request<Term>({ url: `/terms/${id}`, method: 'PUT', data })
}

export function deleteTerm(id: string) {
  return request<void>({ url: `/terms/${id}`, method: 'DELETE' })
}

export function listPromoRules(includeInactive = true) {
  const active = includeInactive ? '' : 'is_active=true&'
  return request<PromoRule[]>({ url: `/promo-rules/?${active}limit=500` })
}

export function createPromoRule(data: {
  name: string
  slot_template?: Record<string, unknown> | null
  term_selection_strategy?: string
  aspect_ratio?: string
  watermark_config?: Record<string, unknown> | null
  is_active?: boolean
}) {
  return request<PromoRule>({ url: '/promo-rules/', method: 'POST', data })
}

export function updatePromoRule(
  id: string,
  data: Partial<{
    name: string
    slot_template: Record<string, unknown> | null
    term_selection_strategy: string
    aspect_ratio: string
    watermark_config: Record<string, unknown> | null
    is_active: boolean
  }>,
) {
  return request<PromoRule>({ url: `/promo-rules/${id}`, method: 'PUT', data })
}

export function deletePromoRule(id: string) {
  return request<void>({ url: `/promo-rules/${id}`, method: 'DELETE' })
}

import { request } from '../request'
import type { PricingPlan } from '@/types'

export function listPricingPlans() {
  return request<PricingPlan[]>({ url: '/admin/pricing-plans' })
}

export function createPricingPlan(data: {
  plan_code: string
  plan_name: string
  quota_units?: number
  price_cents?: number
  valid_days?: number
  is_active?: boolean
  sort_order?: number
}) {
  return request<PricingPlan>({ url: '/admin/pricing-plans', method: 'POST', data })
}

export function updatePricingPlan(
  id: number,
  data: Partial<{
    plan_name: string
    quota_units: number
    price_cents: number
    valid_days: number
    is_active: boolean
    sort_order: number
  }>,
) {
  return request<PricingPlan>({ url: `/admin/pricing-plans/${id}`, method: 'PUT', data })
}

export function deletePricingPlan(id: number) {
  return request<void>({ url: `/admin/pricing-plans/${id}`, method: 'DELETE' })
}

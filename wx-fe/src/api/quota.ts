import request from './request'
import type { QuotaSummary } from '@/types/generation'

export async function getQuotaSummary(): Promise<QuotaSummary> {
  return request<QuotaSummary>({
    url: '/quota/summary',
    method: 'GET',
  }).then((res) => res.data)
}

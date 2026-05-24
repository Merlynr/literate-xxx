import { request } from './request'
import type { PrivacyStatus } from '@/types'

export function getPrivacyStatus() {
  return request<PrivacyStatus>({ url: '/privacy/agreement-status' })
}

export function acceptPrivacy() {
  return request<{ has_privacy_agreement: boolean; privacy_accepted_at: string }>({
    url: '/privacy/accept',
    method: 'POST',
    data: { consent_type: 'generation', source: 'web' },
  })
}

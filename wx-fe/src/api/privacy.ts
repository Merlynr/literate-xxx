import request from './request'
import type { PrivacyStatus } from '@/types/generation'

export async function getPrivacyStatus(): Promise<PrivacyStatus> {
  return request<PrivacyStatus>({
    url: '/privacy/agreement-status',
    method: 'GET',
  }).then((res) => res.data)
}

export async function acceptPrivacyAgreement(): Promise<PrivacyStatus> {
  return request<PrivacyStatus>({
    url: '/privacy/accept',
    method: 'POST',
    data: { consent_type: 'generation', source: 'generation' },
  }).then((res) => res.data)
}

import { request, uploadFileDirect } from './request'
import type { Category, GenerationAsset, GenerationHistoryItem, GenerationJob, Style } from '@/types'

export function listCategories() {
  return request<Category[]>({ url: '/categories/?is_active=true&limit=100' })
}

export function listStyles() {
  return request<Style[]>({ url: '/styles/?is_active=true&limit=100' })
}

export async function uploadSourceAsset(file: File): Promise<GenerationAsset> {
  const direct = await uploadFileDirect(file)
  return request<GenerationAsset>({
    url: '/generation-assets/confirm',
    method: 'POST',
    data: {
      oss_key: direct.key,
      filename: direct.filename,
      content_type: direct.content_type,
      size_bytes: direct.size_bytes,
      asset_role: 'source',
    },
  })
}

export function createJob(payload: {
  client_request_id: string
  source_asset_id: string
  category_id?: string
  style_id?: string
  prompt_hint?: string
}) {
  return request<GenerationJob>({
    url: '/generation-jobs',
    method: 'POST',
    data: payload,
  })
}

export function getJob(jobId: string) {
  return request<GenerationJob>({ url: `/generation-jobs/${jobId}` })
}

export function listHistory(offset = 0, limit = 50, status?: string) {
  const statusQuery = status ? `&status=${encodeURIComponent(status)}` : ''
  return request<GenerationHistoryItem[]>({
    url: `/generation-history?offset=${offset}&limit=${limit}${statusQuery}`,
  })
}

export function listCompletedHistory(offset = 0, limit = 50) {
  return listHistory(offset, limit, 'succeeded')
}

export function buildRequestId() {
  return `web-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`
}

import { request, uploadFileDirect } from './request'
import { cachedFetch } from '@/utils/memoryCache'
import {
  CATALOG_TTL_MS,
  COMPLETED_HISTORY_TTL_MS,
  HISTORY_TTL_MS,
  JOB_DONE_TTL_MS,
  historyCacheKey,
  jobCacheKey,
} from './cacheConfig'
import type { Category, GenerationAsset, GenerationHistoryItem, GenerationJob, Style } from '@/types'

export function listCategories(options?: { force?: boolean }) {
  return cachedFetch(
    'catalog:categories',
    CATALOG_TTL_MS,
    () => request<Category[]>({ url: '/categories/?is_active=true&limit=100' }),
    options,
  )
}

export function listStyles(options?: { force?: boolean }) {
  return cachedFetch(
    'catalog:styles',
    CATALOG_TTL_MS,
    () => request<Style[]>({ url: '/styles/?is_active=true&limit=100' }),
    options,
  )
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

export const MAX_SOURCE_ASSETS = 6

export function createJob(payload: {
  client_request_id: string
  source_asset_id?: string
  source_asset_ids?: string[]
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

export function getJob(jobId: string, options?: { force?: boolean; skipCache?: boolean }) {
  if (options?.skipCache) {
    return request<GenerationJob>({ url: `/generation-jobs/${jobId}` })
  }
  return cachedFetch(
    jobCacheKey(jobId),
    JOB_DONE_TTL_MS,
    () => request<GenerationJob>({ url: `/generation-jobs/${jobId}` }),
    options,
  )
}

export function listHistory(offset = 0, limit = 50, status?: string, options?: { force?: boolean }) {
  const key = historyCacheKey(offset, limit, status)
  return cachedFetch(
    key,
    HISTORY_TTL_MS,
    () => {
      const statusQuery = status ? `&status=${encodeURIComponent(status)}` : ''
      return request<GenerationHistoryItem[]>({
        url: `/generation-history?offset=${offset}&limit=${limit}${statusQuery}`,
      })
    },
    options,
  )
}

export function listCompletedHistory(offset = 0, limit = 50, options?: { force?: boolean }) {
  return cachedFetch(
    historyCacheKey(offset, limit, 'succeeded'),
    COMPLETED_HISTORY_TTL_MS,
    () => {
      const statusQuery = '&status=succeeded'
      return request<GenerationHistoryItem[]>({
        url: `/generation-history?offset=${offset}&limit=${limit}${statusQuery}`,
      })
    },
    options,
  )
}

export function buildRequestId() {
  return `web-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`
}

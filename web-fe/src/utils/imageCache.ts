import { cacheDeletePrefix } from './memoryCache'

interface ImageCacheEntry {
  blobUrl: string
  expiresAt: number
}

const imageStore = new Map<string, ImageCacheEntry>()
const imageInflight = new Map<string, Promise<string>>()

const DEFAULT_IMAGE_TTL_MS = 30 * 60 * 1000

function isHttpUrl(url: string) {
  return url.startsWith('http://') || url.startsWith('https://')
}

function revokeEntry(entry: ImageCacheEntry) {
  try {
    URL.revokeObjectURL(entry.blobUrl)
  } catch {
    /* ignore */
  }
}

export function imageCacheKey(jobId: string, role: 'source' | 'raw' | 'watermark' | 'preview') {
  return `img:${jobId}:${role}`
}

export function invalidateImageCache(key?: string) {
  if (!key) {
    for (const entry of imageStore.values()) revokeEntry(entry)
    imageStore.clear()
    imageInflight.clear()
    return
  }
  const entry = imageStore.get(key)
  if (entry) {
    revokeEntry(entry)
    imageStore.delete(key)
  }
}

export function invalidateImagesForJob(jobId: string) {
  cacheDeletePrefix(`img:${jobId}:`)
  for (const key of [...imageStore.keys()]) {
    if (key.startsWith(`img:${jobId}:`)) {
      const entry = imageStore.get(key)
      if (entry) revokeEntry(entry)
      imageStore.delete(key)
    }
  }
}

/**
 * 将远程图片转为 blob URL 并缓存，避免列表/切页时重复下载。
 * cacheKey 建议用 jobId+角色，避免预签名 URL 变更导致缓存失效。
 */
export async function getCachedImageSrc(
  url: string,
  cacheKey: string,
  options?: { force?: boolean; ttlMs?: number },
): Promise<string> {
  if (!url || !isHttpUrl(url)) return url

  const ttlMs = options?.ttlMs ?? DEFAULT_IMAGE_TTL_MS
  const key = cacheKey || url

  if (!options?.force) {
    const hit = imageStore.get(key)
    if (hit && Date.now() <= hit.expiresAt) return hit.blobUrl
    const pending = imageInflight.get(key)
    if (pending) return pending
  } else {
    invalidateImageCache(key)
  }

  const task = fetch(url, { mode: 'cors', credentials: 'omit' })
    .then(async (res) => {
      if (!res.ok) throw new Error(`图片加载失败 (${res.status})`)
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      const old = imageStore.get(key)
      if (old) revokeEntry(old)
      imageStore.set(key, { blobUrl, expiresAt: Date.now() + ttlMs })
      return blobUrl
    })
    .finally(() => {
      if (imageInflight.get(key) === task) imageInflight.delete(key)
    })

  imageInflight.set(key, task)
  return task
}

/** 生成成功后清理历史/额度等 API 缓存 */
export function invalidateAfterNewGeneration() {
  cacheDeletePrefix('history:')
  cacheDeletePrefix('quota:')
  cacheDeletePrefix('job:')
}

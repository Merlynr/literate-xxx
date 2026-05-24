interface CacheEntry<T> {
  value: T
  expiresAt: number
}

const store = new Map<string, CacheEntry<unknown>>()
const inflight = new Map<string, Promise<unknown>>()

export function cacheGet<T>(key: string): T | undefined {
  const entry = store.get(key)
  if (!entry) return undefined
  if (Date.now() > entry.expiresAt) {
    store.delete(key)
    return undefined
  }
  return entry.value as T
}

export function cacheSet<T>(key: string, value: T, ttlMs: number) {
  store.set(key, { value, expiresAt: Date.now() + ttlMs })
}

export function cacheDelete(key: string) {
  store.delete(key)
}

export function cacheDeletePrefix(prefix: string) {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) cacheDelete(key)
  }
}

export function cacheClear() {
  store.clear()
  inflight.clear()
}

/** 带 TTL 与并发去重的缓存读取 */
export async function cachedFetch<T>(
  key: string,
  ttlMs: number,
  fetcher: () => Promise<T>,
  options?: { force?: boolean },
): Promise<T> {
  if (!options?.force) {
    const hit = cacheGet<T>(key)
    if (hit !== undefined) return hit
    const pending = inflight.get(key)
    if (pending) return pending as Promise<T>
  }

  const task = fetcher()
    .then((value) => {
      cacheSet(key, value, ttlMs)
      return value
    })
    .finally(() => {
      if (inflight.get(key) === task) inflight.delete(key)
    })

  inflight.set(key, task)
  return task as Promise<T>
}

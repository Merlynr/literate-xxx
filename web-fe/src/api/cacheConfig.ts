/** 类目/风格目录 */
export const CATALOG_TTL_MS = 5 * 60 * 1000
/** 历史列表 */
export const HISTORY_TTL_MS = 30 * 1000
/** 已完成任务列表（变更较少） */
export const COMPLETED_HISTORY_TTL_MS = 60 * 1000
/** 任务详情（进行中短缓存，已完成长缓存） */
export const JOB_ACTIVE_TTL_MS = 3 * 1000
export const JOB_DONE_TTL_MS = 10 * 60 * 1000
/** 额度摘要 */
export const QUOTA_TTL_MS = 60 * 1000

export function historyCacheKey(offset: number, limit: number, status?: string) {
  return `history:${status || 'all'}:${offset}:${limit}`
}

export function jobCacheKey(jobId: string) {
  return `job:${jobId}`
}

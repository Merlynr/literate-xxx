import { invalidateImageCache } from './imageCache'

/** 用户强制刷新：清空图片 Blob，避免仍显示已 revoke 的旧 blob URL */
export function prepareForceRefresh() {
  invalidateImageCache()
}

import request, { getToken, BASE_URL } from './request'
import type {
  GenerationAssetConfirmPayload,
  GenerationAssetResponse,
  GenerationCategory,
  GenerationHistoryItem,
  GenerationJobCreatePayload,
  GenerationJobResponse,
  GenerationStyle,
  GenerationUploadPayload,
  LocalFileSelection,
  PresignUploadResponse,
} from '@/types/generation'

function getFileNameFromPath(filePath: string) {
  const segments = filePath.split(/[/\\]/)
  return segments[segments.length - 1] || `upload-${Date.now()}.jpg`
}

function getContentTypeFromName(fileName: string) {
  const lower = fileName.toLowerCase()
  if (lower.endsWith('.png')) return 'image/png'
  if (lower.endsWith('.webp')) return 'image/webp'
  if (lower.endsWith('.gif')) return 'image/gif'
  return 'image/jpeg'
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const wxBase64ToArrayBuffer = (globalThis as any)?.wx?.base64ToArrayBuffer
  if (typeof wxBase64ToArrayBuffer === 'function') {
    return wxBase64ToArrayBuffer(base64)
  }
  const clean = base64.replace(/\s/g, '').replace(/^data:.*;base64,/, '')
  const binary = atob(clean)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}

function isMiniProgramRuntime() {
  return typeof globalThis !== 'undefined' && !!(globalThis as any).wx
}

function parseJsonResponse<T>(payload: unknown): T {
  if (typeof payload === 'string') {
    return JSON.parse(payload) as T
  }
  return payload as T
}

async function readFileAsArrayBuffer(filePath: string): Promise<ArrayBuffer> {
  const fs = (uni as any).getFileSystemManager?.()
  if (!fs || typeof fs.readFile !== 'function') {
    throw new Error('当前运行环境不支持文件读取')
  }
  return await new Promise<ArrayBuffer>((resolve, reject) => {
    fs.readFile({
      filePath,
      encoding: 'base64',
      success: (res: { data: ArrayBuffer | string }) => {
        if (res.data instanceof ArrayBuffer) {
          resolve(res.data)
          return
        }
        if (typeof res.data === 'string' && res.data.length > 0) {
          resolve(base64ToArrayBuffer(res.data))
          return
        }
        reject(new Error('文件读取结果为空'))
      },
      fail: reject,
    })
  })
}

async function uploadFileViaBackend(
  filePath: string,
  filename: string,
  contentType: string,
): Promise<{ key: string; size_bytes: number }> {
  const token = getToken()
  return await new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}/uploads/direct`,
      filePath,
      name: 'file',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      formData: {
        filename,
        content_type: contentType,
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error((res.data as string) || `Direct upload failed: ${res.statusCode}`))
          return
        }
        try {
          resolve(parseJsonResponse<{ key: string; size_bytes: number }>(res.data))
        } catch (error) {
          reject(error)
        }
      },
      fail: reject,
    })
  })
}

export async function putFileToPresignedUrl(
  uploadUrl: string,
  filePath: string,
  contentType: string,
): Promise<void> {
  const payload = await readFileAsArrayBuffer(filePath)
  if (payload.byteLength === 0) {
    throw new Error('上传内容为空，已中止')
  }
  await new Promise<void>((resolve, reject) => {
    uni.request({
      url: uploadUrl,
      method: 'PUT',
      data: payload as ArrayBuffer,
      header: {
        'Content-Type': contentType,
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve()
          return
        }
        reject(new Error(`OSS upload failed: ${res.statusCode}`))
      },
      fail: reject,
    })
  })
}

export function buildGenerationRequestId(): string {
  return `gen-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`
}

export async function listGenerationCategories(): Promise<GenerationCategory[]> {
  return request<GenerationCategory[]>({
    url: '/categories/?is_active=true&limit=100',
    method: 'GET',
  }).then((res) => res.data)
}

export async function listGenerationStyles(): Promise<GenerationStyle[]> {
  return request<GenerationStyle[]>({
    url: '/styles/?is_active=true&limit=100',
    method: 'GET',
  }).then((res) => res.data)
}

export async function presignGenerationUpload(
  payload: GenerationUploadPayload,
): Promise<PresignUploadResponse> {
  const contentType = payload.content_type || getContentTypeFromName(payload.filename)
  return request<PresignUploadResponse>({
    url: '/uploads/presign',
    method: 'POST',
    data: {
      filename: payload.filename,
      content_type: contentType,
    },
  }).then((res) => res.data)
}

export async function confirmGenerationAsset(
  payload: GenerationAssetConfirmPayload,
): Promise<GenerationAssetResponse> {
  return request<GenerationAssetResponse>({
    url: '/generation-assets/confirm',
    method: 'POST',
    data: payload,
  }).then((res) => res.data)
}

export async function createGenerationJob(
  payload: GenerationJobCreatePayload,
): Promise<GenerationJobResponse> {
  return request<GenerationJobResponse>({
    url: '/generation-jobs',
    method: 'POST',
    data: payload,
  }).then((res) => res.data)
}

export async function getGenerationJob(jobId: string): Promise<GenerationJobResponse> {
  return request<GenerationJobResponse>({
    url: `/generation-jobs/${jobId}`,
    method: 'GET',
  }).then((res) => res.data)
}

export async function listGenerationHistory(offset = 0, limit = 20): Promise<GenerationHistoryItem[]> {
  return request<GenerationHistoryItem[]>({
    url: `/generation-history?offset=${offset}&limit=${limit}`,
    method: 'GET',
  }).then((res) => res.data)
}

export async function uploadGenerationAssetFromLocalPath(
  filePath: string,
  options?: {
    filename?: string
    contentType?: string
    assetRole?: string
    sizeBytes?: number
  },
): Promise<GenerationAssetResponse> {
  const filename = options?.filename || getFileNameFromPath(filePath)
  const contentType = options?.contentType || getContentTypeFromName(filename)
  if (isMiniProgramRuntime()) {
    const direct = await uploadFileViaBackend(filePath, filename, contentType)
    return await confirmGenerationAsset({
      oss_key: direct.key,
      filename,
      content_type: contentType,
      size_bytes: direct.size_bytes ?? options?.sizeBytes ?? null,
      asset_role: options?.assetRole || 'source',
    })
  }

  const presign = await presignGenerationUpload({
    filename,
    content_type: contentType,
  })
  await putFileToPresignedUrl(presign.upload_url, filePath, contentType)
  return await confirmGenerationAsset({
    oss_key: presign.key,
    filename,
    content_type: contentType,
    size_bytes: options?.sizeBytes ?? null,
    asset_role: options?.assetRole || 'source',
  })
}

export function buildGenerationLocalFile(filePath: string): LocalFileSelection {
  const name = getFileNameFromPath(filePath)
  return {
    path: filePath,
    name,
    type: getContentTypeFromName(name),
  }
}

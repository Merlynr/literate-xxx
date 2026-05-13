import request from './request'
import type {
  GenerationAssetConfirmPayload,
  GenerationAssetResponse,
  GenerationCategory,
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

async function readFileAsArrayBuffer(filePath: string): Promise<ArrayBuffer> {
  const fs = (uni as any).getFileSystemManager?.()
  if (!fs || typeof fs.readFile !== 'function') {
    throw new Error('当前运行环境不支持文件读取')
  }
  return await new Promise<ArrayBuffer>((resolve, reject) => {
    fs.readFile({
      filePath,
      encoding: 'binary',
      success: (res: { data: ArrayBuffer | string }) => {
        resolve((res.data as ArrayBuffer) || new ArrayBuffer(0))
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

export async function uploadGenerationAssetFromLocalPath(
  filePath: string,
  options?: {
    filename?: string
    contentType?: string
    assetRole?: string
  },
): Promise<GenerationAssetResponse> {
  const filename = options?.filename || getFileNameFromPath(filePath)
  const contentType = options?.contentType || getContentTypeFromName(filename)
  const presign = await presignGenerationUpload({
    filename,
    content_type: contentType,
  })
  await putFileToPresignedUrl(presign.upload_url, filePath, contentType)
  return await confirmGenerationAsset({
    oss_key: presign.key,
    filename,
    content_type: contentType,
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

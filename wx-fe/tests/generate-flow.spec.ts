import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useGenerationStore } from '@/stores/generation'

const mockApis = vi.hoisted(() => ({
  listGenerationCategories: vi.fn(),
  listGenerationStyles: vi.fn(),
  uploadGenerationAssetFromLocalPath: vi.fn(),
  createGenerationJob: vi.fn(),
  getGenerationJob: vi.fn(),
  buildGenerationRequestId: vi.fn(),
}))

vi.mock('@/api/generation', () => mockApis)

describe('generation flow', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockApis.listGenerationCategories.mockReset()
    mockApis.listGenerationStyles.mockReset()
    mockApis.uploadGenerationAssetFromLocalPath.mockReset()
    mockApis.createGenerationJob.mockReset()
    mockApis.getGenerationJob.mockReset()
    mockApis.buildGenerationRequestId.mockReset()
    mockApis.buildGenerationRequestId.mockReturnValue('gen-request-1')
    ;(globalThis as any).uni = {
      chooseImage: ({ success }: any) => {
        success({ tempFilePaths: ['temp/source.jpg'] })
      },
      previewImage: vi.fn(),
    }
  })

  it('uploads, creates a job, and captures result URLs', async () => {
    mockApis.listGenerationCategories.mockResolvedValue([
      { id: 'cat-1', category_code: 'potato', name: '土豆', sort_order: 1, is_active: true },
    ])
    mockApis.listGenerationStyles.mockResolvedValue([
      { id: 'style-1', name: '暖调海报', cover_image_url: 'https://example.com/style.jpg', rule_version: 1, sort_order: 1, is_active: true },
    ])
    mockApis.uploadGenerationAssetFromLocalPath.mockResolvedValue({
      asset_id: 'asset-1',
      tenant_id: 'tenant-1',
      job_id: null,
      asset_role: 'source',
      oss_bucket: 'xxzx-assets',
      oss_key: 'uploads/source.jpg',
      original_filename: 'source.jpg',
      content_type: 'image/jpeg',
      size_bytes: 123,
      sha256: 'abc',
      width: null,
      height: null,
      download_url: 'https://example.com/source.jpg',
      download_expires_in: 3600,
      created_at: '2026-05-13T00:00:00Z',
      updated_at: '2026-05-13T00:00:00Z',
    })
    mockApis.createGenerationJob.mockResolvedValue({
      job_id: 'job-1',
      tenant_id: 'tenant-1',
      client_request_id: 'gen-request-1',
      status: 'queued',
      provider: 'alibaba-dashscope',
      model_name: 'wan2.7-image',
      source_asset_id: 'asset-1',
      raw_result_asset_id: null,
      watermarked_result_asset_id: null,
      task_id: 'task-1',
      rule_snapshot: {},
      prompt_snapshot: {},
      request_snapshot: {},
      error_code: '',
      error_message: '',
      created_at: '2026-05-13T00:00:00Z',
      updated_at: '2026-05-13T00:00:00Z',
    })
    mockApis.getGenerationJob.mockResolvedValue({
      job_id: 'job-1',
      tenant_id: 'tenant-1',
      client_request_id: 'gen-request-1',
      status: 'succeeded',
      provider: 'alibaba-dashscope',
      model_name: 'wan2.7-image',
      source_asset_id: 'asset-1',
      raw_result_asset_id: 'raw-1',
      watermarked_result_asset_id: 'wm-1',
      task_id: 'task-1',
      rule_snapshot: {},
      prompt_snapshot: {},
      request_snapshot: {},
      error_code: '',
      error_message: '',
      raw_result_download_url: 'https://example.com/raw.jpg',
      watermarked_result_download_url: 'https://example.com/wm.jpg',
      created_at: '2026-05-13T00:00:00Z',
      updated_at: '2026-05-13T00:00:00Z',
    })

    const store = useGenerationStore()
    await store.loadCatalogs()
    expect(store.categories).toHaveLength(1)
    expect(store.styles).toHaveLength(1)

    await store.pickAndUploadSourceImage()
    expect(store.sourceAsset?.asset_id).toBe('asset-1')
    expect(store.sourcePreviewUrl).toBe('https://example.com/source.jpg')

    await store.startGeneration()
    expect(store.currentJob?.status).toBe('succeeded')
    expect(store.watermarkedResultUrl).toBe('https://example.com/wm.jpg')
    expect(store.rawResultUrl).toBe('https://example.com/raw.jpg')
    expect(store.stage).toBe('succeeded')
    expect(store.statusMessage).toBe('生成完成')
  })
})

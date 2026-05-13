import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  buildGenerationRequestId,
  createGenerationJob,
  getGenerationJob,
  listGenerationCategories,
  listGenerationStyles,
  uploadGenerationAssetFromLocalPath,
} from '@/api/generation'
import type {
  GenerationAssetResponse,
  GenerationCategory,
  GenerationJobResponse,
  GenerationStyle,
  LocalFileSelection,
} from '@/types/generation'

type GenerationStage = 'idle' | 'ready' | 'generating' | 'succeeded' | 'failed'

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function chooseImage(): Promise<LocalFileSelection | null> {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const filePath = res.tempFilePaths?.[0]
        if (!filePath) {
          resolve(null)
          return
        }
        resolve({
          path: filePath,
          name: filePath.split(/[/\\]/).pop() || `source-${Date.now()}.jpg`,
        })
      },
      fail: reject,
    })
  })
}

export const useGenerationStore = defineStore('generation', () => {
  const categories = ref<GenerationCategory[]>([])
  const styles = ref<GenerationStyle[]>([])
  const selectedCategoryId = ref('')
  const selectedStyleId = ref('')
  const promptHint = ref('')

  const sourceFile = ref<LocalFileSelection | null>(null)
  const sourceAsset = ref<GenerationAssetResponse | null>(null)
  const sourcePreviewUrl = ref('')

  const currentJob = ref<GenerationJobResponse | null>(null)
  const stage = ref<GenerationStage>('idle')
  const loadingCatalog = ref(false)
  const busy = ref(false)
  const errorMessage = ref('')
  const statusMessage = ref('先上传一张商品照片')
  const progress = ref(0)

  const selectedCategory = computed(() => {
    return categories.value.find((item) => item.id === selectedCategoryId.value) || null
  })

  const selectedStyle = computed(() => {
    return styles.value.find((item) => item.id === selectedStyleId.value) || null
  })

  const canGenerate = computed(() => {
    return !!sourceAsset.value && !!selectedCategoryId.value && !!selectedStyleId.value && !busy.value
  })

  const rawResultUrl = computed(() => currentJob.value?.raw_result_download_url || '')
  const watermarkedResultUrl = computed(() => currentJob.value?.watermarked_result_download_url || '')
  const hasResult = computed(() => !!watermarkedResultUrl.value)

  function resetResultState() {
    currentJob.value = null
    progress.value = 0
    errorMessage.value = ''
    statusMessage.value = '先上传一张商品照片'
    stage.value = sourceAsset.value ? 'ready' : 'idle'
  }

  async function loadCatalogs() {
    loadingCatalog.value = true
    try {
      const [categoryList, styleList] = await Promise.all([
        listGenerationCategories(),
        listGenerationStyles(),
      ])
      categories.value = categoryList
      styles.value = styleList
      if (!selectedCategoryId.value && categoryList.length) {
        selectedCategoryId.value = categoryList[0].id
      }
      if (!selectedStyleId.value && styleList.length) {
        selectedStyleId.value = styleList[0].id
      }
    } finally {
      loadingCatalog.value = false
    }
  }

  async function pickAndUploadSourceImage() {
    busy.value = true
    errorMessage.value = ''
    statusMessage.value = '选择图片中...'
    try {
      const selection = await chooseImage()
      if (!selection) {
        statusMessage.value = '未选择图片'
        return null
      }
      sourceFile.value = selection
      statusMessage.value = '上传并确认中...'
      const asset = await uploadGenerationAssetFromLocalPath(selection.path, {
        filename: selection.name,
        assetRole: 'source',
      })
      sourceAsset.value = asset
      sourcePreviewUrl.value = asset.download_url
      currentJob.value = null
      progress.value = 10
      stage.value = 'ready'
      statusMessage.value = '图片已确认，可以开始生成'
      return asset
    } catch (error) {
      stage.value = sourceAsset.value ? 'ready' : 'idle'
      errorMessage.value = error instanceof Error ? error.message : '图片上传失败'
      statusMessage.value = errorMessage.value
      throw error
    } finally {
      busy.value = false
    }
  }

  async function pollGenerationJob(jobId: string) {
    let latest = await getGenerationJob(jobId)
    let attempts = 0
    while (attempts < 30 && latest.status !== 'succeeded' && latest.status !== 'failed') {
      progress.value = Math.min(95, 35 + attempts * 2)
      statusMessage.value = latest.status === 'running' ? 'AI 正在生成中...' : '任务排队中...'
      await wait(2000)
      latest = await getGenerationJob(jobId)
      attempts += 1
    }
    return latest
  }

  async function startGeneration() {
    if (!sourceAsset.value) {
      throw new Error('请先上传商品照片')
    }
    if (!selectedCategoryId.value || !selectedStyleId.value) {
      throw new Error('请先选择类目和风格')
    }
    busy.value = true
    errorMessage.value = ''
    statusMessage.value = '创建生成任务...'
    stage.value = 'generating'
    progress.value = 20
    try {
      const job = await createGenerationJob({
        client_request_id: buildGenerationRequestId(),
        source_asset_id: sourceAsset.value.asset_id,
        category_id: selectedCategoryId.value,
        style_id: selectedStyleId.value,
        prompt_hint: promptHint.value.trim(),
      })
      currentJob.value = job
      progress.value = 35
      statusMessage.value = '任务已提交，正在排队'
      const latest = await pollGenerationJob(job.job_id)
      currentJob.value = latest
      if (latest.status === 'succeeded') {
        stage.value = 'succeeded'
        progress.value = 100
        statusMessage.value = '生成完成'
      } else if (latest.status === 'failed') {
        stage.value = 'failed'
        progress.value = 100
        errorMessage.value = latest.error_message || '生成失败'
        statusMessage.value = errorMessage.value
      } else {
        stage.value = 'ready'
        statusMessage.value = '任务仍在处理'
      }
      return latest
    } catch (error) {
      stage.value = 'failed'
      progress.value = 100
      errorMessage.value = error instanceof Error ? error.message : '生成失败'
      statusMessage.value = errorMessage.value
      throw error
    } finally {
      busy.value = false
    }
  }

  function clearCurrentJob() {
    currentJob.value = null
    progress.value = 0
    errorMessage.value = ''
    if (sourceAsset.value) {
      stage.value = 'ready'
      statusMessage.value = '图片已确认，可以开始生成'
    } else {
      stage.value = 'idle'
      statusMessage.value = '先上传一张商品照片'
    }
  }

  return {
    categories,
    styles,
    selectedCategoryId,
    selectedStyleId,
    promptHint,
    sourceFile,
    sourceAsset,
    sourcePreviewUrl,
    currentJob,
    stage,
    loadingCatalog,
    busy,
    errorMessage,
    statusMessage,
    progress,
    selectedCategory,
    selectedStyle,
    canGenerate,
    rawResultUrl,
    watermarkedResultUrl,
    hasResult,
    loadCatalogs,
    pickAndUploadSourceImage,
    startGeneration,
    clearCurrentJob,
    resetResultState,
  }
})

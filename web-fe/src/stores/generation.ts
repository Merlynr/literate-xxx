import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  buildRequestId,
  createJob,
  getJob,
  listCategories,
  listHistory,
  listStyles,
  MAX_SOURCE_ASSETS,
  uploadSourceAsset,
} from '@/api/generation'
import { acceptPrivacy } from '@/api/privacy'
import { estimateQuota } from '@/api/quota'
import type { Category, GenerationAsset, GenerationHistoryItem, GenerationJob, Style } from '@/types'
import { useUserStore } from './user'

type Stage = 'idle' | 'ready' | 'generating' | 'succeeded' | 'failed'

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

export const useGenerationStore = defineStore('generation', () => {
  const userStore = useUserStore()
  const categories = ref<Category[]>([])
  const styles = ref<Style[]>([])
  const selectedCategoryId = ref('')
  const selectedStyleId = ref('')
  const productName = ref('')
  const outputType = ref('scene')
  const promptHint = ref('')

  const sourceAssets = ref<GenerationAsset[]>([])
  const activeSourcePreviewIndex = ref(0)
  const currentJob = ref<GenerationJob | null>(null)
  const historyItems = ref<GenerationHistoryItem[]>([])
  const stage = ref<Stage>('idle')
  const busy = ref(false)
  const errorMessage = ref('')
  const statusMessage = ref('先上传商品实拍图')
  const progress = ref(0)
  const estimatedUnits = ref<number | null>(null)

  const sourcePreviewUrls = computed(() => sourceAssets.value.map((asset) => asset.download_url))
  const sourcePreviewUrl = computed(
    () => sourcePreviewUrls.value[activeSourcePreviewIndex.value] || sourcePreviewUrls.value[0] || '',
  )

  const canGenerate = computed(
    () =>
      sourceAssets.value.length > 0 &&
      !!selectedCategoryId.value &&
      !!selectedStyleId.value &&
      !busy.value &&
      userStore.hasPrivacyAgreement,
  )

  const hasResult = computed(() => !!currentJob.value?.watermarked_result_download_url)

  const isGenerationFinished = computed(
    () => stage.value === 'succeeded' || stage.value === 'failed',
  )

  function resetForNewTask() {
    if (busy.value && stage.value === 'generating') {
      return false
    }
    sourceAssets.value = []
    activeSourcePreviewIndex.value = 0
    currentJob.value = null
    stage.value = 'idle'
    errorMessage.value = ''
    statusMessage.value = '先上传商品实拍图'
    progress.value = 0
    estimatedUnits.value = null
    productName.value = ''
    promptHint.value = ''
    outputType.value = 'scene'
    return true
  }

  function prepareGeneratePage() {
    if (isGenerationFinished.value) {
      resetForNewTask()
    }
  }

  async function loadCatalogs() {
    const [cats, stys] = await Promise.all([listCategories(), listStyles()])
    categories.value = cats
    styles.value = stys
    if (!selectedCategoryId.value && cats[0]) selectedCategoryId.value = cats[0].id
    if (!selectedStyleId.value && stys[0]) selectedStyleId.value = stys[0].id
  }

  async function loadHistory() {
    historyItems.value = await listHistory(0, 50)
  }

  async function refreshEstimate() {
    if (!sourceAssets.value.length) {
      estimatedUnits.value = null
      return
    }
    const est = await estimateQuota({
      category_id: selectedCategoryId.value,
      style_id: selectedStyleId.value,
      source_asset_id: sourceAssets.value[0]?.asset_id,
      prompt_hint: promptHint.value,
    })
    estimatedUnits.value = est.estimated_units
  }

  async function uploadFiles(files: File[]) {
    if (!files.length) return
    busy.value = true
    errorMessage.value = ''
    try {
      const remaining = MAX_SOURCE_ASSETS - sourceAssets.value.length
      if (remaining <= 0) {
        throw new Error(`最多上传 ${MAX_SOURCE_ASSETS} 张实拍图`)
      }
      for (const file of files.slice(0, remaining)) {
        const asset = await uploadSourceAsset(file)
        sourceAssets.value.push(asset)
      }
      activeSourcePreviewIndex.value = Math.max(0, sourceAssets.value.length - 1)
      stage.value = 'ready'
      statusMessage.value =
        sourceAssets.value.length > 1
          ? `已上传 ${sourceAssets.value.length} 张实拍图，可以开始生成`
          : '图片已确认，可以开始生成'
      await refreshEstimate()
    } catch (e) {
      errorMessage.value = e instanceof Error ? e.message : '上传失败'
      throw e
    } finally {
      busy.value = false
    }
  }

  function removeSourceAsset(index: number) {
    if (index < 0 || index >= sourceAssets.value.length) return
    sourceAssets.value.splice(index, 1)
    if (activeSourcePreviewIndex.value >= sourceAssets.value.length) {
      activeSourcePreviewIndex.value = Math.max(0, sourceAssets.value.length - 1)
    }
    if (!sourceAssets.value.length) {
      stage.value = 'idle'
      statusMessage.value = '先上传商品实拍图'
      estimatedUnits.value = null
      return
    }
    stage.value = 'ready'
    statusMessage.value = `已上传 ${sourceAssets.value.length} 张实拍图，可以开始生成`
    void refreshEstimate()
  }

  async function acceptPrivacyAgreement() {
    const res = await acceptPrivacy()
    userStore.privacyAcceptedAt = res.privacy_accepted_at
  }

  async function pollJob(jobId: string) {
    let latest = await getJob(jobId)
    let attempts = 0
    while (attempts < 40 && latest.status !== 'succeeded' && latest.status !== 'failed') {
      progress.value = Math.min(95, 30 + attempts * 2)
      statusMessage.value = latest.status === 'running' ? 'AI 正在生成中…' : '任务排队中…'
      await wait(2000)
      latest = await getJob(jobId)
      attempts += 1
    }
    return latest
  }

  async function startGeneration() {
    if (!sourceAssets.value.length) throw new Error('请先上传商品照片')
    if (!userStore.hasPrivacyAgreement) throw new Error('请先同意隐私协议')
    busy.value = true
    stage.value = 'generating'
    errorMessage.value = ''
    progress.value = 15
    try {
      const hint = [productName.value, promptHint.value].filter(Boolean).join('；')
      const job = await createJob({
        client_request_id: buildRequestId(),
        source_asset_ids: sourceAssets.value.map((asset) => asset.asset_id),
        category_id: selectedCategoryId.value,
        style_id: selectedStyleId.value,
        prompt_hint: hint,
      })
      currentJob.value = job
      progress.value = 35
      const latest = await pollJob(job.job_id)
      currentJob.value = latest
      if (latest.status === 'succeeded') {
        stage.value = 'succeeded'
        progress.value = 100
        statusMessage.value = '生成完成'
      } else if (latest.status === 'failed') {
        stage.value = 'failed'
        errorMessage.value = latest.error_message || '生成失败'
      }
      await loadHistory()
      return latest
    } catch (e) {
      stage.value = 'failed'
      errorMessage.value = e instanceof Error ? e.message : '生成失败'
      throw e
    } finally {
      busy.value = false
    }
  }

  return {
    categories,
    styles,
    selectedCategoryId,
    selectedStyleId,
    productName,
    outputType,
    promptHint,
    sourceAssets,
    sourcePreviewUrl,
    sourcePreviewUrls,
    activeSourcePreviewIndex,
    currentJob,
    historyItems,
    stage,
    busy,
    errorMessage,
    statusMessage,
    progress,
    estimatedUnits,
    canGenerate,
    hasResult,
    isGenerationFinished,
    maxSourceAssets: MAX_SOURCE_ASSETS,
    resetForNewTask,
    prepareGeneratePage,
    loadCatalogs,
    loadHistory,
    refreshEstimate,
    uploadFiles,
    removeSourceAsset,
    acceptPrivacyAgreement,
    startGeneration,
  }
})

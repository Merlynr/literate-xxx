import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  buildRequestId,
  createJob,
  getJob,
  listCategories,
  listHistory,
  listStyles,
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

  const sourceAsset = ref<GenerationAsset | null>(null)
  const sourcePreviewUrl = ref('')
  const currentJob = ref<GenerationJob | null>(null)
  const historyItems = ref<GenerationHistoryItem[]>([])
  const stage = ref<Stage>('idle')
  const busy = ref(false)
  const errorMessage = ref('')
  const statusMessage = ref('先上传商品实拍图')
  const progress = ref(0)
  const estimatedUnits = ref<number | null>(null)

  const canGenerate = computed(
    () =>
      !!sourceAsset.value &&
      !!selectedCategoryId.value &&
      !!selectedStyleId.value &&
      !busy.value &&
      userStore.hasPrivacyAgreement,
  )

  const hasResult = computed(() => !!currentJob.value?.watermarked_result_download_url)

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
    if (!sourceAsset.value) {
      estimatedUnits.value = null
      return
    }
    const est = await estimateQuota({
      category_id: selectedCategoryId.value,
      style_id: selectedStyleId.value,
      source_asset_id: sourceAsset.value.asset_id,
      prompt_hint: promptHint.value,
    })
    estimatedUnits.value = est.estimated_units
  }

  async function uploadFile(file: File) {
    busy.value = true
    errorMessage.value = ''
    try {
      const asset = await uploadSourceAsset(file)
      sourceAsset.value = asset
      sourcePreviewUrl.value = asset.download_url
      stage.value = 'ready'
      statusMessage.value = '图片已确认，可以开始生成'
      await refreshEstimate()
    } catch (e) {
      errorMessage.value = e instanceof Error ? e.message : '上传失败'
      throw e
    } finally {
      busy.value = false
    }
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
    if (!sourceAsset.value) throw new Error('请先上传商品照片')
    if (!userStore.hasPrivacyAgreement) throw new Error('请先同意隐私协议')
    busy.value = true
    stage.value = 'generating'
    errorMessage.value = ''
    progress.value = 15
    try {
      const hint = [productName.value, promptHint.value].filter(Boolean).join('；')
      const job = await createJob({
        client_request_id: buildRequestId(),
        source_asset_id: sourceAsset.value.asset_id,
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
    sourceAsset,
    sourcePreviewUrl,
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
    loadCatalogs,
    loadHistory,
    refreshEstimate,
    uploadFile,
    acceptPrivacyAgreement,
    startGeneration,
  }
})

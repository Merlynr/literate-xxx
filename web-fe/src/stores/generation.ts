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
import { invalidateAfterNewGeneration } from '@/utils/imageCache'
import type { Category, GenerationAsset, GenerationHistoryItem, GenerationJob, Style } from '@/types'
import { useUserStore } from './user'

type Stage = 'idle' | 'ready'

export interface JobTrack {
  progress: number
  statusMessage: string
}

const JOB_TRACKS_STORAGE_KEY = 'xxzx_job_tracks'
/** 与后端 job_reconciliation.QUEUED_STALE_SECONDS 一致 */
const QUEUED_STALE_MS = 3 * 60 * 1000
const QUEUED_CRITICAL_MS = 10 * 60 * 1000

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

export function isActiveJobStatus(status: string) {
  return status === 'queued' || status === 'running'
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
  const historyItems = ref<GenerationHistoryItem[]>([])
  function loadJobTracksFromSession(): Record<string, JobTrack> {
    try {
      const raw = sessionStorage.getItem(JOB_TRACKS_STORAGE_KEY)
      if (!raw) return {}
      const parsed = JSON.parse(raw) as Record<string, JobTrack>
      return typeof parsed === 'object' && parsed ? parsed : {}
    } catch {
      return {}
    }
  }

  const jobTracks = ref<Record<string, JobTrack>>(loadJobTracksFromSession())
  const stage = ref<Stage>('idle')
  const busy = ref(false)
  const errorMessage = ref('')
  const statusMessage = ref('先上传商品实拍图')
  const estimatedUnits = ref<number | null>(null)

  const jobPollTokens = new Map<string, number>()
  const jobPollInFlight = new Set<string>()

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

  function getJobTrack(jobId: string): JobTrack | undefined {
    return jobTracks.value[jobId]
  }

  function isJobPollActive(jobId: string, token: number) {
    return jobPollTokens.get(jobId) === token
  }

  function persistJobTracks() {
    try {
      sessionStorage.setItem(JOB_TRACKS_STORAGE_KEY, JSON.stringify(jobTracks.value))
    } catch {
      /* ignore quota / private mode */
    }
  }

  function setJobTrack(jobId: string, progress: number, statusMessage: string) {
    jobTracks.value = {
      ...jobTracks.value,
      [jobId]: { progress, statusMessage },
    }
    persistJobTracks()
  }

  /** 进度只增不减，避免刷新/重连轮询时条突然回退 */
  function bumpJobTrack(jobId: string, progress: number, statusMessage: string) {
    const prev = jobTracks.value[jobId]?.progress ?? 0
    setJobTrack(jobId, Math.max(prev, progress), statusMessage)
  }

  function statusMessageForJob(status: string) {
    if (status === 'running') return 'AI 正在生成中…'
    if (status === 'queued') return '任务排队中…'
    return '处理中…'
  }

  function clearJobTrack(jobId: string) {
    const next = { ...jobTracks.value }
    delete next[jobId]
    jobTracks.value = next
    persistJobTracks()
  }

  /** 根据任务停留时间估算进度（刷新/重进页面时避免从 25% 重新开始） */
  function estimateProgressForItem(item: GenerationHistoryItem): number {
    const refMs = new Date(item.updated_at || item.created_at).getTime()
    if (Number.isNaN(refMs)) return 20
    const minutes = Math.max(0, (Date.now() - refMs) / 60_000)
    if (item.status === 'running') return Math.min(95, 45 + Math.floor(minutes * 4))
    if (item.status === 'queued') return Math.min(92, 18 + Math.floor(minutes * 6))
    return 15
  }

  function displayProgress(item: GenerationHistoryItem): number {
    const track = jobTracks.value[item.job_id]
    const estimated = estimateProgressForItem(item)
    if (track) return Math.max(track.progress, estimated)
    return estimated
  }

  function queuedWaitMs(item: GenerationHistoryItem): number {
    const refMs = new Date(item.updated_at || item.created_at).getTime()
    if (Number.isNaN(refMs)) return 0
    return Math.max(0, Date.now() - refMs)
  }

  function isStuckQueued(item: GenerationHistoryItem): boolean {
    return item.status === 'queued' && queuedWaitMs(item) >= QUEUED_STALE_MS
  }

  function isCriticalQueued(item: GenerationHistoryItem): boolean {
    return item.status === 'queued' && queuedWaitMs(item) >= QUEUED_CRITICAL_MS
  }

  function stuckQueuedHint(item: GenerationHistoryItem): string {
    if (item.status !== 'queued') return ''
    const minutes = Math.max(1, Math.floor(queuedWaitMs(item) / 60_000))
    if (isCriticalQueued(item)) {
      return `已排队约 ${minutes} 分钟仍未开始生成。请确认 Celery Worker 与 Redis 正常，或点击刷新；仍无进展请联系管理员。`
    }
    if (isStuckQueued(item)) {
      return `已排队约 ${minutes} 分钟，系统会自动重试投递，请稍候或点击刷新。`
    }
    return ''
  }

  function displayProgressMessage(item: GenerationHistoryItem): string {
    const stuck = stuckQueuedHint(item)
    if (stuck) return stuck
    const track = jobTracks.value[item.job_id]
    if (track?.statusMessage) return track.statusMessage
    if (item.status === 'running') return 'AI 正在生成中…'
    if (item.status === 'queued') return '任务排队中…'
    return '处理中…'
  }

  function jobToHistoryRow(
    job: GenerationJob,
    extras?: Partial<GenerationHistoryItem>,
  ): GenerationHistoryItem {
    return {
      job_id: job.job_id,
      status: job.status,
      created_at: job.created_at,
      updated_at: job.updated_at,
      error_message: job.error_message || '',
      source_preview_url:
        extras?.source_preview_url ?? job.source_preview_url ?? null,
      raw_result_download_url: job.raw_result_download_url ?? null,
      watermarked_result_download_url: job.watermarked_result_download_url ?? null,
      category_name: extras?.category_name,
      style_name: extras?.style_name,
      prompt_hint: extras?.prompt_hint,
    }
  }

  function upsertHistoryItem(job: GenerationJob, extras?: Partial<GenerationHistoryItem>) {
    const row = jobToHistoryRow(job, extras)
    const idx = historyItems.value.findIndex((i) => i.job_id === job.job_id)
    if (idx >= 0) {
      historyItems.value[idx] = { ...historyItems.value[idx], ...row }
    } else {
      historyItems.value.unshift(row)
    }
  }

  function mergeJobIntoHistory(job: GenerationJob) {
    upsertHistoryItem(job)
  }

  function resetGenerateForm() {
    sourceAssets.value = []
    activeSourcePreviewIndex.value = 0
    stage.value = 'idle'
    errorMessage.value = ''
    statusMessage.value = '先上传商品实拍图'
    estimatedUnits.value = null
    productName.value = ''
    promptHint.value = ''
    outputType.value = 'scene'
  }

  function prepareGeneratePage() {
    resetGenerateForm()
  }

  /** 仅对「没有进度记录且未在轮询」的任务启动轮询 */
  function ensureJobPollingForNewActiveJobs() {
    for (const item of historyItems.value) {
      if (!isActiveJobStatus(item.status)) continue
      if (jobPollInFlight.has(item.job_id)) continue
      if (jobTracks.value[item.job_id]) continue
      startJobPolling(item.job_id)
    }
  }

  /** 有进度但轮询已停（如长时间排队）时恢复轮询，不重置进度 */
  function resumeJobPollingIfNeeded() {
    for (const item of historyItems.value) {
      if (!isActiveJobStatus(item.status)) continue
      if (jobPollInFlight.has(item.job_id)) continue
      if (!jobTracks.value[item.job_id]) continue
      startJobPolling(item.job_id, { resume: true })
    }
  }

  /** 刷新列表时同步进行中任务状态，不重启轮询、不回退进度 */
  async function resyncActiveJobsFromApi() {
    const active = historyItems.value.filter((i) => isActiveJobStatus(i.status))
    await Promise.all(
      active.map(async (item) => {
        try {
          const latest = await getJob(item.job_id, { skipCache: true })
          mergeJobIntoHistory(latest)
          const track = jobTracks.value[item.job_id]
          if (track) {
            bumpJobTrack(item.job_id, track.progress, statusMessageForJob(latest.status))
          }
        } catch {
          /* ignore */
        }
      }),
    )
  }

  async function loadCatalogs(options?: { force?: boolean }) {
    const [cats, stys] = await Promise.all([
      listCategories(options),
      listStyles(options),
    ])
    categories.value = cats
    styles.value = stys
    if (!selectedCategoryId.value && cats[0]) selectedCategoryId.value = cats[0].id
    if (!selectedStyleId.value && stys[0]) selectedStyleId.value = stys[0].id
  }

  async function loadHistory(options?: { force?: boolean; keepPolling?: boolean }) {
    historyItems.value = await listHistory(0, 50, undefined, options)
    if (options?.keepPolling) {
      await resyncActiveJobsFromApi()
      resumeJobPollingIfNeeded()
      ensureJobPollingForNewActiveJobs()
      return
    }
    ensureJobPollingForNewActiveJobs()
    resumeJobPollingIfNeeded()
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

  function startJobPolling(jobId: string, options?: { resume?: boolean }) {
    if (jobPollInFlight.has(jobId)) return

    const token = (jobPollTokens.get(jobId) ?? 0) + 1
    jobPollTokens.set(jobId, token)
    if (!jobTracks.value[jobId]) {
      setJobTrack(jobId, 12, '任务已提交，等待处理…')
    } else if (options?.resume) {
      const track = jobTracks.value[jobId]
      bumpJobTrack(jobId, track.progress, track.statusMessage)
    }
    jobPollInFlight.add(jobId)
    void runJobPoll(jobId, token, options)
  }

  async function runJobPoll(
    jobId: string,
    token: number,
    options?: { resume?: boolean },
  ) {
    const resume = !!options?.resume

    try {
      let latest = await getJob(jobId, { skipCache: true })
      if (!isJobPollActive(jobId, token)) return latest

      mergeJobIntoHistory(latest)
      if (resume) {
        bumpJobTrack(
          jobId,
          jobTracks.value[jobId]?.progress ?? 15,
          statusMessageForJob(latest.status),
        )
      } else {
        bumpJobTrack(jobId, 20, statusMessageForJob(latest.status))
      }

      let attempts = 0
      while (attempts < 40 && isActiveJobStatus(latest.status)) {
        if (!isJobPollActive(jobId, token)) return latest
        if (!resume) {
          bumpJobTrack(
            jobId,
            Math.min(95, 25 + attempts * 2),
            statusMessageForJob(latest.status),
          )
        } else {
          const cur = jobTracks.value[jobId]?.progress ?? 15
          bumpJobTrack(jobId, Math.min(99, cur + 1), statusMessageForJob(latest.status))
        }
        await wait(2000)
        if (!isJobPollActive(jobId, token)) return latest
        latest = await getJob(jobId, { skipCache: true })
        mergeJobIntoHistory(latest)
        attempts += 1
      }

      if (isActiveJobStatus(latest.status)) {
        if (!isJobPollActive(jobId, token)) return latest
        bumpJobTrack(jobId, Math.max(jobTracks.value[jobId]?.progress ?? 80, 80), '任务仍在处理中，系统会自动重试排队…')
        let extraAttempts = 0
        while (extraAttempts < 30 && isActiveJobStatus(latest.status)) {
          if (!isJobPollActive(jobId, token)) return latest
          const statusMsg =
            latest.status === 'running'
              ? 'AI 正在生成中，请稍候…'
              : '仍在排队，系统会自动重试…'
          if (resume) {
            const cur = jobTracks.value[jobId]?.progress ?? 82
            bumpJobTrack(jobId, Math.min(99, Math.max(cur, 82 + extraAttempts)), statusMsg)
          } else {
            bumpJobTrack(jobId, Math.min(98, 82 + extraAttempts), statusMsg)
          }
          await wait(3000)
          if (!isJobPollActive(jobId, token)) return latest
          latest = await getJob(jobId, { skipCache: true })
          mergeJobIntoHistory(latest)
          extraAttempts += 1
        }
      }

      if (!isJobPollActive(jobId, token)) return latest

      mergeJobIntoHistory(latest)

      if (latest.status === 'succeeded') {
        setJobTrack(jobId, 100, '生成完成')
        invalidateAfterNewGeneration()
        await loadHistory({ force: true, keepPolling: true })
        window.setTimeout(() => clearJobTrack(jobId), 4000)
      } else if (latest.status === 'failed') {
        setJobTrack(jobId, 100, latest.error_message || '生成失败')
        await loadHistory({ force: true, keepPolling: true })
        window.setTimeout(() => clearJobTrack(jobId), 8000)
      } else {
        bumpJobTrack(jobId, Math.max(jobTracks.value[jobId]?.progress ?? 98, 98), '任务仍在处理中，可刷新列表查看')
        await loadHistory({ force: true, keepPolling: true })
      }

      return latest
    } finally {
      jobPollInFlight.delete(jobId)
    }
  }

  async function startGeneration() {
    if (!sourceAssets.value.length) throw new Error('请先上传商品照片')
    if (!userStore.hasPrivacyAgreement) throw new Error('请先同意隐私协议')

    const previewUrl = sourcePreviewUrl.value
    const categoryName =
      categories.value.find((c) => c.id === selectedCategoryId.value)?.name ?? ''
    const styleName = styles.value.find((s) => s.id === selectedStyleId.value)?.name ?? ''
    const hint = [productName.value, promptHint.value].filter(Boolean).join('；')

    busy.value = true
    errorMessage.value = ''
    try {
      const job = await createJob({
        client_request_id: buildRequestId(),
        source_asset_ids: sourceAssets.value.map((asset) => asset.asset_id),
        category_id: selectedCategoryId.value,
        style_id: selectedStyleId.value,
        prompt_hint: hint,
      })

      upsertHistoryItem(job, {
        source_preview_url: previewUrl || job.source_preview_url,
        category_name: categoryName,
        style_name: styleName,
        prompt_hint: hint,
      })
      startJobPolling(job.job_id)
      resetGenerateForm()
      return job
    } catch (e) {
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
    historyItems,
    jobTracks,
    stage,
    busy,
    errorMessage,
    statusMessage,
    estimatedUnits,
    canGenerate,
    maxSourceAssets: MAX_SOURCE_ASSETS,
    getJobTrack,
    displayProgress,
    displayProgressMessage,
    isStuckQueued,
    isCriticalQueued,
    stuckQueuedHint,
    isActiveJobStatus,
    resetGenerateForm,
    prepareGeneratePage,
    loadCatalogs,
    loadHistory,
    refreshEstimate,
    uploadFiles,
    removeSourceAsset,
    acceptPrivacyAgreement,
    startGeneration,
    startJobPolling,
  }
})

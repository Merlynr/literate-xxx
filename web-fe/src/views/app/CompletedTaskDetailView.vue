<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getJob } from '@/api/generation'
import JobStatusBadge from '@/components/JobStatusBadge.vue'
import type { GenerationJob } from '@/types'

const route = useRoute()
const router = useRouter()
const job = ref<GenerationJob | null>(null)
const loading = ref(false)
const error = ref('')

const categoryName = computed(
  () => job.value?.prompt_snapshot?.category?.name || '—',
)
const styleName = computed(() => job.value?.prompt_snapshot?.style?.name || '—')
const promptHint = computed(() => {
  const fromRequest = job.value?.request_snapshot?.prompt_hint?.trim()
  const fromPrompt = job.value?.prompt_snapshot?.prompt_hint?.trim()
  return fromRequest || fromPrompt || '—'
})

const rawImageUrl = computed(
  () => job.value?.raw_result_download_url || job.value?.source_preview_url || '',
)

onMounted(async () => {
  const jobId = route.params.jobId as string
  if (!jobId) {
    error.value = '无效的任务 ID'
    return
  }
  loading.value = true
  try {
    const data = await getJob(jobId)
    if (data.status !== 'succeeded') {
      error.value = '该任务尚未完成，无法在此查看'
      job.value = data
      return
    }
    job.value = data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <button
      type="button"
      class="mb-4 text-sm text-brand-700 hover:underline"
      @click="router.push('/app/works/completed')"
    >
      ← 返回已完成任务
    </button>

    <el-skeleton v-if="loading" :rows="6" animated />
    <el-alert v-else-if="error" :title="error" type="error" show-icon class="mb-4" />

    <template v-else-if="job">
      <header class="mb-6 flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold">任务详情</h1>
        <JobStatusBadge :status="job.status" />
        <span class="text-xs text-brand-900/50">{{ job.job_id }}</span>
      </header>

      <div class="grid gap-6 lg:grid-cols-2">
        <div class="page-card p-4">
          <h2 class="mb-3 font-semibold text-brand-700">生成原图</h2>
          <div class="flex min-h-[280px] items-center justify-center rounded-xl bg-cream-100">
            <img
              v-if="rawImageUrl"
              :src="rawImageUrl"
              class="max-h-[420px] max-w-full rounded-lg object-contain"
              alt="生成原图"
            />
            <p v-else class="text-sm text-brand-900/40">暂无原图</p>
          </div>
          <div v-if="rawImageUrl" class="mt-3 flex flex-wrap gap-2">
            <a v-if="job.raw_result_download_url" :href="job.raw_result_download_url" target="_blank" class="btn-primary text-sm">
              下载生成原图
            </a>
            <a
              v-if="job.watermarked_result_download_url"
              :href="job.watermarked_result_download_url"
              target="_blank"
              class="rounded-xl border border-brand-700/20 px-4 py-2 text-sm"
            >
              下载水印图
            </a>
          </div>
        </div>

        <div class="space-y-4">
          <div class="page-card p-5">
            <h2 class="mb-4 font-semibold text-brand-700">任务参数</h2>
            <dl class="space-y-3 text-sm">
              <div class="flex gap-4">
                <dt class="w-20 shrink-0 text-brand-900/50">类目</dt>
                <dd class="font-medium">{{ categoryName }}</dd>
              </div>
              <div class="flex gap-4">
                <dt class="w-20 shrink-0 text-brand-900/50">风格</dt>
                <dd class="font-medium">{{ styleName }}</dd>
              </div>
              <div class="flex gap-4">
                <dt class="w-20 shrink-0 text-brand-900/50">画面要求</dt>
                <dd class="whitespace-pre-wrap leading-relaxed">{{ promptHint }}</dd>
              </div>
              <div class="flex gap-4">
                <dt class="w-20 shrink-0 text-brand-900/50">完成时间</dt>
                <dd>{{ new Date(job.updated_at).toLocaleString() }}</dd>
              </div>
            </dl>
          </div>

          <div v-if="job.source_preview_url" class="page-card p-4">
            <h2 class="mb-2 text-sm font-semibold text-brand-700">商品实拍（参考）</h2>
            <img
              :src="job.source_preview_url"
              class="max-h-40 rounded-lg object-contain"
              alt="实拍"
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

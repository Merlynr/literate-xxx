<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CachedImage from '@/components/CachedImage.vue'
import QuotaSummaryCard from '@/components/QuotaSummaryCard.vue'
import JobStatusBadge from '@/components/JobStatusBadge.vue'
import { getQuotaSummary } from '@/api/quota'
import { useGenerationStore } from '@/stores/generation'
import type { QuotaSummary } from '@/types'

const router = useRouter()
const gen = useGenerationStore()
const quota = ref<QuotaSummary | null>(null)
const quotaLoading = ref(false)

onMounted(async () => {
  quotaLoading.value = true
  try {
    quota.value = await getQuotaSummary()
    await gen.loadHistory()
  } finally {
    quotaLoading.value = false
  }
})
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <header>
      <p class="eyebrow">CLIENT PORTAL</p>
      <h1 class="text-3xl font-black text-brand-900">商品图 AI 工作台</h1>
      <p class="mt-2 text-brand-900/70">把实拍图变成能直接投放的宣传海报</p>
    </header>

    <div class="page-card overflow-hidden p-6">
      <p class="eyebrow mb-2">PRODUCTION</p>
      <h2 class="text-xl font-bold">农产品宣传视觉</h2>
      <p class="mt-2 text-sm text-brand-900/65">
        上传商品实拍 → 选择类目与风格 → AI 生成水印成品图
      </p>
      <div class="mt-4 flex flex-wrap gap-3">
        <button type="button" class="btn-primary" @click="router.push('/app/generate')">
          上传商品
        </button>
        <button
          type="button"
          class="rounded-xl border border-brand-700/20 px-5 py-2.5 text-sm font-semibold"
          @click="router.push('/app/works')"
        >
          打开图库
        </button>
      </div>
    </div>

    <QuotaSummaryCard :summary="quota" :loading="quotaLoading" />

    <section>
      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-lg font-bold">最近任务</h2>
        <router-link to="/app/works/tasks" class="text-sm text-brand-700">查看全部</router-link>
      </div>
      <div v-if="!gen.historyItems.length" class="page-card p-8 text-center text-sm text-brand-900/60">
        完成第一次生成后，任务会出现在这里
      </div>
      <div v-else class="grid gap-3 sm:grid-cols-2">
        <div
          v-for="item in gen.historyItems.slice(0, 6)"
          :key="item.job_id"
          class="page-card flex gap-3 p-3"
        >
          <CachedImage
            v-if="item.watermarked_result_download_url || item.source_preview_url"
            :src="item.watermarked_result_download_url || item.source_preview_url"
            :job-id="item.job_id"
            :image-role="item.watermarked_result_download_url ? 'watermark' : 'source'"
            img-class="h-16 w-16 rounded-lg object-cover"
          />
          <div class="min-w-0 flex-1">
            <JobStatusBadge :status="item.status" />
            <p class="mt-1 truncate text-xs text-brand-900/50">{{ item.job_id }}</p>
            <p class="text-xs text-brand-900/40">{{ new Date(item.created_at).toLocaleString() }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

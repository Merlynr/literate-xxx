<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CachedImage from '@/components/CachedImage.vue'
import JobDeleteButton from '@/components/JobDeleteButton.vue'
import { listCompletedHistory } from '@/api/generation'
import { enrichHistoryItems } from '@/utils/jobMeta'
import { prepareForceRefresh } from '@/utils/refresh'
import type { GenerationHistoryItem } from '@/types'

const router = useRouter()
const items = ref<GenerationHistoryItem[]>([])
const loading = ref(false)
const reloadKey = ref(0)

async function load(force = false) {
  loading.value = true
  try {
    if (force) {
      prepareForceRefresh()
      reloadKey.value += 1
    }
    const rows = await listCompletedHistory(0, 100, { force })
    items.value = await enrichHistoryItems(rows)
  } finally {
    loading.value = false
  }
}

function openDetail(jobId: string) {
  router.push({ name: 'app-work-detail', params: { jobId } })
}

function onRowClick(row: GenerationHistoryItem) {
  openDetail(row.job_id)
}

function onJobDeleted(jobId: string) {
  items.value = items.value.filter((row) => row.job_id !== jobId)
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="mb-6">
      <p class="eyebrow">COMPLETED JOBS</p>
      <h1 class="text-2xl font-bold">已完成任务</h1>
      <p class="mt-1 text-sm text-brand-900/60">查看生成成功的任务详情：原图、类目、风格与画面要求</p>
    </header>

    <div class="mb-4 flex gap-3">
      <el-button :loading="loading" @click="load(true)">刷新</el-button>
      <router-link to="/app/generate">
        <el-button type="primary">发起新生成</el-button>
      </router-link>
    </div>

    <el-skeleton v-if="loading" :rows="5" animated />
    <div v-else-if="!items.length" class="page-card p-12 text-center text-brand-900/50">
      暂无已完成任务
    </div>
    <div v-else class="page-card overflow-hidden">
      <el-table :data="items" stripe class="cursor-pointer" @row-click="onRowClick">
        <el-table-column label="预览" width="88">
          <template #default="{ row }">
            <CachedImage
              v-if="row.raw_result_download_url || row.watermarked_result_download_url || row.source_preview_url"
              :src="row.raw_result_download_url || row.watermarked_result_download_url || row.source_preview_url"
              :job-id="row.job_id"
              :image-role="row.raw_result_download_url ? 'raw' : row.watermarked_result_download_url ? 'watermark' : 'source'"
              :reload-key="reloadKey"
              img-class="h-14 w-14 rounded-lg object-cover"
            />
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="类目" min-width="100" />
        <el-table-column prop="style_name" label="风格" min-width="100" />
        <el-table-column label="画面要求" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.prompt_hint || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="完成时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.updated_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row.job_id)">查看</el-button>
            <JobDeleteButton
              :job-id="row.job_id"
              status="succeeded"
              variant="text"
              @deleted="onJobDeleted(row.job_id)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import JobStatusBadge from '@/components/JobStatusBadge.vue'
import { listHistory } from '@/api/generation'
import type { GenerationHistoryItem } from '@/types'

const rows = ref<GenerationHistoryItem[]>([])
const loading = ref(false)
const statusFilter = ref('')

async function load() {
  loading.value = true
  const all = await listHistory(0, 100)
  rows.value = statusFilter.value ? all.filter((j) => j.status === statusFilter.value) : all
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <h1 class="text-2xl font-bold">生成任务监控</h1>
      <el-select v-model="statusFilter" clearable placeholder="状态" style="width: 140px" @change="load">
        <el-option label="排队" value="queued" />
        <el-option label="运行中" value="running" />
        <el-option label="成功" value="succeeded" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="job_id" label="任务 ID" min-width="220" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><JobStatusBadge :status="row.status" /></template>
      </el-table-column>
      <el-table-column prop="error_message" label="错误" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="预览" width="90">
        <template #default="{ row }">
          <a
            v-if="row.watermarked_result_download_url"
            :href="row.watermarked_result_download_url"
            target="_blank"
            class="text-blue-600"
          >
            查看
          </a>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

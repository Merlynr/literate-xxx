<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listHistory } from '@/api/generation'
import { listQuotaLedger } from '@/api/quota'
import type { GenerationHistoryItem, QuotaLedgerItem } from '@/types'

const jobs = ref<GenerationHistoryItem[]>([])
const ledger = ref<QuotaLedgerItem[]>([])

onMounted(async () => {
  ;[jobs.value, ledger.value] = await Promise.all([listHistory(0, 100), listQuotaLedger(0, 50)])
})

const succeeded = computed(() => jobs.value.filter((j) => j.status === 'succeeded').length)
const failed = computed(() => jobs.value.filter((j) => j.status === 'failed').length)
const rate = computed(() =>
  jobs.value.length ? Math.round((succeeded.value / jobs.value.length) * 100) : 0,
)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">运营概览</h1>
    <div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-xl bg-white p-5 shadow-sm">
        <p class="text-sm text-slate-500">任务总数</p>
        <p class="text-3xl font-bold">{{ jobs.length }}</p>
      </div>
      <div class="rounded-xl bg-white p-5 shadow-sm">
        <p class="text-sm text-slate-500">成功率</p>
        <p class="text-3xl font-bold text-green-600">{{ rate }}%</p>
      </div>
      <div class="rounded-xl bg-white p-5 shadow-sm">
        <p class="text-sm text-slate-500">成功</p>
        <p class="text-3xl font-bold">{{ succeeded }}</p>
      </div>
      <div class="rounded-xl bg-white p-5 shadow-sm">
        <p class="text-sm text-slate-500">失败</p>
        <p class="text-3xl font-bold text-red-600">{{ failed }}</p>
      </div>
    </div>

    <h2 class="mb-3 text-lg font-semibold">最近失败任务</h2>
    <el-table :data="jobs.filter((j) => j.status === 'failed').slice(0, 10)" stripe>
      <el-table-column prop="job_id" label="任务 ID" min-width="200" />
      <el-table-column prop="error_message" label="错误" min-width="240" />
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

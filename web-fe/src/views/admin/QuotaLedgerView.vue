<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listQuotaLedger } from '@/api/quota'
import type { QuotaLedgerItem } from '@/types'

const rows = ref<QuotaLedgerItem[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  rows.value = await listQuotaLedger()
  loading.value = false
})
</script>

<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">额度流水</h1>
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="event_type" label="事件" width="120" />
      <el-table-column prop="delta_units" label="变动" width="80" />
      <el-table-column prop="reason" label="原因" min-width="160" />
      <el-table-column prop="job_id" label="任务" min-width="180" show-overflow-tooltip />
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

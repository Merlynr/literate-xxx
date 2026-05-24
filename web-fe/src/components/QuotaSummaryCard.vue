<script setup lang="ts">
import type { QuotaSummary } from '@/types'

defineProps<{
  summary: QuotaSummary | null
  loading?: boolean
}>()
</script>

<template>
  <div class="page-card p-5">
    <p class="eyebrow mb-2">额度</p>
    <el-skeleton v-if="loading" :rows="2" animated />
    <template v-else-if="summary">
      <div class="grid grid-cols-3 gap-4 text-center">
        <div>
          <p class="text-2xl font-bold text-brand-700">{{ summary.available_units }}</p>
          <p class="text-xs text-brand-900/60">可用</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-gold-600">{{ summary.frozen_units }}</p>
          <p class="text-xs text-brand-900/60">冻结</p>
        </div>
        <div>
          <p class="text-2xl font-bold">{{ summary.total_units }}</p>
          <p class="text-xs text-brand-900/60">总量</p>
        </div>
      </div>
      <p v-if="summary.active_plan_name" class="mt-3 text-center text-sm text-brand-900/70">
        当前套餐：{{ summary.active_plan_name }}
      </p>
    </template>
    <p v-else class="text-sm text-brand-900/60">暂无额度数据</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import QuotaSummaryCard from '@/components/QuotaSummaryCard.vue'
import { getQuotaSummary } from '@/api/quota'
import { useUserStore } from '@/stores/user'
import type { QuotaSummary } from '@/types'

const userStore = useUserStore()
const quota = ref<QuotaSummary | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  quota.value = await getQuotaSummary()
  loading.value = false
})
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <header>
      <p class="eyebrow">CLIENT CONFIGURATION</p>
      <h1 class="text-2xl font-bold">客户配置中心</h1>
    </header>

    <div class="page-card p-6">
      <p class="text-sm text-brand-900/70">
        专属视觉工作台：提交商品图需求、查看生成进度、下载成品。
      </p>
      <dl class="mt-4 space-y-2 text-sm">
        <div class="flex justify-between">
          <dt class="text-brand-900/50">昵称</dt>
          <dd>{{ userStore.profile?.nickname || '—' }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-brand-900/50">租户 ID</dt>
          <dd class="font-mono text-xs">{{ userStore.profile?.tenant_id }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-brand-900/50">隐私协议</dt>
          <dd>{{ userStore.hasPrivacyAgreement ? '已同意' : '未同意' }}</dd>
        </div>
      </dl>
    </div>

    <QuotaSummaryCard :summary="quota" :loading="loading" />

    <p class="text-center text-xs text-brand-900/40">当前演示周期：2026.05 · 按已提交任务计算额度</p>
  </div>
</template>

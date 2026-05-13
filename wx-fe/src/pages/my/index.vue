<template>
  <view class="page-my">
    <view class="header">
      <view class="avatar-placeholder">
        <text>👤</text>
      </view>
      <view v-if="userStore.isLoggedIn" class="user-info">
        <text class="username">{{ userStore.nickname || '未设置昵称' }}</text>
        <text class="tenant-id">租户: {{ userStore.tenantId.substring(0, 8) }}...</text>
      </view>
      <text v-else class="username">未登录</text>
    </view>

    <view class="content">
      <QuotaCard
        :summary="quotaSummary"
        :busy="quotaLoading"
        action-text="刷新额度"
        @action="loadPageData"
      />

      <view class="section-title">
        <text>我的作品</text>
        <text class="section-subtitle">下拉刷新查看最近生成记录</text>
      </view>
      <WorksList
        :items="generationStore.historyItems"
        :refreshing="generationStore.loadingHistory"
        @refresh="loadHistory"
        @preview="previewItem"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import QuotaCard from '@/components/quota/QuotaCard.vue'
import WorksList from '@/components/works/WorksList.vue'
import { useUserStore } from '@/stores/user'
import { useGenerationStore } from '@/stores/generation'
import { getQuotaSummary } from '@/api/quota'
import type { QuotaSummary, GenerationHistoryItem } from '@/types/generation'

const userStore = useUserStore()
const generationStore = useGenerationStore()
const quotaSummary = ref<QuotaSummary | null>(null)
const quotaLoading = ref(false)

async function loadQuotaSummary() {
  quotaLoading.value = true
  try {
    quotaSummary.value = await getQuotaSummary()
  } finally {
    quotaLoading.value = false
  }
}

async function loadHistory() {
  await generationStore.loadHistory()
}

async function loadPageData() {
  await Promise.all([loadQuotaSummary(), loadHistory()])
}

function previewItem(item: GenerationHistoryItem) {
  const url = item.watermarked_result_download_url || item.raw_result_download_url || item.source_preview_url
  if (!url) return
  uni.previewImage({
    urls: [url],
    current: url,
  })
}

onMounted(async () => {
  await userStore.ensureAuth()
  await loadPageData()
})

onPullDownRefresh(() => {
  loadPageData()
    .finally(() => uni.stopPullDownRefresh())
})
</script>

<style scoped>
.page-my {
  padding: 0;
}
.header {
  background: linear-gradient(135deg, #1aad19, #12b7f5);
  padding: 60rpx 32rpx 40rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.avatar-placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.username {
  font-size: 32rpx;
  color: #fff;
  font-weight: 500;
}
.tenant-id {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 8rpx;
}
.content {
  padding: 24rpx 32rpx 40rpx;
}
.section-title {
  margin: 24rpx 0 14rpx;
}
.section-title text {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #10291b;
}
.section-subtitle {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.58);
}
</style>

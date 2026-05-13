<template>
  <view class="page-home">
    <view class="hero">
      <text class="title">XX甄选</text>
      <text class="subtitle">AI商品宣传图生成</text>
      <text class="intro">把实拍图变成可直接投放的商品海报</text>
    </view>

    <QuotaCard
      :summary="quotaSummary"
      :busy="quotaLoading"
      action-text="开始生成"
      @action="goToGenerate"
    />

    <view class="features">
      <view class="feature-card">
        <text class="feature-icon">📷</text>
        <text class="feature-title">拍照上传</text>
        <text class="feature-desc">拍摄商品实物照片</text>
      </view>
      <view class="feature-card">
        <text class="feature-icon">✅</text>
        <text class="feature-title">AI生成</text>
        <text class="feature-desc">一键生成宣传图</text>
      </view>
      <view class="feature-card">
        <text class="feature-icon">💾</text>
        <text class="feature-title">下载使用</text>
        <text class="feature-desc">保存到相册直接使用</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import QuotaCard from '@/components/quota/QuotaCard.vue'
import { getQuotaSummary } from '@/api/quota'
import { useUserStore } from '@/stores/user'
import type { QuotaSummary } from '@/types/generation'

const userStore = useUserStore()
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

function goToGenerate() {
  uni.switchTab({ url: '/pages/generate/index' })
}

onMounted(async () => {
  await userStore.ensureAuth()
  await loadQuotaSummary()
})
</script>

<style scoped>
.page-home {
  padding: 32rpx;
}
.hero {
  text-align: center;
  padding: 60rpx 0 32rpx;
}
.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
}
.subtitle {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-top: 16rpx;
}
.intro {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: rgba(16, 41, 27, 0.68);
}
.features {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}
.feature-card {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx 16rpx;
  text-align: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}
.feature-icon {
  font-size: 48rpx;
  display: block;
}
.feature-title {
  font-size: 28rpx;
  font-weight: 500;
  display: block;
  margin-top: 16rpx;
}
.feature-desc {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-top: 8rpx;
}
</style>

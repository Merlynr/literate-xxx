<template>
  <view class="quota-card">
    <view class="quota-head">
      <text class="eyebrow">剩余额度</text>
      <text class="plan">{{ summary?.active_plan_name || '默认套餐' }}</text>
    </view>
    <view class="quota-grid">
      <view class="metric">
        <text class="value">{{ summary?.available_units ?? '--' }}</text>
        <text class="label">可用</text>
      </view>
      <view class="metric">
        <text class="value">{{ summary?.frozen_units ?? '--' }}</text>
        <text class="label">冻结</text>
      </view>
      <view class="metric">
        <text class="value">{{ summary?.total_units ?? '--' }}</text>
        <text class="label">总量</text>
      </view>
    </view>
    <button class="cta" :disabled="busy" @tap="$emit('action')">
      {{ actionText }}
    </button>
  </view>
</template>

<script setup lang="ts">
import type { QuotaSummary } from '@/types/generation'

defineProps<{
  summary?: QuotaSummary | null
  busy?: boolean
  actionText?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.quota-card {
  padding: 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, rgba(31, 93, 58, 0.12), rgba(185, 139, 42, 0.12));
  border: 1rpx solid rgba(31, 93, 58, 0.12);
}
.quota-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.eyebrow {
  font-size: 22rpx;
  color: #1f5d3a;
  font-weight: 700;
}
.plan {
  font-size: 20rpx;
  color: rgba(16, 41, 27, 0.6);
}
.quota-grid {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
}
.metric {
  flex: 1;
  padding: 18rpx 12rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.7);
  text-align: center;
}
.value {
  display: block;
  font-size: 36rpx;
  font-weight: 900;
  color: #10291b;
}
.label {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: rgba(16, 41, 27, 0.6);
}
.cta {
  margin-top: 20rpx;
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
  color: #fff;
  border-radius: 20rpx;
  font-size: 26rpx;
  font-weight: 800;
}
</style>

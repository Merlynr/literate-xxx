<template>
  <scroll-view class="works-list" scroll-y refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="$emit('refresh')">
    <view v-if="items.length === 0" class="empty">
      <text class="empty-title">暂无作品</text>
      <text class="empty-desc">完成一次生成后，这里会显示你的历史作品。</text>
    </view>
    <view v-for="item in items" :key="item.job_id" class="work-row" @tap="$emit('preview', item)">
      <image v-if="item.source_preview_url" class="thumb" :src="item.source_preview_url" mode="aspectFill" />
      <view v-else class="thumb fallback">图</view>
      <view class="meta">
        <view class="title-row">
          <text class="status">{{ item.status }}</text>
          <text class="time">{{ formatTime(item.created_at) }}</text>
        </view>
        <text class="desc">{{ item.error_message || '点击查看结果预览' }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import type { GenerationHistoryItem } from '@/types/generation'

defineProps<{
  items: GenerationHistoryItem[]
  refreshing?: boolean
}>()

defineEmits<{
  refresh: []
  preview: [item: GenerationHistoryItem]
}>()

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.works-list {
  max-height: 70vh;
}
.empty {
  padding: 40rpx 20rpx;
  text-align: center;
}
.empty-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #10291b;
}
.empty-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.58);
}
.work-row {
  display: flex;
  gap: 16rpx;
  padding: 18rpx;
  margin-bottom: 14rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.76);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
}
.thumb,
.fallback {
  width: 110rpx;
  height: 110rpx;
  border-radius: 18rpx;
  flex-shrink: 0;
}
.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(31, 93, 58, 0.1);
  color: #1f5d3a;
  font-weight: 800;
}
.meta {
  flex: 1;
  min-width: 0;
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status {
  font-size: 24rpx;
  font-weight: 800;
  color: #1f5d3a;
}
.time {
  font-size: 20rpx;
  color: rgba(16, 41, 27, 0.5);
}
.desc {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.68);
}
</style>

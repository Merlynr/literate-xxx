<template>
  <view class="album-actions">
    <view class="header">
      <text class="title">保存到相册</text>
      <text class="subtitle">先授权，再保存原图或水印图</text>
    </view>
    <view class="buttons">
      <button class="ghost" :disabled="!rawUrl || busy" @tap="$emit('save', 'raw')">保存原图</button>
      <button class="ghost" :disabled="!watermarkedUrl || busy" @tap="$emit('save', 'watermarked')">保存水印图</button>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  rawUrl?: string | null
  watermarkedUrl?: string | null
  busy?: boolean
}>()

defineEmits<{
  save: [kind: 'raw' | 'watermarked']
}>()
</script>

<style scoped>
.album-actions {
  padding: 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.74);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
}
.title {
  font-size: 30rpx;
  font-weight: 900;
  color: #10291b;
}
.subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.58);
}
.buttons {
  display: flex;
  gap: 14rpx;
  margin-top: 16rpx;
}
.ghost {
  flex: 1;
  background: rgba(31, 93, 58, 0.08);
  color: #1f5d3a;
  border-radius: 18rpx;
  font-size: 24rpx;
  font-weight: 800;
}
</style>

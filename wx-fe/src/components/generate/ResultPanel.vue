<template>
  <view class="panel" v-if="watermarkedUrl || rawUrl">
    <view class="header">
      <text class="title">生成结果</text>
      <text class="subtitle">默认展示水印图，原图可切换查看</text>
    </view>

    <view class="primary">
      <image v-if="watermarkedUrl" class="image" :src="watermarkedUrl" mode="widthFix" />
      <view v-else class="empty">
        <text>结果尚未返回</text>
      </view>
    </view>

    <view class="thumbnails">
      <view class="thumb">
        <text class="thumb-label">水印图</text>
        <text class="thumb-url">{{ watermarkedUrl || '等待结果' }}</text>
      </view>
      <view class="thumb">
        <text class="thumb-label">原图</text>
        <text class="thumb-url">{{ rawUrl || '等待结果' }}</text>
      </view>
    </view>

    <view class="links">
      <button class="ghost" v-if="rawUrl" @tap="$emit('preview', rawUrl)">预览原图</button>
      <button class="solid" v-if="watermarkedUrl" @tap="$emit('preview', watermarkedUrl)">预览水印图</button>
    </view>

    <text v-if="jobId" class="job-id">任务编号 {{ jobId }}</text>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  jobId?: string
  rawUrl: string
  watermarkedUrl: string
}>()

defineEmits<{
  preview: [url: string]
}>()
</script>

<style scoped>
.panel {
  padding: 26rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
  box-shadow: 0 18rpx 42rpx rgba(38, 60, 44, 0.08);
}

.header {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.title {
  font-size: 32rpx;
  font-weight: 800;
  color: #10291b;
}

.subtitle {
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.6);
}

.primary {
  margin-top: 20rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: #f7f3ea;
}

.image {
  width: 100%;
}

.empty {
  min-height: 300rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(16, 41, 27, 0.55);
}

.thumbnails {
  display: grid;
  gap: 14rpx;
  margin-top: 18rpx;
}

.thumb {
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: rgba(31, 93, 58, 0.06);
}

.thumb-label {
  display: block;
  font-size: 22rpx;
  font-weight: 700;
  color: #1f5d3a;
}

.thumb-url {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: rgba(16, 41, 27, 0.54);
  word-break: break-all;
}

.links {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.ghost,
.solid {
  flex: 1;
  font-size: 24rpx;
  border-radius: 18rpx;
}

.ghost {
  background: rgba(31, 93, 58, 0.08);
  color: #1f5d3a;
}

.solid {
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
  color: #fff;
}

.job-id {
  display: block;
  margin-top: 14rpx;
  font-size: 20rpx;
  color: rgba(16, 41, 27, 0.55);
}
</style>

<template>
  <view class="panel">
    <view class="row">
      <text class="label">任务状态</text>
      <text class="value">{{ status }}</text>
    </view>
    <view class="progress-track">
      <view class="progress-fill" :style="{ width: `${progress}%` }" />
    </view>
    <text class="message">{{ message }}</text>
    <text v-if="jobId" class="job-id">任务编号 {{ jobId }}</text>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  status: string
  progress: number
  message: string
  jobId?: string
}>()
</script>

<style scoped>
.panel {
  padding: 26rpx;
  border-radius: 28rpx;
  background: rgba(18, 41, 27, 0.92);
  color: #f7f3ea;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-size: 24rpx;
  color: rgba(247, 243, 234, 0.68);
}

.value {
  font-size: 26rpx;
  font-weight: 700;
}

.progress-track {
  margin-top: 18rpx;
  height: 14rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.12);
}

.progress-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #d9b563, #f4e1a8);
}

.message {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
}

.job-id {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: rgba(247, 243, 234, 0.65);
}
</style>

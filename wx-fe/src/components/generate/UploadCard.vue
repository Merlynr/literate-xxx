<template>
  <view class="card">
    <view class="header">
      <view>
        <text class="title">{{ title }}</text>
        <text class="desc">{{ description }}</text>
      </view>
      <view class="badge" :class="{ busy }">{{ busy ? '处理中' : statusText }}</view>
    </view>

    <view class="preview" :class="{ empty: !imageUrl }">
      <image v-if="imageUrl" class="image" :src="imageUrl" mode="aspectFill" />
      <view v-else class="placeholder">
        <text class="icon">📷</text>
        <text class="placeholder-text">先上传一张产品实拍图</text>
      </view>
    </view>

    <button class="action" :disabled="busy" @tap="$emit('pick')">
      {{ buttonText }}
    </button>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
  imageUrl: string
  statusText: string
  buttonText: string
  busy?: boolean
}>()

defineEmits<{
  pick: []
}>()
</script>

<style scoped>
.card {
  padding: 28rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.8);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
  box-shadow: 0 18rpx 42rpx rgba(38, 60, 44, 0.08);
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  align-items: flex-start;
}

.title {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
  color: #10291b;
}

.desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.6);
}

.badge {
  font-size: 20rpx;
  color: #1f5d3a;
  background: rgba(31, 93, 58, 0.12);
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.badge.busy {
  color: #9a6b11;
  background: rgba(185, 139, 42, 0.14);
}

.preview {
  margin-top: 22rpx;
  border-radius: 28rpx;
  overflow: hidden;
  min-height: 320rpx;
  background: linear-gradient(180deg, rgba(31, 93, 58, 0.08), rgba(185, 139, 42, 0.06));
}

.preview.empty {
  border: 1rpx dashed rgba(18, 48, 32, 0.14);
}

.image {
  width: 100%;
  height: 320rpx;
}

.placeholder {
  height: 320rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.icon {
  font-size: 56rpx;
}

.placeholder-text {
  font-size: 24rpx;
  color: rgba(16, 41, 27, 0.54);
}

.action {
  margin-top: 22rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
}

.action[disabled] {
  opacity: 0.55;
}
</style>

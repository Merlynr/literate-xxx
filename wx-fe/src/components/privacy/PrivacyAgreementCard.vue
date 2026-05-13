<template>
  <view class="privacy-card">
    <view class="title-row">
      <text class="title">隐私协议</text>
      <text class="badge" :class="{ active: accepted }">
        {{ accepted ? '已同意' : '未同意' }}
      </text>
    </view>
    <text class="desc">
      首次生成前需要确认你已阅读并同意隐私协议与用户条款，协议状态会在本地和服务端同时记录。
    </text>
    <view class="actions">
      <button class="secondary" :disabled="busy || accepted" @tap="$emit('accept')">
        {{ accepted ? '已完成' : '同意协议' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  accepted: boolean
  busy?: boolean
}>()

defineEmits<{
  accept: []
}>()
</script>

<style scoped>
.privacy-card {
  padding: 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.74);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-size: 30rpx;
  font-weight: 900;
  color: #10291b;
}
.badge {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: #1f5d3a;
  background: rgba(31, 93, 58, 0.1);
}
.badge.active {
  color: #fff;
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
}
.desc {
  display: block;
  margin-top: 14rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: rgba(16, 41, 27, 0.66);
}
.actions {
  margin-top: 18rpx;
}
.secondary {
  background: rgba(31, 93, 58, 0.08);
  color: #1f5d3a;
  border-radius: 18rpx;
  font-size: 24rpx;
  font-weight: 800;
}
</style>

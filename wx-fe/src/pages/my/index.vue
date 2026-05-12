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
    <view class="menu">
      <view class="menu-item">
        <text>我的作品</text>
        <text class="arrow">→</text>
      </view>
      <view class="menu-item">
        <text>额度明细</text>
        <text class="arrow">→</text>
      </view>
      <view class="menu-item">
        <text>关于我们</text>
        <text class="arrow">→</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(async () => {
  await userStore.ensureAuth()
})
</script>

<style scoped>
.page-my {
  padding: 0;
}
.header {
  background: linear-gradient(135deg, #1AAD19, #12B7F5);
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
.menu {
  margin-top: 24rpx;
  background: #fff;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32rpx;
  border-bottom: 1rpx solid #f0f0f0;
  font-size: 28rpx;
}
.arrow {
  color: #ccc;
  font-size: 32rpx;
}
</style>

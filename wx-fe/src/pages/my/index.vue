<template>
  <view class="page-my">
    <view class="header">
      <view class="avatar-placeholder">
        <text>👤</text>
      </view>
      <text class="username">未登录</text>
    </view>
    <view class="menu">
      <view class="menu-item">
        <text>我的作品</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item">
        <text>额度明细</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item">
        <text>关于我们</text>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
// Profile page - Phase 2 will add WeChat login, Phase 4 will add works/credits
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
.username {
  font-size: 32rpx;
  color: #fff;
  font-weight: 500;
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
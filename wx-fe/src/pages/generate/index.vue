<template>
  <view class="page-generate">
    <view class="coming-soon">
      <text class="icon">🚀</text>
      <text class="title">AI生成向导</text>
      <text class="desc">选择类目 → 选择风格 → 上传照片 → 生成宣传图</text>
      <text class="hint">Phase 3 将实现完整向导流程</text>
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
.page-generate {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}
.coming-soon {
  text-align: center;
}
.icon {
  font-size: 80rpx;
  display: block;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  display: block;
  margin-top: 24rpx;
}
.desc {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-top: 16rpx;
}
.hint {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-top: 32rpx;
}
</style>

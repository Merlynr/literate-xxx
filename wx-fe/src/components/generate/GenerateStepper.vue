<template>
  <view class="stepper">
    <view
      v-for="(item, index) in steps"
      :key="item.key"
      class="step"
      :class="{ active: index <= currentIndex, done: index < currentIndex }"
    >
      <view class="dot">{{ index + 1 }}</view>
      <view class="meta">
        <text class="label">{{ item.label }}</text>
        <text class="desc">{{ item.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Stage = 'idle' | 'ready' | 'generating' | 'succeeded' | 'failed'

const props = defineProps<{
  stage: Stage
}>()

const steps = [
  { key: 'upload', label: '上传实拍图', desc: '确认资产后才能生成' },
  { key: 'configure', label: '选择类目/风格', desc: '冻结生成规则与提示词' },
  { key: 'result', label: '输出原图/水印图', desc: '双版本 OSS 结果' },
]

const currentIndex = computed(() => {
  switch (props.stage) {
    case 'idle':
      return 0
    case 'ready':
      return 1
    case 'generating':
      return 2
    case 'succeeded':
      return 2
    case 'failed':
      return 2
    default:
      return 0
  }
})
</script>

<style scoped>
.stepper {
  display: grid;
  gap: 20rpx;
}

.step {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 22rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.72);
  border: 1rpx solid rgba(30, 80, 50, 0.08);
}

.step.active {
  box-shadow: 0 16rpx 42rpx rgba(47, 86, 56, 0.12);
}

.step.done .dot {
  background: linear-gradient(135deg, #1f5d3a, #87b76b);
}

.dot {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, #b78d2a, #d9b563);
  flex-shrink: 0;
}

.meta {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 28rpx;
  color: #123020;
  font-weight: 700;
}

.desc {
  font-size: 22rpx;
  color: rgba(18, 48, 32, 0.62);
  margin-top: 6rpx;
}
</style>

<template>
  <view class="page">
    <view class="backdrop backdrop-a" />
    <view class="backdrop backdrop-b" />

    <view class="shell">
      <view class="hero">
        <text class="eyebrow">Phase 3 · AI Generation Pipeline</text>
        <text class="title">把实物图，变成能直接投放的宣传海报</text>
        <text class="subtitle">
          先上传实拍图，再选类目和风格。后端会冻结规则快照，输出原图和水印图两个 OSS 成品。
        </text>
      </view>

      <GenerateStepper :stage="generationStore.stage" />

      <view class="selection-grid">
        <view class="section">
          <view class="section-head">
            <text class="section-title">类目</text>
            <text class="section-desc">选择这次海报对应的商品类目</text>
          </view>
          <scroll-view scroll-x class="chips">
            <view
              v-for="category in generationStore.categories"
              :key="category.id"
              class="chip"
              :class="{ active: generationStore.selectedCategoryId === category.id }"
              @tap="generationStore.selectedCategoryId = category.id"
            >
              {{ category.name }}
            </view>
          </scroll-view>
        </view>

        <view class="section">
          <view class="section-head">
            <text class="section-title">风格</text>
            <text class="section-desc">参考图与画风会冻结到任务快照里</text>
          </view>
          <scroll-view scroll-x class="style-strip">
            <view
              v-for="style in generationStore.styles"
              :key="style.id"
              class="style-card"
              :class="{ active: generationStore.selectedStyleId === style.id }"
              @tap="generationStore.selectedStyleId = style.id"
            >
              <image v-if="style.cover_image_url" class="style-cover" :src="style.cover_image_url" mode="aspectFill" />
              <view class="style-fallback" v-else>风格</view>
              <text class="style-name">{{ style.name }}</text>
            </view>
          </scroll-view>
        </view>
      </view>

      <UploadCard
        title="上传实拍图"
        description="确认资产后才能创建生成任务"
        :image-url="generationStore.sourcePreviewUrl"
        :status-text="generationStore.sourceAsset ? '已确认' : '未上传'"
        :button-text="generationStore.sourceAsset ? '重新上传实拍图' : '选择并上传图片'"
        :busy="generationStore.busy"
        @pick="generationStore.pickAndUploadSourceImage"
      />

      <view class="note-card">
        <text class="note-title">补充提示</text>
        <textarea
          v-model="generationStore.promptHint"
          class="prompt"
          placeholder="例如：突出新鲜感、保留包装标签、整体更高级"
          maxlength="300"
        />
      </view>

      <view class="cta-bar">
        <button class="secondary" :disabled="generationStore.busy" @tap="generationStore.resetResultState">
          清空结果
        </button>
        <button class="primary" :disabled="!generationStore.canGenerate" @tap="generationStore.startGeneration">
          开始生成
        </button>
      </view>

      <ProgressPanel
        v-if="generationStore.stage === 'generating' || generationStore.currentJob"
        :status="generationStore.currentJob?.status || generationStore.stage"
        :progress="generationStore.progress"
        :message="generationStore.statusMessage"
        :job-id="generationStore.currentJob?.job_id"
      />

      <view v-if="generationStore.errorMessage" class="error-card">
        <text class="error-title">生成失败</text>
        <text class="error-text">{{ generationStore.errorMessage }}</text>
      </view>

      <ResultPanel
        v-if="generationStore.hasResult"
        :job-id="generationStore.currentJob?.job_id"
        :raw-url="generationStore.rawResultUrl"
        :watermarked-url="generationStore.watermarkedResultUrl"
        @preview="openPreview"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import GenerateStepper from '@/components/generate/GenerateStepper.vue'
import UploadCard from '@/components/generate/UploadCard.vue'
import ProgressPanel from '@/components/generate/ProgressPanel.vue'
import ResultPanel from '@/components/generate/ResultPanel.vue'
import { useUserStore } from '@/stores/user'
import { useGenerationStore } from '@/stores/generation'

const userStore = useUserStore()
const generationStore = useGenerationStore()

function openPreview(url: string) {
  if (!url) return
  uni.previewImage({
    urls: [url],
    current: url,
  })
}

onMounted(async () => {
  await userStore.ensureAuth()
  await generationStore.loadCatalogs()
})
</script>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
  padding: 24rpx 24rpx 60rpx;
  background:
    radial-gradient(circle at top left, rgba(185, 139, 42, 0.2), transparent 32%),
    radial-gradient(circle at top right, rgba(31, 93, 58, 0.16), transparent 28%),
    linear-gradient(180deg, #fbf7ef 0%, #f3ead8 52%, #eef3ee 100%);
}

.backdrop {
  position: absolute;
  border-radius: 999rpx;
  filter: blur(8rpx);
  opacity: 0.55;
  pointer-events: none;
}

.backdrop-a {
  width: 240rpx;
  height: 240rpx;
  background: rgba(31, 93, 58, 0.16);
  top: -60rpx;
  right: -70rpx;
}

.backdrop-b {
  width: 300rpx;
  height: 300rpx;
  background: rgba(185, 139, 42, 0.18);
  top: 320rpx;
  left: -120rpx;
}

.shell {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 24rpx;
}

.hero {
  padding: 24rpx 6rpx 8rpx;
}

.eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 2rpx;
  color: #1f5d3a;
  text-transform: uppercase;
}

.title {
  display: block;
  margin-top: 14rpx;
  font-size: 44rpx;
  font-weight: 900;
  line-height: 1.15;
  color: #10291b;
}

.subtitle {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(16, 41, 27, 0.68);
}

.selection-grid {
  display: grid;
  gap: 20rpx;
}

.section {
  padding: 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.7);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
  box-shadow: 0 16rpx 36rpx rgba(38, 60, 44, 0.07);
}

.section-head {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 18rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #10291b;
}

.section-desc {
  font-size: 22rpx;
  color: rgba(16, 41, 27, 0.58);
}

.chips {
  white-space: nowrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  margin-right: 14rpx;
  padding: 16rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(31, 93, 58, 0.08);
  color: #1f5d3a;
  font-size: 24rpx;
  font-weight: 700;
}

.chip.active {
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
  color: #fff;
  box-shadow: 0 10rpx 24rpx rgba(31, 93, 58, 0.18);
}

.style-strip {
  white-space: nowrap;
}

.style-card {
  display: inline-flex;
  flex-direction: column;
  width: 200rpx;
  margin-right: 14rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.78);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
}

.style-card.active {
  box-shadow: 0 16rpx 34rpx rgba(31, 93, 58, 0.16);
  border-color: rgba(31, 93, 58, 0.22);
}

.style-cover,
.style-fallback {
  width: 200rpx;
  height: 220rpx;
}

.style-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(31, 93, 58, 0.12), rgba(185, 139, 42, 0.12));
  color: #1f5d3a;
  font-size: 28rpx;
  font-weight: 700;
}

.style-name {
  padding: 18rpx 16rpx 20rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: #10291b;
}

.note-card {
  padding: 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.72);
  border: 1rpx solid rgba(18, 48, 32, 0.08);
}

.note-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #10291b;
}

.prompt {
  width: 100%;
  min-height: 160rpx;
  margin-top: 14rpx;
  padding: 18rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  background: #fff;
  color: #10291b;
  font-size: 24rpx;
  line-height: 1.7;
}

.cta-bar {
  display: flex;
  gap: 14rpx;
}

.primary,
.secondary {
  flex: 1;
  border-radius: 20rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.primary {
  background: linear-gradient(135deg, #1f5d3a, #2d7d4d);
  color: #fff;
}

.secondary {
  background: rgba(31, 93, 58, 0.08);
  color: #1f5d3a;
}

.primary[disabled],
.secondary[disabled] {
  opacity: 0.55;
}

.error-card {
  padding: 22rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(158, 51, 27, 0.1);
  color: #9e331b;
}

.error-title {
  display: block;
  font-size: 26rpx;
  font-weight: 800;
}

.error-text {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
}
</style>

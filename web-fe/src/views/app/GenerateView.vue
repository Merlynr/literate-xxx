<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useGenerationStore } from '@/stores/generation'
import { useUserStore } from '@/stores/user'

const gen = useGenerationStore()
const userStore = useUserStore()
const fileInput = ref<HTMLInputElement | null>(null)
const previewTab = ref<'watermark' | 'raw' | 'source'>('watermark')
const privacyChecked = ref(false)

onMounted(async () => {
  await gen.loadCatalogs()
  privacyChecked.value = userStore.hasPrivacyAgreement
})

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  await gen.uploadFile(file)
}

async function acceptPrivacy() {
  await gen.acceptPrivacyAgreement()
  privacyChecked.value = true
}

const previewUrl = () => {
  const job = gen.currentJob
  if (previewTab.value === 'source') return gen.sourcePreviewUrl
  if (previewTab.value === 'raw') return job?.raw_result_download_url
  return job?.watermarked_result_download_url || gen.sourcePreviewUrl
}
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <header class="mb-6">
      <p class="eyebrow">NEW GENERATION</p>
      <h1 class="text-2xl font-bold">创建商品图任务</h1>
    </header>

    <div class="flex flex-col gap-6 xl:flex-row">
      <div class="page-card w-full shrink-0 space-y-5 p-5 xl:w-80">
        <el-alert
          v-if="!userStore.hasPrivacyAgreement"
          title="首次生成前需同意隐私协议"
          type="warning"
          :closable="false"
        />
        <el-checkbox v-if="!userStore.hasPrivacyAgreement" v-model="privacyChecked">
          我已阅读并同意隐私协议
        </el-checkbox>
        <el-button
          v-if="!userStore.hasPrivacyAgreement && privacyChecked"
          size="small"
          class="mt-2"
          @click="acceptPrivacy"
        >
          确认协议
        </el-button>

        <div>
          <label class="mb-1 block text-sm font-medium">商品名称（可选）</label>
          <el-input v-model="gen.productName" placeholder="例如：红皮土豆 5斤装" />
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">出图类型</label>
          <el-radio-group v-model="gen.outputType" class="flex flex-col gap-2">
            <el-radio value="white">白底主图</el-radio>
            <el-radio value="scene">场景图</el-radio>
            <el-radio value="detail">详情页图</el-radio>
          </el-radio-group>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">类目</label>
          <el-select v-model="gen.selectedCategoryId" class="w-full" @change="gen.refreshEstimate()">
            <el-option
              v-for="c in gen.categories"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">风格</label>
          <el-select v-model="gen.selectedStyleId" class="w-full" @change="gen.refreshEstimate()">
            <el-option v-for="s in gen.styles" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">上传实拍图</label>
          <div
            class="cursor-pointer rounded-xl border-2 border-dashed border-brand-700/25 bg-cream-50 p-6 text-center text-sm text-brand-900/60 hover:border-gold-600"
            @click="pickFile"
          >
            点击或拖拽上传<br />
            <span class="text-xs">建议正面、侧面、细节图</span>
          </div>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">画面要求</label>
          <el-input
            v-model="gen.promptHint"
            type="textarea"
            :rows="3"
            maxlength="300"
            show-word-limit
            placeholder="例如：突出新鲜感、保留包装标签"
            @blur="gen.refreshEstimate()"
          />
        </div>

        <p v-if="gen.estimatedUnits != null" class="text-sm text-gold-600">
          预计消耗 {{ gen.estimatedUnits }} 张额度
        </p>

        <el-button
          type="primary"
          class="w-full"
          size="large"
          :disabled="!gen.canGenerate"
          :loading="gen.busy"
          @click="gen.startGeneration()"
        >
          开始 AI 生成
        </el-button>
        <p class="text-center text-xs text-brand-900/50">{{ gen.statusMessage }}</p>
        <el-progress v-if="gen.stage === 'generating'" :percentage="gen.progress" />
        <el-alert v-if="gen.errorMessage" :title="gen.errorMessage" type="error" show-icon />
      </div>

      <div class="page-card min-h-[480px] flex-1 p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="font-semibold">Smart Preview</p>
          <el-radio-group v-model="previewTab" size="small">
            <el-radio-button value="source">源图</el-radio-button>
            <el-radio-button value="watermark" :disabled="!gen.hasResult">水印</el-radio-button>
            <el-radio-button value="raw" :disabled="!gen.currentJob?.raw_result_download_url">
              原图
            </el-radio-button>
          </el-radio-group>
        </div>
        <div
          class="flex min-h-[400px] items-center justify-center overflow-hidden rounded-xl bg-cream-100"
        >
          <img
            v-if="previewUrl()"
            :src="previewUrl()!"
            class="max-h-[70vh] max-w-full object-contain"
            alt="preview"
          />
          <p v-else class="text-sm text-brand-900/40">上传图片后在此预览</p>
        </div>
        <div v-if="gen.hasResult" class="mt-4 flex gap-2">
          <a
            v-if="gen.currentJob?.watermarked_result_download_url"
            :href="gen.currentJob.watermarked_result_download_url"
            target="_blank"
            class="btn-primary text-sm"
          >
            下载水印图
          </a>
          <a
            v-if="gen.currentJob?.raw_result_download_url"
            :href="gen.currentJob.raw_result_download_url"
            target="_blank"
            class="rounded-xl border px-4 py-2 text-sm"
          >
            下载原图
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

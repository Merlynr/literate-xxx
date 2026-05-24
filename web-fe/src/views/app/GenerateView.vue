<script setup lang="ts">
import { onActivated, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import CachedImage from '@/components/CachedImage.vue'
import { useGenerationStore } from '@/stores/generation'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const gen = useGenerationStore()
const userStore = useUserStore()
const fileInput = ref<HTMLInputElement | null>(null)
const privacyChecked = ref(false)

async function bootstrapGeneratePage() {
  gen.prepareGeneratePage()
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  await gen.loadCatalogs()
  privacyChecked.value = userStore.hasPrivacyAgreement
}

onMounted(bootstrapGeneratePage)
onActivated(bootstrapGeneratePage)

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  if (!files.length) return
  await gen.uploadFiles(files)
  input.value = ''
}

function selectSourcePreview(index: number) {
  gen.activeSourcePreviewIndex = index
}

async function acceptPrivacy() {
  await gen.acceptPrivacyAgreement()
  privacyChecked.value = true
}

async function submitGeneration() {
  try {
    await gen.startGeneration()
    ElMessage.success({
      message: '任务已提交，请在「生成任务」查看进度',
      duration: 4000,
    })
    router.push('/app/works/tasks')
  } catch {
    /* errorMessage 已在 store */
  }
}
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <header class="mb-6">
      <p class="eyebrow">NEW GENERATION</p>
      <h1 class="text-2xl font-bold">创建商品图任务</h1>
      <p class="mt-1 text-sm text-brand-900/60">提交后本页会清空，进度请在「生成任务」查看</p>
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
          <label class="mb-1 block text-sm font-medium">
            上传实拍图
            <span class="text-xs text-brand-900/50">
              （{{ gen.sourceAssets.length }}/{{ gen.maxSourceAssets }}）
            </span>
          </label>
          <div
            class="cursor-pointer rounded-xl border-2 border-dashed border-brand-700/25 bg-cream-50 p-6 text-center text-sm text-brand-900/60 hover:border-gold-600"
            @click="pickFile"
          >
            点击选择图片，可一次选多张<br />
            <span class="text-xs">建议上传正面、侧面、细节图</span>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="onFileChange"
          />
          <div v-if="gen.sourceAssets.length" class="mt-3 grid grid-cols-3 gap-2">
            <div
              v-for="(asset, index) in gen.sourceAssets"
              :key="asset.asset_id"
              class="relative overflow-hidden rounded-lg border"
              :class="gen.activeSourcePreviewIndex === index ? 'border-gold-600 ring-2 ring-gold-200' : 'border-brand-700/10'"
              @click="selectSourcePreview(index)"
            >
              <CachedImage
                :src="asset.download_url"
                :cache-key="`asset:${asset.asset_id}`"
                img-class="aspect-square w-full object-cover"
                alt="source"
              />
              <button
                type="button"
                class="absolute right-1 top-1 rounded bg-black/55 px-1.5 py-0.5 text-xs text-white"
                @click.stop="gen.removeSourceAsset(index)"
              >
                删除
              </button>
            </div>
          </div>
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
          @click="submitGeneration"
        >
          开始 AI 生成
        </el-button>
        <p class="text-center text-xs text-brand-900/50">{{ gen.statusMessage }}</p>
        <el-alert v-if="gen.errorMessage" :title="gen.errorMessage" type="error" show-icon />
      </div>

      <div class="page-card min-h-[480px] flex-1 p-4">
        <p class="mb-3 font-semibold">上传预览</p>
        <div
          class="flex min-h-[400px] items-center justify-center overflow-hidden rounded-xl bg-cream-100"
        >
          <CachedImage
            v-if="gen.sourcePreviewUrl"
            :src="gen.sourcePreviewUrl"
            :cache-key="`upload:${gen.sourceAssets[gen.activeSourcePreviewIndex]?.asset_id}`"
            img-class="max-h-[70vh] max-w-full object-contain"
            alt="preview"
          />
          <p v-else class="text-sm text-brand-900/40">上传图片后在此预览</p>
        </div>
      </div>
    </div>
  </div>
</template>

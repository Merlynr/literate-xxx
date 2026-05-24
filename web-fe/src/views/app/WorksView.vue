<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import JobStatusBadge from '@/components/JobStatusBadge.vue'
import { useGenerationStore } from '@/stores/generation'

const props = defineProps<{ tab?: string }>()
const route = useRoute()
const router = useRouter()
const gen = useGenerationStore()
const statusFilter = ref('')
const loading = ref(false)

const activeTab = computed(() => props.tab || (route.path.includes('tasks') ? 'tasks' : 'gallery'))

onMounted(async () => {
  loading.value = true
  await gen.loadHistory()
  loading.value = false
})

const filtered = computed(() => {
  if (!statusFilter.value) return gen.historyItems
  return gen.historyItems.filter((i) => i.status === statusFilter.value)
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="mb-6">
      <p class="eyebrow">{{ activeTab === 'tasks' ? 'GENERATION QUEUE' : 'FINISHED ASSETS' }}</p>
      <h1 class="text-2xl font-bold">{{ activeTab === 'tasks' ? '生成任务' : '成品图库' }}</h1>
      <p v-if="activeTab === 'gallery'" class="mt-1 text-sm text-brand-900/60">
        建议按商品系列下载后上传至淘宝、抖店和小红书素材库
      </p>
    </header>

    <div class="mb-4 flex flex-wrap gap-3">
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 160px">
        <el-option label="排队中" value="queued" />
        <el-option label="生成中" value="running" />
        <el-option label="成功" value="succeeded" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button :loading="loading" @click="gen.loadHistory()">刷新</el-button>
      <router-link to="/app/works/completed">
        <el-button>已完成任务</el-button>
      </router-link>
      <router-link to="/app/generate">
        <el-button type="primary">创建更多成品</el-button>
      </router-link>
    </div>

    <el-skeleton v-if="loading" :rows="4" animated />
    <div v-else-if="!filtered.length" class="page-card p-12 text-center text-brand-900/50">
      暂无作品
    </div>
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="item in filtered" :key="item.job_id" class="page-card overflow-hidden">
        <a
          :href="item.watermarked_result_download_url || item.source_preview_url || '#'"
          target="_blank"
        >
          <img
            v-if="item.watermarked_result_download_url || item.source_preview_url"
            :src="(item.watermarked_result_download_url || item.source_preview_url)!"
            class="aspect-square w-full object-cover"
            alt=""
          />
        </a>
        <div class="p-3">
          <JobStatusBadge :status="item.status" />
          <p class="mt-2 truncate text-xs text-brand-900/50">{{ item.job_id }}</p>
          <p class="text-xs text-brand-900/40">{{ new Date(item.created_at).toLocaleString() }}</p>
          <p v-if="item.error_message" class="mt-1 text-xs text-red-700">{{ item.error_message }}</p>
          <el-button
            v-if="item.status === 'succeeded'"
            link
            type="primary"
            class="mt-2"
            @click="router.push({ name: 'app-work-detail', params: { jobId: item.job_id } })"
          >
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

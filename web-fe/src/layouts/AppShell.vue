<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Grid,
  HomeFilled,
  Plus,
  Setting,
  Star,
  SwitchButton,
} from '@element-plus/icons-vue'
import BrandLogo from '@/components/BrandLogo.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const nav = [
  { path: '/app/dashboard', label: '工作台', icon: HomeFilled },
  { path: '/app/generate', label: '发起生成', icon: Plus },
  { path: '/app/works/tasks', label: '生成任务', icon: Grid },
  { path: '/app/works/completed', label: '已完成任务', icon: Grid },
  { path: '/app/works', label: '成品图库', icon: Grid },
  { path: '/app/modules', label: '可定制模块', icon: Star },
  { path: '/app/account', label: '客户配置', icon: Setting },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function logout() {
  userStore.logout()
  router.push('/app/login')
}

onMounted(() => {
  userStore.bootstrap()
})
</script>

<template>
  <div class="flex min-h-screen">
    <aside
      class="flex w-60 shrink-0 flex-col border-r border-brand-700/10 bg-white/80 px-4 py-6 backdrop-blur"
    >
      <BrandLogo subtitle="商品图 AI 工作台" class="mb-8 px-2" />
      <p class="mb-4 px-2 text-xs text-brand-900/50">CLIENT PORTAL</p>
      <nav class="flex flex-1 flex-col gap-1">
        <router-link
          v-for="item in nav"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm transition"
          :class="
            isActive(item.path)
              ? 'bg-brand-700/10 font-semibold text-brand-700'
              : 'text-brand-900/70 hover:bg-cream-100'
          "
        >
          <el-icon><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
      </nav>
      <div class="mt-4 border-t border-brand-700/10 pt-4">
        <p class="truncate px-2 text-sm font-medium">
          {{ userStore.profile?.nickname || '未登录' }}
        </p>
        <p class="truncate px-2 text-xs text-brand-900/50">
          {{ userStore.profile?.tenant_id?.slice(0, 8) }}…
        </p>
        <button
          type="button"
          class="mt-3 flex w-full items-center justify-center gap-1 rounded-xl border border-brand-700/15 py-2 text-sm text-brand-900/70 hover:bg-cream-50"
          @click="logout"
        >
          <el-icon><SwitchButton /></el-icon>
          退出
        </button>
      </div>
    </aside>
    <main class="flex-1 overflow-auto p-6 lg:p-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Coin,
  Document,
  Grid,
  Histogram,
  List,
  SwitchButton,
  Tickets,
} from '@element-plus/icons-vue'
import BrandLogo from '@/components/BrandLogo.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const nav = [
  { path: '/admin/dashboard', label: '运营概览', icon: Histogram },
  { path: '/admin/catalog/categories', label: '商品类目', icon: List },
  { path: '/admin/catalog/styles', label: '风格模板', icon: Grid },
  { path: '/admin/content/terms', label: '词条库', icon: Document },
  { path: '/admin/content/promo-rules', label: '宣传规则', icon: Tickets },
  { path: '/admin/billing/pricing-plans', label: '定价套餐', icon: Coin },
  { path: '/admin/billing/quota-ledger', label: '额度流水', icon: Coin },
  { path: '/admin/jobs', label: '生成任务', icon: Grid },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}

function logout() {
  userStore.logout()
  router.push('/admin/login')
}

onMounted(() => userStore.bootstrap())
</script>

<template>
  <div class="flex min-h-screen bg-slate-50">
    <aside class="flex w-56 shrink-0 flex-col bg-slate-900 px-3 py-5 text-slate-200">
      <div class="mb-6 px-2 text-white">
        <BrandLogo subtitle="运营后台" size="sm" />
      </div>
      <nav class="flex flex-1 flex-col gap-0.5">
        <router-link
          v-for="item in nav"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition"
          :class="isActive(item.path) ? 'bg-slate-700 text-white' : 'hover:bg-slate-800'"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
      </nav>
      <button
        type="button"
        class="mt-4 flex items-center justify-center gap-1 rounded-lg border border-slate-600 py-2 text-sm hover:bg-slate-800"
        @click="logout"
      >
        <el-icon><SwitchButton /></el-icon>
        退出
      </button>
    </aside>
    <main class="flex-1 overflow-auto p-6">
      <router-view />
    </main>
  </div>
</template>

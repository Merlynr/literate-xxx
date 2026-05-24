<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const nickname = ref('商家用户')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await userStore.loginAs(nickname.value.trim() || '商家用户')
    router.push('/app/dashboard')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-cream-50 via-cream-100 to-cream-200 p-6">
    <div class="page-card w-full max-w-md p-8">
      <div class="mb-8 flex justify-center">
        <BrandLogo subtitle="商品图 AI 工作台" />
      </div>
      <p class="eyebrow mb-1 text-center">CLIENT PORTAL</p>
      <h1 class="mb-6 text-center text-xl font-bold text-brand-900">登录商家工作台</h1>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="显示名称（开发模式）">
          <el-input v-model="nickname" placeholder="商家昵称" />
        </el-form-item>
        <el-alert
          v-if="error"
          type="error"
          :title="error"
          show-icon
          class="mb-4"
          :closable="false"
        />
        <el-button type="primary" class="w-full" native-type="submit" :loading="userStore.loading">
          登录
        </el-button>
      </el-form>
      <p class="mt-6 text-center text-xs text-brand-900/50">
        使用 BFF <code class="rounded bg-cream-100 px-1">/auth/dev-login</code>（需 DEBUG=true）
      </p>
      <p class="mt-4 text-center text-sm">
        <router-link to="/admin/login" class="text-brand-700 underline">进入运营后台 →</router-link>
      </p>
    </div>
  </div>
</template>

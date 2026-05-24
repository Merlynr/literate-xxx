<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const nickname = ref('运营管理员')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await userStore.loginAs(nickname.value.trim() || '运营管理员')
    router.push('/admin/dashboard')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-900 p-6">
    <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
      <BrandLogo subtitle="运营后台" class="mb-6 justify-center" />
      <h1 class="mb-6 text-center text-xl font-bold">运营登录</h1>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="显示名称（开发模式）">
          <el-input v-model="nickname" />
        </el-form-item>
        <el-alert v-if="error" type="error" :title="error" class="mb-4" show-icon />
        <el-button type="primary" class="w-full" native-type="submit" :loading="userStore.loading">
          登录
        </el-button>
      </el-form>
      <p class="mt-4 text-center text-sm">
        <router-link to="/app/login" class="text-brand-700 underline">返回商家工作台</router-link>
      </p>
    </div>
  </div>
</template>

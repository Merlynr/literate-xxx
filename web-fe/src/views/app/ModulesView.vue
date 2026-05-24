<script setup lang="ts">
const modules = [
  {
    title: '资料整理与文案',
    desc: '资料整理、文案生成、任务分发自动化',
  },
  {
    title: '多模型初稿',
    desc: '即梦 API / 豆包 API 初稿生成（路线图）',
  },
  {
    title: '店铺分析',
    desc: '商品、内容、店铺分析建议',
  },
  {
    title: '工具链连接',
    desc: '连接资料库、表格和工具链',
  },
  {
    title: '视觉 SOP',
    desc: '沉淀视觉规则和交付 SOP',
  },
]
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <header class="mb-6">
      <p class="eyebrow">PAID ADD-ONS</p>
      <h1 class="text-2xl font-bold">可定制增值模块</h1>
      <p class="mt-1 text-sm text-brand-900/60">Web 端扩展能力，按业务优先级逐步接入</p>
    </header>
    <div class="grid gap-4 md:grid-cols-2">
      <div v-for="m in modules" :key="m.title" class="page-card p-5">
        <h3 class="font-bold text-brand-700">{{ m.title }}</h3>
        <p class="mt-2 text-sm text-brand-900/65">{{ m.desc }}</p>
        <el-tag class="mt-3" type="info" size="small">规划中</el-tag>
      </div>
    </div>
  </div>
</template>

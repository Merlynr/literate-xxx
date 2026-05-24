<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const type = computed(() => {
  switch (props.status) {
    case 'succeeded':
      return 'success'
    case 'failed':
      return 'danger'
    case 'running':
      return 'warning'
    default:
      return 'info'
  }
})

const label = computed(() => {
  const map: Record<string, string> = {
    queued: '排队中',
    running: '生成中',
    succeeded: '成功',
    failed: '失败',
  }
  return map[props.status] || props.status
})
</script>

<template>
  <el-tag :type="type" size="small">{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useGenerationStore } from '@/stores/generation'

const props = withDefaults(
  defineProps<{
    jobId: string
    status: string
    variant?: 'icon' | 'text'
  }>(),
  { variant: 'icon' },
)

const emit = defineEmits<{ deleted: [] }>()

const gen = useGenerationStore()
const deleting = ref(false)

function confirmMessage() {
  if (props.status === 'queued') {
    return '将移除此排队任务；若额度仍处于冻结状态，会尝试退回。此操作不可撤销。'
  }
  if (props.status === 'failed') {
    return '将移除此失败任务记录。此操作不可撤销。'
  }
  return '将移除此任务及列表中的展示记录，OSS 上的图片文件不会自动删除。此操作不可撤销。'
}

async function handleClick(event: Event) {
  event.preventDefault()
  event.stopPropagation()

  if (props.status === 'running') {
    await ElMessageBox.alert('任务正在生成中，请等待完成或失败后再删除。', '暂无法删除', {
      type: 'warning',
      confirmButtonText: '知道了',
    })
    return
  }

  try {
    await ElMessageBox.confirm(confirmMessage(), '确认删除任务？', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
      autofocus: false,
    })
  } catch {
    return
  }

  deleting.value = true
  try {
    await gen.deleteJob(props.jobId)
    ElMessage.success({ message: '任务已删除', duration: 2000 })
    emit('deleted')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <el-button
    v-if="variant === 'text'"
    link
    type="danger"
    size="small"
    :loading="deleting"
    @click="handleClick"
  >
    删除
  </el-button>
  <button
    v-else
    type="button"
    class="job-delete-fab"
    :class="{ 'is-loading': deleting }"
    :disabled="deleting"
    aria-label="删除任务"
    @click="handleClick"
  >
    <el-icon v-if="!deleting" :size="16"><Delete /></el-icon>
    <span v-else class="job-delete-spinner" />
  </button>
</template>

<style scoped>
.job-delete-fab {
  display: flex;
  height: 2rem;
  width: 2rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: none;
  background: rgb(255 255 255 / 0.92);
  color: #b42318;
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.12);
  cursor: pointer;
  transition:
    transform 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.job-delete-fab:hover:not(:disabled) {
  transform: scale(1.05);
  background: #fff;
  box-shadow: 0 4px 12px rgb(0 0 0 / 0.16);
}

.job-delete-fab:disabled {
  cursor: wait;
  opacity: 0.85;
}

.job-delete-spinner {
  height: 0.875rem;
  width: 0.875rem;
  border-radius: 9999px;
  border: 2px solid rgb(180 35 24 / 0.25);
  border-top-color: #b42318;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

<script setup lang="ts">
defineProps<{ subtitle?: string; size?: 'sm' | 'md' }>()
</script>

<template>
  <div class="flex items-center gap-3">
    <div
      class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-500 text-lg font-bold text-white shadow"
      :class="size === 'sm' ? 'h-8 w-8 text-sm' : ''"
    >
      甄
    </div>
    <div>
      <div class="text-base font-bold text-brand-900">XX甄选</div>
      <div v-if="subtitle" class="text-xs text-brand-900/60">{{ subtitle }}</div>
    </div>
  </div>
</template>

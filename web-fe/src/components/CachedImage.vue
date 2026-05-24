<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { getCachedImageSrc, imageCacheKey } from '@/utils/imageCache'

const props = withDefaults(
  defineProps<{
    src?: string | null
    jobId?: string
    imageRole?: 'source' | 'raw' | 'watermark' | 'preview'
    cacheKey?: string
    reloadKey?: number
    alt?: string
    imgClass?: string
  }>(),
  { alt: '' },
)

const displaySrc = ref('')

function resolveCacheKey(url: string) {
  if (props.cacheKey) return props.cacheKey
  if (props.jobId && props.imageRole) return imageCacheKey(props.jobId, props.imageRole)
  return `url:${url}`
}

async function load(force = false) {
  const url = props.src?.trim()
  if (!url) {
    displaySrc.value = ''
    return
  }
  const key = resolveCacheKey(url)
  try {
    displaySrc.value = await getCachedImageSrc(url, key, { force })
  } catch {
    displaySrc.value = url
  }
}

watch(
  () => [props.src, props.jobId, props.imageRole, props.cacheKey, props.reloadKey] as const,
  () => {
    void load(!!props.reloadKey)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  displaySrc.value = ''
})
</script>

<template>
  <img v-if="displaySrc" :src="displaySrc" :class="imgClass" :alt="alt" />
</template>

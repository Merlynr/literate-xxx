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

function isHttpUrl(url: string) {
  return url.startsWith('http://') || url.startsWith('https://')
}

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
    // OSS 预签名常无 CORS；<img> 直链仍可显示，勿留空
    displaySrc.value = isHttpUrl(url) ? url : ''
  }
}

/** 预签名 URL 每次轮询会变 query，不应因此重复拉取 */
watch(
  () =>
    [
      props.jobId,
      props.imageRole,
      props.cacheKey,
      props.reloadKey,
      Boolean(props.src?.trim()),
    ] as const,
  () => {
    void load(props.reloadKey != null && props.reloadKey > 0)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  displaySrc.value = ''
})
</script>

<template>
  <img
    v-if="displaySrc"
    :src="displaySrc"
    :class="imgClass"
    :alt="alt"
    referrerpolicy="no-referrer"
    loading="lazy"
  />
</template>

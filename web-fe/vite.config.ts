import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    // element-plus → @vueuse 在 Rolldown 下可能打 INVALID_ANNOTATION 警告，可忽略
    chunkSizeWarningLimit: 1200,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://8.141.7.56:8000',
        changeOrigin: true,
      },
    },
  },
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clearTokens, getAccessToken } from '@/api/request'
import { devLogin, getMe } from '@/api/auth'
import { getPrivacyStatus } from '@/api/privacy'
import type { UserProfile } from '@/types'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)
  const privacyAcceptedAt = ref<string | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!profile.value && !!getAccessToken())
  const hasPrivacyAgreement = computed(
    () => !!privacyAcceptedAt.value || !!profile.value?.privacy_accepted_at,
  )

  async function loginAs(nickname: string) {
    loading.value = true
    try {
      await devLogin(nickname)
      await bootstrap()
    } finally {
      loading.value = false
    }
  }

  async function bootstrap() {
    if (!getAccessToken()) return
    profile.value = await getMe()
    privacyAcceptedAt.value = profile.value.privacy_accepted_at || null
    if (!privacyAcceptedAt.value) {
      const status = await getPrivacyStatus()
      privacyAcceptedAt.value = status.privacy_accepted_at || null
    }
  }

  function logout() {
    profile.value = null
    privacyAcceptedAt.value = null
    clearTokens()
  }

  return {
    profile,
    privacyAcceptedAt,
    loading,
    isLoggedIn,
    hasPrivacyAgreement,
    loginAs,
    bootstrap,
    logout,
  }
})

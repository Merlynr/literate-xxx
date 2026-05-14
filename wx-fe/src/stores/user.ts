import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { devLogin as apiDevLogin, getMe, login as apiLogin, refreshToken as apiRefresh } from '../api/auth'
import { clearTokens, setTokenPair } from '../api/request'

const ACCESS_TOKEN_KEY = 'xxzx_access_token'
const REFRESH_TOKEN_KEY = 'xxzx_refresh_token'

export const useUserStore = defineStore('user', () => {
  const accessToken = ref('')
  const refreshTokenValue = ref('')
  const nickname = ref('')
  const tenantId = ref('')
  const userId = ref('')
  const privacyAcceptedAt = ref('')
  const isLoggedIn = computed(() => !!accessToken.value)
  const hasPrivacyAgreement = computed(() => !!privacyAcceptedAt.value)

  function applyProfile(profile: Awaited<ReturnType<typeof getMe>>) {
    nickname.value = profile.nickname
    tenantId.value = profile.tenant_id
    userId.value = profile.id
    privacyAcceptedAt.value = profile.privacy_accepted_at || ''
  }

  function loadTokens() {
    accessToken.value = uni.getStorageSync(ACCESS_TOKEN_KEY) || ''
    refreshTokenValue.value = uni.getStorageSync(REFRESH_TOKEN_KEY) || ''
    setTokenPair(accessToken.value, refreshTokenValue.value)
  }

  function saveTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshTokenValue.value = refresh
    uni.setStorageSync(ACCESS_TOKEN_KEY, access)
    uni.setStorageSync(REFRESH_TOKEN_KEY, refresh)
    setTokenPair(access, refresh)
  }

  function clearAuth() {
    accessToken.value = ''
    refreshTokenValue.value = ''
    nickname.value = ''
    tenantId.value = ''
    userId.value = ''
    privacyAcceptedAt.value = ''
    uni.removeStorageSync(ACCESS_TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
    clearTokens()
  }

  async function wxLogin(): Promise<boolean> {
    return new Promise((resolve) => {
      uni.login({
        provider: 'weixin',
        success: async (loginRes) => {
          try {
            const tokens = await apiLogin(loginRes.code)
            saveTokens(tokens.access_token, tokens.refresh_token)
            const profile = await getMe()
            applyProfile(profile)
            resolve(true)
          } catch (e) {
            console.warn('WeChat login failed, falling back to dev login:', e)
            try {
              const tokens = await apiDevLogin({ nickname: '本地调试' })
              saveTokens(tokens.access_token, tokens.refresh_token)
              const profile = await getMe()
              applyProfile(profile)
              resolve(true)
            } catch (devError) {
              console.error('Dev login failed:', devError)
              resolve(false)
            }
          }
        },
        fail: (err) => {
          console.warn('wx.login failed, falling back to dev login:', err)
          apiDevLogin({ nickname: '本地调试' })
            .then(async (tokens) => {
              saveTokens(tokens.access_token, tokens.refresh_token)
              const profile = await getMe()
              applyProfile(profile)
              resolve(true)
            })
            .catch((devError) => {
              console.error('Dev login failed:', devError)
              resolve(false)
            })
        },
      })
    })
  }

  async function tryRefreshToken(): Promise<boolean> {
    if (!refreshTokenValue.value) return false
    try {
      const tokens = await apiRefresh(refreshTokenValue.value)
      saveTokens(tokens.access_token, tokens.refresh_token)
      return true
    } catch (e) {
      console.error('Token refresh failed:', e)
      clearAuth()
      return false
    }
  }

  async function checkAndRelogin(): Promise<boolean> {
    return new Promise((resolve) => {
      uni.checkSession({
        success: () => resolve(true),
        fail: async () => {
          console.log('WeChat session expired, re-logging in...')
          clearAuth()
          const ok = await wxLogin()
          resolve(ok)
        },
      })
    })
  }

  async function ensureAuth(): Promise<boolean> {
    loadTokens()
    if (!accessToken.value) {
      return await wxLogin()
    }
    const sessionOk = await checkAndRelogin()
    if (!sessionOk) return false
    const profile = await getMe()
    applyProfile(profile)
    return true
  }

  return {
    accessToken,
    refreshTokenValue,
    nickname,
    tenantId,
    userId,
    privacyAcceptedAt,
    isLoggedIn,
    hasPrivacyAgreement,
    loadTokens,
    saveTokens,
    clearAuth,
    wxLogin,
    tryRefreshToken,
    checkAndRelogin,
    ensureAuth,
  }
})

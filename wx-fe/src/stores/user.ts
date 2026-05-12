import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, refreshToken as apiRefresh, getMe } from '../api/auth'
import { setToken } from '../api/request'

const ACCESS_TOKEN_KEY = 'xxzx_access_token'
const REFRESH_TOKEN_KEY = 'xxzx_refresh_token'

export const useUserStore = defineStore('user', () => {
  const accessToken = ref('')
  const refreshTokenValue = ref('')
  const nickname = ref('')
  const tenantId = ref('')
  const userId = ref('')
  const isLoggedIn = computed(() => !!accessToken.value)

  /** Load tokens from storage on app start */
  function loadTokens() {
    accessToken.value = uni.getStorageSync(ACCESS_TOKEN_KEY) || ''
    refreshTokenValue.value = uni.getStorageSync(REFRESH_TOKEN_KEY) || ''
    if (accessToken.value) {
      setToken(accessToken.value)
    }
  }

  /** Persist tokens to storage */
  function saveTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshTokenValue.value = refresh
    uni.setStorageSync(ACCESS_TOKEN_KEY, access)
    uni.setStorageSync(REFRESH_TOKEN_KEY, refresh)
    setToken(access)
  }

  /** Clear all auth state */
  function clearAuth() {
    accessToken.value = ''
    refreshTokenValue.value = ''
    nickname.value = ''
    tenantId.value = ''
    userId.value = ''
    uni.removeStorageSync(ACCESS_TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
    setToken('')
  }

  /** WeChat login: wx.login -> backend -> save tokens */
  async function wxLogin(): Promise<boolean> {
    return new Promise((resolve) => {
      uni.login({
        provider: 'weixin',
        success: async (loginRes) => {
          try {
            const tokens = await apiLogin(loginRes.code)
            saveTokens(tokens.access_token, tokens.refresh_token)
            // Fetch user profile
            const profile = await getMe()
            nickname.value = profile.nickname
            tenantId.value = profile.tenant_id
            userId.value = profile.id
            resolve(true)
          } catch (e) {
            console.error('Login failed:', e)
            resolve(false)
          }
        },
        fail: (err) => {
          console.error('wx.login failed:', err)
          resolve(false)
        },
      })
    })
  }

  /** Try silent token refresh. Returns true if successful. */
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

  /** Check WeChat session validity; re-login if expired */
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

  /** Ensure user is authenticated: load tokens -> check session -> refresh if needed */
  async function ensureAuth(): Promise<boolean> {
    loadTokens()
    if (!accessToken.value) {
      return await wxLogin()
    }
    // Check WeChat session
    const sessionOk = await checkAndRelogin()
    if (!sessionOk) return false
    return true
  }

  return {
    accessToken, refreshTokenValue, nickname, tenantId, userId, isLoggedIn,
    loadTokens, saveTokens, clearAuth, wxLogin, tryRefreshToken,
    checkAndRelogin, ensureAuth,
  }
})

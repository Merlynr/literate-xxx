/**
 * HTTP request wrapper for XX甄选 BFF API.
 *
 * Uses uni.request for WeChat Mini Program compatibility.
 * Base URL configured per environment.
 * Includes 401 interceptor for silent token refresh.
 */

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown> | unknown
  header?: Record<string, string>
  _retry?: boolean  // internal flag to prevent infinite retry loop
}

interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

function normalizeResponse<T>(payload: unknown): ApiResponse<T> {
  if (
    payload &&
    typeof payload === 'object' &&
    'code' in (payload as Record<string, unknown>) &&
    'data' in (payload as Record<string, unknown>) &&
    'message' in (payload as Record<string, unknown>)
  ) {
    return payload as ApiResponse<T>
  }
  return {
    code: 0,
    data: payload as T,
    message: 'ok',
  }
}

// BFF base URL — update per environment
// WeChat Mini Program requires HTTPS in production; HTTP OK for dev
export const BASE_URL = 'http://8.141.7.56:8000/api/v1'

let authToken = ''
let refreshTokenValue = ''

export function setToken(token: string) {
  authToken = token
}

export function clearTokens() {
  authToken = ''
  refreshTokenValue = ''
}

export function setTokenPair(accessToken: string, refreshToken: string) {
  authToken = accessToken
  refreshTokenValue = refreshToken
}

export function getToken() {
  return authToken
}

async function tryRefreshAndRetry<T>(options: RequestOptions): Promise<ApiResponse<T>> {
  if (!refreshTokenValue) {
    uni.showToast({ title: '请重新登录', icon: 'none' })
    return Promise.reject(new Error('Token refresh failed'))
  }
  const refreshed = await new Promise<TokenResponse>((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}/auth/refresh`,
      method: 'POST',
      data: { refresh_token: refreshTokenValue },
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const payload = normalizeResponse<TokenResponse>(res.data)
          resolve(payload.data)
          return
        }
        reject(new Error('Token refresh failed'))
      },
      fail: reject,
    })
  })
  setTokenPair(refreshed.access_token, refreshed.refresh_token)
  uni.setStorageSync('xxzx_access_token', refreshed.access_token)
  uni.setStorageSync('xxzx_refresh_token', refreshed.refresh_token)
  return request<T>({ ...options, _retry: true })
}

export function request<T = unknown>(options: RequestOptions): Promise<ApiResponse<T>> {
  return new Promise((resolve, reject) => {
    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.header,
    }

    if (authToken) {
      header['Authorization'] = `Bearer ${authToken}`
    }

    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data as string | Record<string, unknown> | ArrayBuffer | undefined,
      header,
      success: async (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(normalizeResponse<T>(res.data))
        } else if (res.statusCode === 401 && !options._retry) {
          // Attempt silent refresh
          try {
            const result = await tryRefreshAndRetry<T>(options)
            resolve(result)
          } catch (e) {
            reject(e)
          }
        } else if (res.statusCode === 401) {
          uni.showToast({ title: '请重新登录', icon: 'none' })
          reject(new Error('Unauthorized'))
        } else {
          const errMsg = (res.data as { message?: string })?.message || '请求失败'
          uni.showToast({ title: errMsg, icon: 'none' })
          reject(new Error(errMsg))
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}

export default request

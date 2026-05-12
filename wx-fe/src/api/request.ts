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

// BFF base URL — update per environment
// WeChat Mini Program requires HTTPS in production; HTTP OK for dev
const BASE_URL = 'http://localhost:8000/api/v1'

let authToken = ''

export function setToken(token: string) {
  authToken = token
}

/** Lazy import to avoid circular dependency */
async function tryRefreshAndRetry<T>(options: RequestOptions): Promise<ApiResponse<T>> {
  // Dynamically import the store
  const { useUserStore } = await import('../stores/user')
  const userStore = useUserStore()
  const refreshed = await userStore.tryRefreshToken()
  if (refreshed) {
    // Retry original request with new token
    return request<T>({ ...options, _retry: true })
  }
  // Refresh failed — redirect to login
  uni.showToast({ title: '请重新登录', icon: 'none' })
  return Promise.reject(new Error('Token refresh failed'))
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
      data: options.data,
      header,
      success: async (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as ApiResponse<T>)
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

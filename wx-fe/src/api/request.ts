/**
 * HTTP request wrapper for XX甄选 BFF API.
 *
 * Uses uni.request for WeChat Mini Program compatibility.
 * Base URL configured per environment.
 */

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown> | unknown
  header?: Record<string, string>
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
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as ApiResponse<T>)
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
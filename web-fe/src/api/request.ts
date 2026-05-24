export const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const ACCESS_KEY = 'xxzx_access_token'
const REFRESH_KEY = 'xxzx_refresh_token'

export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: unknown
  headers?: Record<string, string>
  _retry?: boolean
}

export interface TokenPair {
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
    'data' in (payload as Record<string, unknown>)
  ) {
    return payload as ApiResponse<T>
  }
  return { code: 0, data: payload as T, message: 'ok' }
}

export function getAccessToken(): string {
  return localStorage.getItem(ACCESS_KEY) || ''
}

export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_KEY) || ''
}

export function setTokenPair(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

async function refreshTokens(): Promise<TokenPair> {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('请重新登录')
  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })
  if (!res.ok) throw new Error('登录已过期')
  const body = normalizeResponse<TokenPair>(await res.json())
  setTokenPair(body.data.access_token, body.data.refresh_token)
  return body.data
}

export async function request<T>(options: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${options.url}`, {
    method: options.method || 'GET',
    headers,
    body: options.data !== undefined ? JSON.stringify(options.data) : undefined,
  })

  if (res.status === 401 && !options._retry) {
    await refreshTokens()
    return request<T>({ ...options, _retry: true })
  }

  if (res.status === 204) return undefined as T

  const payload = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg =
      (payload as { detail?: string; message?: string }).detail ||
      (payload as { message?: string }).message ||
      `请求失败 (${res.status})`
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }

  return normalizeResponse<T>(payload).data
}

export async function uploadFileDirect(file: File): Promise<{
  key: string
  filename: string
  content_type: string
  size_bytes: number
}> {
  const form = new FormData()
  form.append('file', file)
  const token = getAccessToken()
  const res = await fetch(`${BASE_URL}/uploads/direct`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || '上传失败')
  }
  return res.json()
}

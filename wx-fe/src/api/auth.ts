import request from './request'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface DevLoginPayload {
  nickname?: string
  avatar_url?: string
}

export interface UserProfile {
  id: string
  openid: string
  nickname: string
  avatar_url: string
  tenant_id: string
  privacy_accepted_at?: string | null
}

/** WeChat login: send wx.login code to backend */
export function login(code: string): Promise<TokenResponse> {
  return request<TokenResponse>({
    url: '/auth/login',
    method: 'POST',
    data: { code },
  }).then(res => res.data)
}

/** Local development login fallback for H5 / non-WeChat environments */
export function devLogin(payload?: DevLoginPayload): Promise<TokenResponse> {
  return request<TokenResponse>({
    url: '/auth/dev-login',
    method: 'POST',
    data: payload || {},
  }).then(res => res.data)
}

/** Refresh tokens using a valid refresh_token */
export function refreshToken(refreshTokenValue: string): Promise<TokenResponse> {
  return request<TokenResponse>({
    url: '/auth/refresh',
    method: 'POST',
    data: { refresh_token: refreshTokenValue },
  }).then(res => res.data)
}

/** Get current user profile */
export function getMe(): Promise<UserProfile> {
  return request<UserProfile>({
    url: '/auth/me',
    method: 'GET',
  }).then(res => res.data)
}

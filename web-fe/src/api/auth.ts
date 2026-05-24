import { request, setTokenPair, type TokenPair } from './request'
import type { UserProfile } from '@/types'

export async function devLogin(nickname = 'Web 用户'): Promise<TokenPair> {
  const tokens = await request<TokenPair>({
    url: '/auth/dev-login',
    method: 'POST',
    data: { nickname, avatar_url: '' },
  })
  setTokenPair(tokens.access_token, tokens.refresh_token)
  return tokens
}

export function getMe() {
  return request<UserProfile>({ url: '/auth/me' })
}

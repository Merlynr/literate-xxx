import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref(false)
  const nickname = ref('')
  const tenantId = ref('')

  function setUser(data: { nickname: string; tenantId: string }) {
    isLoggedIn.value = true
    nickname.value = data.nickname
    tenantId.value = data.tenantId
  }

  function logout() {
    isLoggedIn.value = false
    nickname.value = ''
    tenantId.value = ''
  }

  return { isLoggedIn, nickname, tenantId, setUser, logout }
})

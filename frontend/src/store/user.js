import { defineStore } from 'pinia'
import { login, getInfo } from '@/api/system'
import router from '@/router'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    menus: []
  }),
  actions: {
    // 登录动作
    async login(loginForm) {
      try {
        const res = await login(loginForm)
        if (res.access_token) {
          this.token = res.access_token
          localStorage.setItem('token', res.access_token)
          return true
        }
        return false
      } catch (error) {
        console.error('Login failed:', error)
        return false
      }
    },
    // 获取用户信息及菜单
    async getUserInfo() {
      try {
        const res = await getInfo()
        if (res.code === 200) {
          this.userInfo = res.data.user
          this.menus = res.data.menus
          return res.data
        }
        return null
      } catch (error) {
        this.resetToken()
        return null
      }
    },
    // 退出登录
    logout() {
      this.resetToken()
      router.push('/login')
    },
    // 重置 Token 和用户信息
    resetToken() {
      this.token = ''
      this.userInfo = null
      this.menus = []
      localStorage.removeItem('token')
    }
  }
})

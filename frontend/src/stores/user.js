import { defineStore } from 'pinia'
import { authAPI } from '@/api'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    apiConfig: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    hasApiConfig: (state) => !!(state.apiConfig?.ocr_api_key_set && state.apiConfig?.translate_api_key_set)
  },

  actions: {
    // 登录
    async login(username, password) {
      try {
        const data = await authAPI.login({ username, password })
        this.token = data.access_token
        localStorage.setItem('token', data.access_token)
        await this.fetchUserInfo()
        ElMessage.success('登录成功')
        return true
      } catch (error) {
        return false
      }
    },

    // 注册
    async register(username, password) {
      try {
        await authAPI.register({ username, password })
        ElMessage.success('注册成功，请登录')
        return true
      } catch (error) {
        return false
      }
    },

    // 获取用户信息
    async fetchUserInfo() {
      try {
        this.userInfo = await authAPI.getCurrentUser()
      } catch (error) {
        console.error('Failed to fetch user info:', error)
      }
    },

    // 获取API配置
    async fetchApiConfig() {
      try {
        this.apiConfig = await authAPI.getApiConfig()
      } catch (error) {
        console.error('Failed to fetch API config:', error)
      }
    },

    // 保存API配置
    async saveApiConfig(config) {
      try {
        this.apiConfig = await authAPI.saveApiConfig(config)
        ElMessage.success('API配置保存成功')
        return true
      } catch (error) {
        return false
      }
    },

    // 登出
    logout() {
      this.token = ''
      this.userInfo = null
      this.apiConfig = null
      localStorage.removeItem('token')
      ElMessage.success('已退出登录')
    }
  }
})

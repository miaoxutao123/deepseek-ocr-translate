<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="header-left">
        <h2>OCR 翻译系统</h2>
      </div>
      <div class="header-right">
        <span class="username">{{ userStore.userInfo?.username }}</span>
        <el-button @click="handleLogout" text>退出登录</el-button>
      </div>
    </el-header>

    <el-container>
      <el-aside width="200px" class="sidebar">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/ocr">
            <el-icon><Document /></el-icon>
            <span>OCR识别</span>
          </el-menu-item>
          <el-menu-item index="/translate">
            <el-icon><ChatDotRound /></el-icon>
            <span>文档翻译</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
          </el-menu-item>
          <el-menu-item index="/corrections">
            <el-icon><Edit /></el-icon>
            <span>纠错管理</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>API配置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #409eff;
  color: white;
  padding: 0 20px;
  height: 60px;
}

.header-left h2 {
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  color: white;
}

.sidebar {
  background: #f5f7fa;
  padding: 10px 0;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}
</style>

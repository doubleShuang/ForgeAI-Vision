<template>
  <el-container style="height: 100vh; width: 100vw;">
    <!-- Sidebar -->
    <el-aside width="240px" style="display: flex; flex-direction: column; border-right: 1px solid var(--el-border-color-light); background-color: var(--el-bg-color); transition: background-color 0.3s; box-shadow: 2px 0 8px rgba(0,0,0,0.05);">
      <div style="display: flex; align-items: center; justify-content: center; height: 64px; font-weight: bold; font-size: 1.25rem; background-color: var(--el-bg-color-overlay); border-bottom: 1px solid var(--el-border-color-light); transition: background-color 0.3s;">
        <span style="background-clip: text; color: transparent; background-image: linear-gradient(to right, #3b82f6, #14b8a6);">
          ForgeAI Vision
        </span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="border-none flex-1 overflow-y-auto custom-scrollbar"
        style="border-right: none; background-color: transparent;"
      >
        <template v-for="menu in userStore.menus" :key="menu.id">
            <!-- 有子菜单的情况 -->
            <el-sub-menu v-if="menu.children && menu.children.length > 0" :index="menu.path || String(menu.id)">
                <template #title>
                    <el-icon v-if="menu.meta.icon"><component :is="menu.meta.icon" /></el-icon>
                    <span>{{ menu.name }}</span>
                </template>
                <el-menu-item v-for="child in menu.children" :key="child.id" :index="child.path">
                    <el-icon v-if="child.meta.icon"><component :is="child.meta.icon" /></el-icon>
                    <span>{{ child.name }}</span>
                </el-menu-item>
            </el-sub-menu>
            
            <!-- 无子菜单的情况 -->
            <el-menu-item v-else :index="menu.path">
                <el-icon v-if="menu.meta.icon"><component :is="menu.meta.icon" /></el-icon>
                <span>{{ menu.name }}</span>
            </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <!-- Main Container -->
    <el-container style="display: flex; flex-direction: column; background-color: var(--el-bg-color-page); transition: background-color 0.3s;">
      <!-- Header -->
      <el-header style="height: 64px; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background-color: var(--el-bg-color-overlay); border-bottom: 1px solid var(--el-border-color-light); backdrop-filter: blur(8px); z-index: 10;">
        <div style="font-size: 1.125rem; font-weight: 600; color: var(--el-text-color-primary);">
          {{ $route.meta.title || $route.name || '控制台' }}
        </div>
        <div style="display: flex; align-items: center; gap: 24px;">
          <el-switch
            v-model="isDark"
            inline-prompt
            :active-icon="Moon"
            :inactive-icon="Sunny"
            style="--el-switch-on-color: #4b5563; --el-switch-off-color: #fbbf24"
          />
          <el-dropdown trigger="click">
            <span class="flex items-center outline-none cursor-pointer">
              <el-avatar :size="36" class="bg-gradient-to-tr from-blue-500 to-teal-400 text-white font-bold select-none cursor-pointer hover:ring-2 ring-blue-400 transition-all">
                {{ userStore.userInfo?.nickname?.substring(0, 1) || 'U' }}
              </el-avatar>
              <span class="ml-2 text-sm font-medium hidden md:inline-block">{{ userStore.userInfo?.nickname }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main style="flex: 1; padding: 24px; overflow-y: auto; overflow-x: hidden; width: 100%; position: relative;">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { watch } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'

const isDark = useDark({
  initialValue: 'light'
})
const toggleDark = useToggle(isDark)
const userStore = useUserStore()

// 监听主题变化，打印日志辅助调试
watch(isDark, (val) => {
  console.log('主题已切换至:', val ? 'dark' : 'light')
})

const handleLogout = () => {
    ElMessageBox.confirm('确定退出系统吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        userStore.logout()
    })
}
</script>

<style scoped lang="less">
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.custom-scrollbar {
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #4b5563;
    border-radius: 4px;
    &:hover {
      background: #6b7280;
    }
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}
</style>

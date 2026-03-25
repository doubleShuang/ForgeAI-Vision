import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    // 配置路径别名，@ 指向 src 目录
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})

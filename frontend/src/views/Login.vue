<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="title">ForgeAI Vision</h1>
        <p class="subtitle">智能视觉模型开发与管理平台</p>
      </div>
      
      <el-form :model="loginForm" :rules="rules" ref="loginRef" label-width="0" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock" 
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <div class="login-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-link type="primary">忘记密码？</el-link>
        </div>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            class="login-button" 
            size="large"
            @click="handleLogin"
          >
            立即登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>演示账号: admin / admin123</p>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="bg-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loginRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginRef.value) return
  
  await loginRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const success = await userStore.login(loginForm)
      if (success) {
        ElMessage.success('登录成功')
        // 登录成功后会自动触发路由守卫去拉取用户信息和菜单
        router.push('/')
      } else {
        ElMessage.error('登录失败，请检查用户名或密码')
      }
      loading.value = false
    }
  })
}
</script>

<style scoped lang="less">
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #0f172a;
  overflow: hidden;
  position: relative;
  
  .login-box {
    width: 420px;
    padding: 40px;
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    z-index: 10;
    
    .login-header {
      text-align: center;
      margin-bottom: 40px;
      
      .title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 8px;
        background: linear-gradient(to right, #60a5fa, #2dd4bf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
      
      .subtitle {
        color: #94a3b8;
        font-size: 0.875rem;
      }
    }
    
    .login-options {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      
      :deep(.el-checkbox__label) {
        color: #94a3b8;
      }
    }
    
    .login-button {
      width: 100%;
      background: linear-gradient(to right, #3b82f6, #06b6d4);
      border: none;
      font-weight: 600;
      transition: all 0.3s;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
      }
    }
    
    .login-footer {
      margin-top: 32px;
      text-align: center;
      color: #64748b;
      font-size: 0.75rem;
    }
  }
}

// 装饰性的圆圈
.bg-decoration {
    position: absolute;
    width: 100%;
    height: 100%;
    
    .circle {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
    }
    
    .circle-1 {
        width: 400px;
        height: 400px;
        background: rgba(59, 130, 246, 0.15);
        top: -100px;
        left: -100px;
    }
    
    .circle-2 {
        width: 300px;
        height: 300px;
        background: rgba(20, 184, 166, 0.15);
        bottom: -50px;
        right: -50px;
    }
}

:deep(.el-input__wrapper) {
    background-color: rgba(15, 23, 42, 0.5);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
    
    &.is-focus {
        box-shadow: 0 0 0 1px #3b82f6 inset;
    }
}

:deep(.el-input__inner) {
    color: #f1f5f9;
    height: 48px;
    
    &::placeholder {
        color: #475569;
    }
}
</style>

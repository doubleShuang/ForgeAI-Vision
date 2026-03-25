import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from './store/user'

const Layout = () => import('@/layout/index.vue')

// 基础静态路由
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    name: 'Root',
    component: Layout,
    redirect: '/ModelList',
    children: [
        {
            path: 'projects/:id',
            name: 'ProjectDetail',
            component: () => import('@/views/ProjectDetail.vue'),
            meta: { title: '项目详情' }
        }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由白名单
const whiteList = ['/login']

// 动态导入视图组件的映射辅助函数
const modules = import.meta.glob('./views/**/*.vue')

function filterAsyncRoutes(menus) {
  const res = []
  menus.forEach(menu => {
    if (menu.component === 'Layout') {
        // 目录型仅递归处理子级
        if (menu.children && menu.children.length > 0) {
            res.push(...filterAsyncRoutes(menu.children))
        }
    } else {
        const componentPath = `./views/${menu.component}.vue`
        const component = modules[componentPath]
        
        if (component) {
            const route = {
                path: menu.path,
                name: menu.name || menu.id,
                // 将所有动态业务页面也挂载在 Root 下，渲染到 Layout 的 router-view
                component: component,
                meta: { 
                    title: menu.meta?.title || menu.name,
                    icon: menu.meta?.icon
                }
            }
            res.push(route)
        }
    }
  })
  return res
}

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const hasToken = userStore.token

  if (hasToken) {
    if (to.path === '/login') {
      next({ path: '/' })
    } else {
      const hasUserInfo = userStore.userInfo
      if (hasUserInfo) {
        next()
      } else {
        try {
          const data = await userStore.getUserInfo()
          if (data) {
              const accessRoutes = filterAsyncRoutes(data.menus)
              accessRoutes.forEach(route => {
                  // 将动态路由作为根路由 Root 的子路由添加
                  router.addRoute('Root', route)
              })
              
              // 添加一个 404 兜底，确保在此之后的任何不匹配都重回首页或登录
              router.addRoute({
                  path: '/:pathMatch(.*)*',
                  redirect: '/ModelList'
              })
              
              next({ ...to, replace: true })
          } else {
              next(`/login?redirect=${to.path}`)
          }
        } catch (error) {
          userStore.resetToken()
          next(`/login?redirect=${to.path}`)
        }
      }
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
    }
  }
})

export default router

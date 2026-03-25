# ForgeAI-Vision Frontend

本项目是 ForgeAI-Vision 视觉识别平台的前端部分，基于 **Vue 3 + Vite + Element Plus** 构建，提供一套适配全终端的科技风界面，包含：在线标注、实时推理展示、模型训练可视化及完整的后台管理。

## 技术栈
- **核心框架**: Vue 3 (Composition API)
- **工程化**: Vite
- **UI 组件库**: Element Plus
- **样式**: Tailwind CSS, Less
- **状态管理**: Pinia
- **路由**: Vue Router (支持动态鉴权路由)
- **工具库**: @vueuse/core, Axios, Video.js

## 核心特性
- **动态权限路由**: 登录后根据角色动态注入路由，支持菜单、页面的精细化权限隔离。
- **浅色/深色模式**: 基于 VueUse 实现的全局主题无缝切换。
- **可视化标注**: 纯 Canvas 实现的 YOLO 格式在线标注工具。
- **数据解构响应**: 统一 Axios 拦截器处理 Token 注入与响应自动解构。

## 目录结构
```
frontend/
├── src/
│   ├── api/        # 统一接口管理 (system.js, index.js)
│   ├── layout/     # 全局布局 (Sidebar, Navbar, Main)
│   ├── store/      # Pinia 状态 (user.js)
│   ├── utils/      # 工具类 (request.js 拦截器)
│   ├── views/      # 业务页面 (系统管理、模型、识别、训练、标注)
│   ├── App.vue     # 入口组件
│   └── router.js   # 路由守护与守卫逻辑
└── tailwind.config.js # Tailwind 配置
```

## 运行与开发

### 1. 安装依赖
```bash
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```
启动后可访问：`http://localhost:5173`

### 3. 环境配置
默认 API 基础路径配置在 `src/utils/request.js` 中，开发环境指向 `http://localhost:8000/api/v1`。

## 开发建议
- **新增页面**: 请在 `src/views/` 下创建对应模块文件夹，并在数据库 `sys_menu` 表中配置相应的 `component` 路径。
- **API 调用**: 请在 `src/api/` 中统一导出请求方法，并在组件中按需 import。
- **主题适配**: 尽量使用 Tailwind CSS 的 `dark:` 前缀处理深色模式下的样式差异。

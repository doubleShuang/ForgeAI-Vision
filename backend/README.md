# ForgeAI-Vision Backend

本项目是 ForgeAI-Vision 视觉识别平台的后端核心，基于 **FastAPI** 和 **YOLOv8** 构建，提供模型管理、异步训练监控、实时推理识别及完整的企业级权限管理 (RBAC) 支撑。

## 技术栈
- **Web 框架**: FastAPI (Python 3.8+)
- **深度学习**: Ultralytics YOLOv8
- **ORM / 数据库**: SQLAlchemy / SQLite (支持切换 MySQL)
- **安全 / 鉴权**: 基于 PyJWT 的令牌机制，Bcrypt 密码哈希
- **文件处理**: Multipart Upload, OpenCV, Pillow

## 核心目录
```
backend/
├── app/
│   ├── api/            # 接口定义 (v1 路由)
│   │   └── endpoints/  # 子模块接口 (auth, system, models, projects, training)
│   ├── core/           # 核心配置 (security, config)
│   ├── db/             # 数据库连接与模型定义 (SysUser, SysRole, SysMenu, InferenceRecord)
│   ├── models/         # 数据库 ORM 模型
│   ├── services/       # 业务服务层 (推理引擎, 训练调度, 项目管理)
│   └── main.py         # 应用入口
├── uploads/            # 推理图片/视频临时存储
└── workspaces/         # 标注工程与数据集存储
```

## 运行与开发

### 1. 安装依赖
建议在 Python 虚拟环境中运行：
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
uvicorn app.main:app --reload --port 8000
```
启动后可访问 Swagger 文档：`http://localhost:8000/docs`

### 3. 主要功能节点
- **鉴权中心**: `/api/v1/auth` (登录、用户信息、权限菜单获取)
- **系统设置**: `/api/v1/system` (用户/角色/菜单/日志管理)
- **视觉业务**: `/api/v1/models`, `/api/v1/projects`, `/api/v1/training`, `/api/v1/history`

## 开发者提示
- **权限校验**: 核心业务接口均集成了 `Depends(get_current_user)` 以确保身份安全。
- **自动审计**: 所有涉及系统管理的 `POST` 操作均会自动记录审计日志。
- **路径适配**: 本地存储自动兼容 Windows/Linux 路径。

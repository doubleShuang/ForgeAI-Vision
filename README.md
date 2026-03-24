# ForgeAI-Vision
这是一个轻量化、快速上手的通用目标检测平台，实现标注、训练、推理的一站式服务，兼顾本地与边缘侧部署的视觉解决方案。项目基于 **YOLOv8** + **FastAPI** + **Vue3** 的全栈智能识别平台，支持模型管理、在线标注、模型训练和多媒体识别。
<img width="1435" height="651" alt="image" src="https://github.com/user-attachments/assets/1a44cd7e-9b7f-4ca2-b704-f948e0d7251e" />

## 功能特性

- **模型库管理**: 查看、导入、管理 YOLOv8 模型。
- **在线标注**: 基于 Canvas 的标注工具，支持导出 COCO 格式。
- **在线训练**: 配置训练参数 (Epochs, Batch Size) 并启动训练任务。
- **媒体识别**: 支持图片上传识别和视频流处理。
- **工程化架构**: 前后端分离，支持 MySQL/MinIO/Redis (生产环境) 和 SQLite/本地存储 (演示环境)。

## 快速开始 (演示模式)

无需安装 MySQL/MinIO，直接运行即可体验：

1. **环境准备**:
   - Python 3.8+
   - Node.js 16+

2. **一键启动**:
   双击运行 `run.bat` 脚本。
   
   或者手动运行：
   ```bash
   # 启动后端 (http://localhost:8000)
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload

   # 启动前端 (http://localhost:5173)
   cd frontend
   npm install
   npm run dev
   ```

## 生产环境部署 (Docker)

如果需要完整的生产环境 (MySQL, MinIO, Redis):

1. 确保安装 Docker Desktop。
2. 运行:
   ```bash
   docker-compose up --build -d
   ```

## 目录结构

```
YOLOv8/
├── backend/             # Python FastAPI 后端
│   ├── app/
│   │   ├── api/         # 接口定义
│   │   ├── core/        # 配置与核心逻辑
│   │   ├── db/          # 数据库模型
│   │   ├── services/    # 业务逻辑 (推理, 训练, 存储)
│   │   └── main.py      # 入口文件
│   └── requirements.txt
├── frontend/            # Vue3 + Element Plus 前端
│   ├── src/
│   │   ├── views/       # 页面 (模型, 标注, 训练, 识别)
│   │   └── api/         # Axios 封装
├── docker-compose.yml   # 容器编排
└── run.bat              # Windows 一键启动脚本
```

## 技术栈

- **前端**: Vue 3, Vite, Element Plus, Video.js
- **后端**: FastAPI, SQLAlchemy, Celery (模拟), Ultralytics YOLOv8
- **基础设施**: MySQL, Redis, MinIO (可选)

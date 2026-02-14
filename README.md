## Quick start

### 开发环境

#### 前端启动

Run `npm i` to install the dependencies.

Run `npm run dev` to start the development server.

#### 后端启动

```shell
cd backend

# 首次运行：配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少配置一个AI模型的API Key：
# - GEMINI_API_KEY (Google Gemini)
# - QWEN_API_KEY (阿里云通义千问)

# 启动服务
python main.py
```

### AI模型配置 (新增功能 ✨)

系统现已支持多个AI模型后端，用于PDF试卷识别：

1. **Google Gemini 2.0 Flash** - 快速、适合清晰PDF
2. **Qwen VL Max** - 对中文识别效果好，适合复杂版面

**快速配置：**
```bash
# 在 backend/.env 中配置（至少一个）
GEMINI_API_KEY=your_key_here
QWEN_API_KEY=your_key_here  # 已提供
DEFAULT_AI_MODEL=qwen-vl
```

**测试配置：**
```bash
cd backend
python test_ai_models.py
```

**详细文档：**
- 📖 [AI模型配置指南](docs/AI_MODELS.md)
- 🚀 [快速开始](docs/QUICKSTART_AI_MODELS.md)
- 📝 [更新说明](docs/MULTI_MODEL_UPDATE.md)

## 生产部署 🚀

### 静态托管 + Cloud Run 部署

本项目已配置为单容器部署方案，无需 `npm i`，适合生产环境：

**快速部署到 Google Cloud Run：**
```bash
# 1. 构建静态文件（已集成在Docker中）
npm run build  # 可选，Docker会自动构建

# 2. 部署到 Cloud Run
gcloud builds submit --config cloudbuild.yaml .
```

**本地测试 Docker：**
```bash
# 构建镜像
docker build -t exampapersys:local .

# 运行容器
docker run -p 8080:8080 exampapersys:local

# 访问 http://localhost:8080
```

**详细部署文档：**
- 📖 [完整部署指南](DEPLOYMENT.md) - Google Cloud Run 部署步骤
- 🐳 [Dockerfile](Dockerfile) - 多阶段构建配置
- ☁️ [cloudbuild.yaml](cloudbuild.yaml) - CI/CD 配置

### 部署架构

```
┌─────────────────────────────────────────┐
│         Google Cloud Run                │
│  ┌─────────────────────────────────┐   │
│  │   单容器 (exampapersys)         │   │
│  │                                 │   │
│  │  ┌──────────────────────────┐  │   │
│  │  │  静态文件 (/app/static)  │  │   │
│  │  │  - index.html            │  │   │
│  │  │  - assets/*.js           │  │   │
│  │  │  - assets/*.css          │  │   │
│  │  └──────────────────────────┘  │   │
│  │              ↓                  │   │
│  │  ┌──────────────────────────┐  │   │
│  │  │  Python 后端 (aiohttp)   │  │   │
│  │  │  - API 服务 (/api/*)     │  │   │
│  │  │  - 静态文件托管 (/*)     │  │   │
│  │  └──────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## TODO

还需要完善的地方：

导入导出：

1. 导出

    1) 题目编号目前还是沿用原来的，需要修改

    2) 导出目前直接下载latex格式的文档，后续可以提供在线预览编辑调格式比较好。需要网页端支持latex引擎

2. 导入

    1) 数据还是不是格式良好的，可能有缺损或者串行。导入后试卷数据如何结构化存储校验？

    2) ✅ AI后端迁移：**已完成**

        1) ✅ 已支持多AI后端（Gemini、Qwen VL等）

        2) ✅ 用户可在导入时选择模型

        3) 后续：对齐效果，回归数据测试

    3) 标签：目前是AI随意生成的标签，后续如果有标签集合可以更新在prompt中，让AI reference to 已有语义标签

如果要汇报需要一定的可用性，目前除了搜索还行还完全不可直接用...！

## 部署指南

### 部署到 Google Cloud Run

#### 快速部署

使用自动化脚本部署最新代码（推荐）：

```bash
# 确保已安装 gcloud CLI 并完成认证
./deploy.sh
```

部署脚本会自动：
- 清理 Python 缓存文件
- 检查代码状态
- 强制无缓存构建（避免旧代码问题）
- 使用时间戳标签
- 验证部署状态

#### 验证部署

检查线上版本：

```bash
./check-deployment.sh
```

#### 手动部署

```bash
# 清理缓存
find . -type d -name "__pycache__" -exec rm -rf {} +

# 提交构建
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_TAG="v-$(date +%Y%m%d-%H%M%S)" \
    --no-source-cache
```

#### 常见问题

**问题：本地和线上代码不一致**

原因：Docker 构建缓存或 Python 字节码缓存

解决：
1. 使用 `./deploy.sh` 脚本（自动清理缓存）
2. 查看详细排查指南：[DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md)

**问题：部署成功但功能未更新**

```bash
# 强制使用新镜像
gcloud run services update exampapersys \
    --region=us-central1 \
    --image=IMAGE_URL
```

### 一些想法
1. 为了提高导入导出质量，重新做SFT对齐是否有助于提高OCR效果？
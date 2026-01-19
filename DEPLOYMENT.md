# Google Cloud Run 部署指南

本文档说明如何将 Exam Paper System 部署到 Google Cloud Run。

## 架构说明

本项目使用**单容器部署**方案：
- **前端**：React + Vite，构建成静态文件
- **后端**：Python + aiohttp，同时托管静态文件和提供API服务
- **容器化**：使用多阶段 Docker 构建，第一阶段构建前端，第二阶段整合后端

## 前置准备

### 1. 安装 Google Cloud SDK

```bash
# macOS (使用 Homebrew)
brew install --cask google-cloud-sdk

# 或者使用官方安装脚本
curl https://sdk.cloud.google.com | bash

# 初始化
gcloud init
```

### 2. 创建 GCP 项目

```bash
# 创建新项目
gcloud projects create exampapersys --name="Exam Paper System"

# 设置为当前项目
gcloud config set project exampapersys

# 查看当前项目
gcloud config get-value project
```

### 3. 启用必要的 API

```bash
# 启用 Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# 启用 Cloud Run API
gcloud services enable run.googleapis.com

# 启用 Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# 启用 Container Registry API (如果需要)
gcloud services enable containerregistry.googleapis.com
```

### 4. 创建 Artifact Registry 仓库

```bash
# 创建 Docker 仓库
gcloud artifacts repositories create exampapersys \
    --repository-format=docker \
    --location=us-central1 \
    --description="Exam Paper System Docker images"

# 验证仓库创建成功
gcloud artifacts repositories list
```

### 5. 配置 IAM 权限

Cloud Build 需要权限来部署到 Cloud Run：

```bash
# 获取项目编号
PROJECT_NUMBER=$(gcloud projects describe exampapersys --format='value(projectNumber)')

# 授予 Cloud Build 服务账号必要的权限
gcloud projects add-iam-policy-binding exampapersys \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding exampapersys \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

或者通过 Console 手动设置：
1. 访问 [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. 找到 `[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com`
3. 编辑权限，添加角色：
   - **Cloud Run Admin**
   - **Service Account User**

## 部署步骤

### 方式一：命令行手动部署

```bash
# 进入项目根目录
cd /Users/test/Downloads/feng_games/exampapersys

# 提交构建和部署任务
gcloud builds submit --config cloudbuild.yaml .
```

构建过程大约需要 5-10 分钟，包括：
1. 构建前端 (npm install + build)
2. 构建后端 Docker 镜像
3. 推送镜像到 Artifact Registry
4. 部署到 Cloud Run

### 方式二：连接 GitHub 实现 CI/CD

#### 步骤 1：连接仓库

1. 访问 [Cloud Build > Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. 点击 **"连接代码库"** 或 **"CREATE TRIGGER"**
3. 选择源代码提供商：**GitHub**
4. 授权 Google Cloud 访问你的 GitHub
5. 选择你的仓库 `feng_games/exampapersys`

#### 步骤 2：创建触发器

在触发器配置页面：

- **名称**：`deploy-on-push-main`
- **描述**：`Deploy to Cloud Run when pushing to main`
- **事件**：Push to a branch
- **源**：
  - 仓库：`feng_games/exampapersys`
  - 分支：`^main$`（正则匹配 main 分支）
- **配置**：
  - 类型：Cloud Build configuration file (yaml or json)
  - 位置：`/cloudbuild.yaml`
- **高级**（可选）：
  - 超时：1200s (20分钟)

点击 **创建** 后，每次推送到 `main` 分支时将自动触发构建和部署。

#### 步骤 3：测试自动部署

```bash
# 修改代码后提交
git add .
git commit -m "Test Cloud Build deployment"
git push origin main

# 查看构建状态
gcloud builds list --limit=5
```

## 配置环境变量

部署后需要更新环境变量，特别是 `FRONTEND_URL` 和 `CORS_ORIGINS`。

### 获取 Cloud Run 服务 URL

```bash
# 部署后获取服务 URL
gcloud run services describe exampapersys \
    --region=us-central1 \
    --format='value(status.url)'
```

输出示例：`https://exampapersys-abc123-uc.a.run.app`

### 更新环境变量

方法一：通过命令行更新

```bash
# 替换为你的实际 URL
SERVICE_URL="https://exampapersys-abc123-uc.a.run.app"

gcloud run services update exampapersys \
    --region=us-central1 \
    --set-env-vars="FRONTEND_URL=${SERVICE_URL},CORS_ORIGINS=${SERVICE_URL}"
```

方法二：修改 `cloudbuild.yaml`

编辑 [cloudbuild.yaml](cloudbuild.yaml#L35)，将 `XXXXX` 替换为实际的服务 ID：

```yaml
--set-env-vars=FRONTEND_URL=https://exampapersys-abc123-uc.a.run.app,CORS_ORIGINS=https://exampapersys-abc123-uc.a.run.app
```

### 其他环境变量（可选）

```bash
gcloud run services update exampapersys \
    --region=us-central1 \
    --set-env-vars="JWT_SECRET=your-secret-key-here" \
    --set-env-vars="GEMINI_API_KEY=your-gemini-key" \
    --set-env-vars="QWEN_API_KEY=your-qwen-key"
```

## 数据持久化

⚠️ **重要**：Cloud Run 的文件系统是临时的，容器重启后数据会丢失。

### 选项一：使用 Cloud Storage（推荐）

修改后端代码，将 `questions.json` 等文件存储到 Cloud Storage。

### 选项二：使用 Cloud SQL 或 Firestore

将数据从 JSON 文件迁移到数据库。

### 选项三：使用卷挂载（NFS）

Cloud Run 支持 GCS Fuse 挂载 Cloud Storage 为文件系统。

## 查看日志和监控

### 查看构建日志

```bash
# 查看最近的构建
gcloud builds list --limit=5

# 查看特定构建的日志
gcloud builds log BUILD_ID
```

### 查看 Cloud Run 日志

```bash
# 实时查看日志
gcloud run services logs read exampapersys \
    --region=us-central1 \
    --limit=50 \
    --format="table(timestamp,textPayload)"

# 或访问 Console
# https://console.cloud.google.com/run/detail/us-central1/exampapersys/logs
```

### 监控指标

访问 [Cloud Run > Services > exampapersys > Metrics](https://console.cloud.google.com/run)

可以查看：
- 请求计数
- 请求延迟
- 容器实例数量
- CPU/内存使用率
- 错误率

## 本地测试 Docker 镜像

在部署前，可以在本地测试 Docker 镜像：

```bash
# 构建镜像
docker build -t exampapersys:local .

# 运行容器
docker run -p 8080:8080 \
    -e FRONTEND_URL=http://localhost:8080 \
    -e CORS_ORIGINS=http://localhost:8080 \
    exampapersys:local

# 访问
open http://localhost:8080
```

## 成本估算

Cloud Run 按使用量计费：

- **免费额度**（每月）：
  - 2,000,000 次请求
  - 360,000 GB-秒
  - 180,000 vCPU-秒
  
- **超出免费额度后**：
  - 请求：$0.40 / 百万次
  - 内存：$0.0000025 / GB-秒
  - CPU：$0.00002400 / vCPU-秒

对于低流量应用，通常可以**完全免费运行**。

## 故障排查

### 构建失败

```bash
# 查看详细的构建日志
gcloud builds log BUILD_ID

# 常见问题：
# 1. 权限不足 → 检查 IAM 设置
# 2. 超时 → 增加 cloudbuild.yaml 中的 timeout
# 3. 依赖安装失败 → 检查 requirements.txt 和 package.json
```

### 服务无法启动

```bash
# 查看服务详情
gcloud run services describe exampapersys --region=us-central1

# 检查日志
gcloud run services logs read exampapersys --region=us-central1 --limit=100

# 常见问题：
# 1. 端口不匹配 → 确保监听 $PORT (8080)
# 2. 健康检查失败 → 检查 /health 端点
# 3. 环境变量缺失 → 检查 CORS_ORIGINS 等配置
```

### CORS 错误

前端无法访问 API，浏览器显示 CORS 错误：

```bash
# 更新 CORS_ORIGINS 环境变量
SERVICE_URL=$(gcloud run services describe exampapersys --region=us-central1 --format='value(status.url)')
gcloud run services update exampapersys \
    --region=us-central1 \
    --set-env-vars="CORS_ORIGINS=${SERVICE_URL}"
```

## 更新和回滚

### 更新服务

```bash
# 通过 Cloud Build 自动部署
git push origin main

# 或手动触发
gcloud builds submit --config cloudbuild.yaml .
```

### 回滚到之前的版本

```bash
# 查看所有版本
gcloud run revisions list --service=exampapersys --region=us-central1

# 回滚到指定版本
gcloud run services update-traffic exampapersys \
    --region=us-central1 \
    --to-revisions=exampapersys-00002-abc=100
```

## 清理资源

如果不再需要，可以删除所有资源：

```bash
# 删除 Cloud Run 服务
gcloud run services delete exampapersys --region=us-central1

# 删除 Artifact Registry 仓库
gcloud artifacts repositories delete exampapersys --location=us-central1

# 删除项目（慎重！）
gcloud projects delete exampapersys
```

## 附录：cloudbuild.yaml 详解

```yaml
steps:
  # Step 1: 构建 Docker 镜像
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'IMAGE_URL', '.']
    
  # Step 2: 推送镜像
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'IMAGE_URL']
    
  # Step 3: 部署到 Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'SERVICE_NAME'
      - '--image=IMAGE_URL'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'  # 允许公开访问
      - '--memory=1Gi'              # 内存限制
      - '--cpu=1'                   # CPU 数量
      - '--timeout=300'             # 超时时间（秒）
```

## 参考文档

- [Cloud Run 官方文档](https://cloud.google.com/run/docs)
- [Cloud Build 文档](https://cloud.google.com/build/docs)
- [Artifact Registry 文档](https://cloud.google.com/artifact-registry/docs)

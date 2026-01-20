# Cloud 部署改造总结

## 改造内容

已完成从"npm i 本地开发模式"到"单容器静态托管"的改造，可部署到 Google Cloud Run。

## 新增文件

1. **`Dockerfile`** - 多阶段构建配置
   - Stage 1: 使用 Node.js 构建前端静态文件 (dist/)
   - Stage 2: 使用 Python 运行后端，并托管前端静态文件

2. **`cloudbuild.yaml`** - Google Cloud Build 配置
   - 自动构建 Docker 镜像
   - 推送到 Artifact Registry
   - 部署到 Cloud Run

3. **`.dockerignore`** - Docker 构建优化
   - 排除不必要的文件，减小镜像体积
   - 加快构建速度

4. **`DEPLOYMENT.md`** - 完整部署指南
   - GCP 环境准备
   - 部署步骤详解
   - 故障排查指南
   - 数据持久化方案

## 修改文件

### `backend/server.py`

添加了静态文件托管功能：

```python
def setup_static_files(app: web.Application):
    """Setup static file serving for production (SPA support)."""
    static_dir = Path(__file__).parent / 'static'
    
    if static_dir.exists() and static_dir.is_dir():
        # 托管静态资源 (JS, CSS, etc.)
        app.router.add_static('/assets', static_dir / 'assets', name='assets')
        
        # SPA fallback: 所有非API路由返回 index.html
        async def serve_spa(request):
            index_file = static_dir / 'index.html'
            if index_file.exists():
                return web.FileResponse(index_file)
            return web.Response(text='Frontend not built', status=404)
        
        app.router.add_get('/{path:.*}', serve_spa)
```

**关键特性：**
- ✅ 托管前端静态文件 (`/app/static/`)
- ✅ 支持 SPA 路由 (所有路由返回 index.html)
- ✅ 开发环境兼容 (static目录不存在时跳过)

### `README.md`

添加了生产部署章节，包括：
- 部署命令
- 架构图
- 文档链接

## 部署流程

### 本地测试

```bash
# 1. 构建 Docker 镜像
docker build -t exampapersys:test .

# 2. 运行容器
docker run -p 8080:8080 \
  -e FRONTEND_URL=http://localhost:8080 \
  -e CORS_ORIGINS=http://localhost:8080 \
  exampapersys:test

# 3. 访问
open http://localhost:8080
```

### 部署到 Cloud Run

```bash
# 方式一：手动部署
gcloud builds submit --config cloudbuild.yaml .

# 方式二：连接 GitHub 自动部署
# 1. 访问 Cloud Build > Triggers
# 2. 连接 GitHub 仓库
# 3. 创建触发器（push to main → deploy）
```

## 技术栈

### 构建阶段
- **Node.js 18-alpine** - 构建前端
- **Vite** - 前端构建工具
- **npm** - 包管理

### 运行阶段
- **Python 3.11-slim** - 后端运行环境
- **aiohttp** - 异步 Web 框架
- **静态文件托管** - 无需 Nginx/Apache

## 优势

✅ **简化部署** - 单个容器，无需分别部署前后端  
✅ **零配置** - 前端自动托管，无需配置 Nginx  
✅ **自动扩展** - Cloud Run 按需扩缩容  
✅ **成本优化** - 低流量几乎免费（Cloud Run 免费额度）  
✅ **CI/CD 就绪** - GitHub 集成，自动部署  
✅ **开发兼容** - 开发环境仍可用 `npm run dev`

## 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `PORT` | 服务端口 | `8080` |
| `FRONTEND_URL` | 前端 URL (用于邮件链接) | `https://your-app.run.app` |
| `CORS_ORIGINS` | CORS 允许的源 | `https://your-app.run.app` |
| `GEMINI_API_KEY` | Gemini AI Key | `AIza...` |
| `QWEN_API_KEY` | 通义千问 Key | `sk-...` |
| `JWT_SECRET` | JWT 密钥 | `random-secret` |

## 注意事项

⚠️ **数据持久化**  
Cloud Run 的文件系统是临时的，需要使用：
- Cloud Storage (推荐)
- Cloud SQL
- Firestore

⚠️ **首次部署后**  
需要更新 `cloudbuild.yaml` 中的 URL：
```yaml
--set-env-vars=FRONTEND_URL=https://your-actual-url.run.app
```

⚠️ **健康检查**  
确保 `/health` 端点正常工作：
```bash
curl https://your-app.run.app/health
```

## 下一步

1. **配置 IAM 权限** - 见 [DEPLOYMENT.md](DEPLOYMENT.md#5-配置-iam-权限)
2. **创建 Artifact Registry** - 存储 Docker 镜像
3. **首次部署** - `gcloud builds submit`
4. **配置环境变量** - 更新 FRONTEND_URL 和 CORS_ORIGINS
5. **数据持久化** - 迁移到 Cloud Storage 或数据库

## 故障排查

详见 [DEPLOYMENT.md](DEPLOYMENT.md#故障排查)

常见问题：
- CORS 错误 → 检查 `CORS_ORIGINS` 环境变量
- 服务无法启动 → 查看日志 `gcloud run services logs read`
- 静态文件 404 → 确认 `dist/` 目录已复制到容器

## 参考资料

- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署指南
- [Dockerfile](Dockerfile) - 容器构建配置
- [cloudbuild.yaml](cloudbuild.yaml) - CI/CD 配置
- [Cloud Run 文档](https://cloud.google.com/run/docs)

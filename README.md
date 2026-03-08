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

### 模型配置 

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

## gcloud部署

配置secrets
```shell
# 查看现有的 secrets
gcloud secrets list

# 如果 gemini-api-key 不存在，创建它
echo -n "your-actual-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# 同样创建其他 secrets
echo -n "your-qwen-api-key" | gcloud secrets create qwen-api-key --data-file=-
echo -n "your-random-jwt-secret" | gcloud secrets create jwt-secret --data-file=-
echo -n "your-gmail-app-password" | gcloud secrets create smtp-password --data-file=-

# 授予 Cloud Run 访问 secrets 的权限
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 对其他 secrets 重复授权
gcloud secrets add-iam-policy-binding qwen-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding jwt-secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding smtp-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

提交构建docker镜像
```shell
gcloud builds submit --config cloudbuild.yaml
```


运行构建好的docker镜像
```shell
gcloud run deploy exam-paper \
  --image us-central1-docker.pkg.dev/gen-lang-client-0254991670/exampapersys/app:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --execution-environment gen2 \
 --add-volume=name=data-vol,type=cloud-storage,bucket=exampapersys-data \
  --add-volume-mount=volume=data-vol,mount-path=/app/data \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="QWEN_API_KEY=qwen-api-key:latest" \
  --set-secrets="JWT_SECRET=jwt-secret:latest" \
  --set-secrets="SMTP_PASSWORD=smtp-password:latest" \
  --set-env-vars="DEFAULT_AI_MODEL=gemini" \
  --set-env-vars="DEV_MODE=false" \
  --set-env-vars="SMTP_HOST=smtp.gmail.com" \
  --set-env-vars="SMTP_PORT=587" \
  --set-env-vars="SMTP_USER=michu1415926535@gmail.com" \
  --set-env-vars="SMTP_FROM=michu1415926535@gmail.com" \
  --set-env-vars="FRONTEND_URL=https://exam-paper-893028988766.us-central1.run.app"

```
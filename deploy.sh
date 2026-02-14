#!/bin/bash

# 部署脚本 - 确保部署最新代码到 Google Cloud Run
# 使用方法: ./deploy.sh

set -e  # 遇到错误立即退出

echo "========================================="
echo "开始部署到 Google Cloud Run"
echo "========================================="

# 1. 清理本地 Python 字节码缓存
echo ""
echo "步骤 1/5: 清理本地 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✓ 缓存清理完成"

# 2. 检查 git 状态
echo ""
echo "步骤 2/5: 检查代码状态..."
if [[ -n $(git status -s) ]]; then
    echo "警告: 有未提交的更改，建议先提交:"
    git status -s
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 1
    fi
else
    echo "✓ 工作区干净，没有未提交的更改"
fi

# 3. 使用唯一标签构建（避免缓存）
echo ""
echo "步骤 3/5: 构建 Docker 镜像（强制无缓存）..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TAG="v-${TIMESTAMP}"
echo "使用标签: ${TAG}"

# 4. 触发 Cloud Build（使用 --no-cache 参数）
echo ""
echo "步骤 4/5: 提交到 Cloud Build..."
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_TAG="${TAG}" \
    --no-source-cache

echo "✓ 构建完成"

# 5. 验证部署
echo ""
echo "步骤 5/5: 验证部署..."
echo "等待服务启动（30秒）..."
sleep 30

SERVICE_URL=$(gcloud run services describe exampapersys \
    --region=us-central1 \
    --format='value(status.url)')

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo "服务地址: ${SERVICE_URL}"
echo "部署标签: ${TAG}"
echo ""
echo "⚠️  重要提示：浏览器缓存问题"
echo "如果前端界面没有更新，请清理浏览器缓存："
echo ""
echo "Chrome/Edge:"
echo "  - macOS: Cmd+Shift+R (硬刷新)"
echo "  - Windows: Ctrl+Shift+R"
echo "  - 或：Cmd/Ctrl+Shift+Delete -> 清除缓存和Cookie"
echo ""
echo "Safari:"
echo "  - Cmd+Option+E (清空缓存)"
echo "  - 然后 Cmd+R (刷新)"
echo ""
echo "Firefox:"
echo "  - Cmd/Ctrl+Shift+R (硬刷新)"
echo ""
echo "建议的验证步骤："
echo "1. 访问 ${SERVICE_URL}/health 检查健康状态"
echo "2. 清理浏览器缓存（见上方提示）"
echo "3. 测试上传 PDF 功能，检查答案编辑面板是否更新"
echo ""

# 可选：打开浏览器
read -p "是否在浏览器中打开服务? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "${SERVICE_URL}"
    echo ""
    echo "⚠️  请记得在浏览器中按 Cmd+Shift+R (macOS) 或 Ctrl+Shift+R (Windows) 硬刷新！"
fi

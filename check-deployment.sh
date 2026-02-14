#!/bin/bash

# 验证线上代码版本脚本
# 使用方法: ./check-deployment.sh

set -e

echo "========================================="
echo "检查线上部署版本"
echo "========================================="

SERVICE_URL="https://exam-paper-893028988766.us-central1.run.app"

echo ""
echo "1. 检查健康状态..."
curl -s "${SERVICE_URL}/health" | python3 -m json.tool || echo "健康检查失败"

echo ""
echo ""
echo "2. 获取线上服务信息..."
gcloud run services describe exampapersys \
    --region=us-central1 \
    --format="table(
        metadata.name,
        status.url,
        status.latestReadyRevisionName,
        spec.template.spec.containers[0].image
    )"

echo ""
echo "3. 检查最近的部署历史..."
gcloud run revisions list \
    --service=exampapersys \
    --region=us-central1 \
    --limit=5 \
    --format="table(
        metadata.name,
        status.conditions[0].lastTransitionTime.date('%Y-%m-%d %H:%M:%S'),
        spec.containers[0].image
    )"

echo ""
echo "4. 获取当前运行的镜像标签..."
CURRENT_IMAGE=$(gcloud run services describe exampapersys \
    --region=us-central1 \
    --format='value(spec.template.spec.containers[0].image)')

echo "当前镜像: ${CURRENT_IMAGE}"

echo ""
echo "5. 本地代码最后修改时间..."
echo "pdf_import_service.py: $(ls -l backend/services/pdf_import_service.py | awk '{print $6, $7, $8}')"

echo ""
echo "========================================="
echo "建议操作："
echo "========================================="
echo "如果线上代码版本较旧，请运行:"
echo "  ./deploy.sh"
echo ""
echo "如果需要查看 prompt 内容，可以:"
echo "  grep -A 5 '_get_extraction_prompt' backend/services/pdf_import_service.py"
echo ""

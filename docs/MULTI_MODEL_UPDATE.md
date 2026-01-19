# 多AI模型后端支持 - 更新说明

## 更新日期
2026年1月15日

## 功能概述

系统现已支持多个AI模型后端，用户可以在导入试卷时选择不同的AI模型进行识别和提取。

## 新增功能

### 1. 多模型支持架构
- 创建了统一的 AI 模型抽象层 (`AIModel` 基类)
- 支持灵活扩展新的 AI 模型
- 模型实例化与配置管理分离

### 2. 支持的 AI 模型

#### Google Gemini 2.0 Flash
- 配置项: `GEMINI_API_KEY`
- 特点: 快速、支持长文本和图像
- 适用场景: 清晰的 PDF 文档

#### Qwen VL Max (新增)
- 配置项: `QWEN_API_KEY`
- API 地址: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- 模型名称: `qwen-vl-max` (可改为 `qwen3-vl-flash` 以提升速度)
- 特点: 对中文识别效果好，支持复杂版面
- 适用场景: 中文试卷、复杂版面的扫描件

### 3. 前端选择界面
- 导入页面新增"选择AI模型"下拉框
- 显示每个模型的配置状态（可用/未配置）
- 只允许选择已配置的模型
- 使用 Sparkles 图标标识 AI 功能

### 4. 新增 API 端点

#### GET /api/papers/models
获取可用模型列表
```json
{
  "success": true,
  "models": [
    {
      "type": "gemini",
      "name": "Google Gemini 2.0 Flash",
      "available": true
    },
    {
      "type": "qwen-vl",
      "name": "Qwen VL Max",
      "available": true
    }
  ]
}
```

## 文件变更

### 后端

#### 新增文件
- `backend/services/ai_models/__init__.py` - AI 模型模块
- `backend/services/ai_models/base.py` - 抽象基类和枚举
- `backend/services/ai_models/gemini.py` - Gemini 模型实现
- `backend/services/ai_models/qwen_vl.py` - Qwen VL 模型实现

#### 修改文件
- `backend/config.py`
  - 新增 `GEMINI_API_KEY` 配置
  - 新增 `QWEN_API_KEY` 配置
  - 新增 `DEFAULT_AI_MODEL` 配置

- `backend/services/pdf_import_service.py`
  - 重构为支持多模型架构
  - 添加 `model_type` 参数
  - 添加 `get_available_models()` 静态方法
  - 移除旧的 Gemini 专用方法

- `backend/handlers/pdf_handlers.py`
  - `parse_paper()` 支持 `model` 参数
  - 新增 `get_available_models()` 处理器

- `backend/server.py`
  - 新增路由: `GET /api/papers/models`

- `backend/.env.example`
  - 更新环境变量示例
  - 添加 QWEN_API_KEY 配置

### 前端

#### 修改文件
- `src/app/components/ImportPaperPage.tsx`
  - 新增 AI 模型选择状态
  - 新增模型列表加载逻辑
  - 新增模型选择 UI 组件
  - 上传时传递选中的模型参数
  - 添加 `Sparkles` 图标导入

## 配置说明

### 环境变量配置

在 `backend/.env` 文件中添加：

```bash
# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key_here
QWEN_API_KEY=your_qwen_key_here
DEFAULT_AI_MODEL=gemini
```

### Qwen API 配置细节

```python
# 基础 URL
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# 模型选择
MODEL_NAME = "qwen-vl-max"  # 高质量
# 或
MODEL_NAME = "qwen3-vl-flash"  # 更快速度

# OpenAI 兼容的调用格式
{
  "model": "qwen-vl-max",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        {"type": "text", "text": "prompt"}
      ]
    }
  ]
}
```

## 使用方法

### 开发环境设置

1. 配置环境变量:
```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入 API Keys
```

2. 重启后端服务:
```bash
python main.py
```

3. 前端自动检测可用模型

### 用户操作流程

1. 进入"导入试卷"页面
2. 从下拉框选择AI模型（Gemini 或 Qwen VL）
3. 上传PDF文件
4. 点击"开始解析"
5. 等待AI处理（1-2分钟）
6. 预览和确认导入

## 扩展新模型

如需添加其他AI模型（如 Claude、GPT-4V 等）：

1. 在 `backend/services/ai_models/` 创建新文件
2. 继承 `AIModel` 基类
3. 实现必要的方法
4. 在 `AIModelType` 枚举中添加新类型
5. 更新 `PDFImportService` 的创建和获取逻辑

示例骨架：
```python
class NewModel(AIModel):
    @property
    def name(self) -> str:
        return "New Model Display Name"
    
    @property
    def model_type(self) -> AIModelType:
        return AIModelType.NEW_MODEL
    
    async def extract_from_text(self, text_content, filename, prompt):
        # 实现逻辑
        pass
    
    async def extract_from_images(self, images_base64, filename, prompt):
        # 实现逻辑
        pass
```

## 测试建议

1. **配置测试**: 分别测试只配置 Gemini、只配置 Qwen、两者都配置的情况
2. **模型切换**: 测试同一PDF用不同模型解析的结果差异
3. **错误处理**: 测试 API Key 无效、网络错误等异常情况
4. **性能测试**: 对比不同模型的解析速度和准确度

## 注意事项

1. **API 配额**: Qwen API 可能有调用限制，注意监控用量
2. **成本控制**: 不同模型计费方式不同，建议设置使用上限
3. **数据安全**: PDF 内容会发送到第三方 API，注意数据隐私
4. **兼容性**: 旧的导入数据不受影响，新功能向后兼容

## 已知问题

1. Qwen VL 对某些特殊格式的 LaTeX 可能需要额外调整
2. 图像模式下大文件可能超时，建议分页处理

## 后续计划

- [ ] 添加模型性能监控和统计
- [ ] 支持自定义提示词模板
- [ ] 添加模型结果对比功能
- [ ] 支持本地部署的开源模型

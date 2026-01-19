# AI 模型后端配置说明

## 概述

系统现在支持多个 AI 模型后端，用于PDF试卷的自动识别和提取。用户可以在导入试卷时选择不同的AI模型。

## 支持的模型

### 1. Google Gemini 2.0 Flash
- **类型**: `gemini`
- **名称**: Google Gemini 2.0 Flash
- **特点**: 
  - 快速响应
  - 支持长文本和图像识别
  - 适合清晰的PDF文档
- **配置**: 需要在 `.env` 中设置 `GEMINI_API_KEY`

### 2. Qwen VL Max
- **类型**: `qwen-vl`
- **名称**: Qwen VL Max
- **特点**: 
  - 阿里云通义千问视觉模型
  - 对中文识别效果好
  - 支持复杂版面分析
- **配置**: 需要在 `.env` 中设置 `QWEN_API_KEY`

## 配置方法

### 1. 环境变量配置

在 `backend/.env` 文件中添加以下配置：

```bash
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Qwen API Key
QWEN_API_KEY=your_qwen_api_key_here

# 默认使用的AI模型 ("gemini" 或 "qwen-vl")
DEFAULT_AI_MODEL=gemini
```

### 2. 获取 API Key

#### Gemini API Key
1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 创建新的 API Key
3. 复制 Key 到 `.env` 文件

#### Qwen API Key (已提供)
- 使用提供的 Key: `your_qwen_key_here`
- 或访问 [阿里云百炼平台](https://dashscope.console.aliyun.com/) 获取新的 Key

## 使用方法

### 前端选择模型

1. 进入"导入试卷"页面
2. 在上传文件前，从"选择AI模型"下拉框中选择要使用的模型
3. 只有已配置 API Key 的模型才可选择
4. 上传PDF文件并开始解析

### API 调用

#### 获取可用模型列表
```bash
GET /api/papers/models
Authorization: Bearer <token>

Response:
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

#### 解析PDF（指定模型）
```bash
POST /api/papers/parse
Authorization: Bearer <token>
Content-Type: multipart/form-data

Body:
- file: PDF文件
- model: "gemini" 或 "qwen-vl" (可选，不指定则使用默认模型)

Response:
{
  "success": true,
  "preview": {
    "title": "2024年高考英语试卷",
    "year": 2024,
    "totalQuestions": 15,
    "questions": [...]
  }
}
```

## 架构说明

### 代码结构

```
backend/
├── services/
│   ├── ai_models/
│   │   ├── __init__.py          # 模块导出
│   │   ├── base.py              # 抽象基类
│   │   ├── gemini.py            # Gemini 实现
│   │   └── qwen_vl.py           # Qwen VL 实现
│   └── pdf_import_service.py    # PDF导入服务（使用AI模型）
├── handlers/
│   └── pdf_handlers.py          # PDF相关API处理器
├── config.py                     # 配置管理
└── .env.example                  # 环境变量示例
```

### 扩展新模型

要添加新的AI模型，请：

1. 在 `backend/services/ai_models/` 创建新的模型实现文件
2. 继承 `AIModel` 基类
3. 实现 `extract_from_text` 和 `extract_from_images` 方法
4. 在 `__init__.py` 中导出新模型
5. 在 `PDFImportService._create_model()` 中添加模型创建逻辑
6. 在 `PDFImportService.get_available_models()` 中添加模型信息
7. 在 `config.py` 中添加相应的环境变量

示例：
```python
from .base import AIModel, AIModelType

class NewModel(AIModel):
    @property
    def name(self) -> str:
        return "New Model Name"
    
    @property
    def model_type(self) -> AIModelType:
        return AIModelType.NEW_MODEL
    
    async def extract_from_text(self, text_content: str, filename: str, prompt: str):
        # 实现文本提取逻辑
        pass
    
    async def extract_from_images(self, images_base64: List[str], filename: str, prompt: str):
        # 实现图像提取逻辑
        pass
```

## 注意事项

1. **API配额**: 不同的AI服务有不同的调用限制和计费方式，请注意监控使用量
2. **响应速度**: 图像模式（扫描版PDF）比文本模式慢，通常需要1-2分钟
3. **识别准确度**: 不同模型对不同类型的试卷识别效果可能有差异，建议测试后选择最适合的模型
4. **API Key 安全**: 不要将 API Key 提交到版本控制系统，使用 `.env` 文件管理
5. **并发限制**: 某些API有并发请求限制，大量导入时需要注意

## 故障排查

### 模型不可用
- 检查 `.env` 文件中是否正确配置了 API Key
- 重启后端服务以加载新的环境变量
- 检查 API Key 是否有效（是否过期、是否有配额）

### 解析失败
- 检查 PDF 文件是否损坏
- 尝试切换其他AI模型
- 查看后端日志了解详细错误信息

### API 错误
- 检查网络连接
- 验证 API Key 的有效性
- 查看具体的错误响应信息

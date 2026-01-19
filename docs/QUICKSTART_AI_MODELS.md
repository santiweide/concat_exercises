# 快速开始 - 配置多AI模型支持

本指南帮助你快速配置和使用新增的多AI模型功能。

## 第一步：配置环境变量

### 1. 复制配置模板

```bash
cd backend
cp .env.example .env
```

### 2. 编辑 `.env` 文件

使用文本编辑器打开 `backend/.env` 文件，填入 API Keys：

```bash
# Gemini API Key (可选)
GEMINI_API_KEY=your_gemini_api_key_here

# Qwen API Key (已提供)
QWEN_API_KEY=your_qwen_key_here

# 默认使用的模型
DEFAULT_AI_MODEL=qwen-vl
```

**说明：**
- 至少配置一个 API Key
- 建议配置 Qwen API Key（已提供有效的 Key）
- `DEFAULT_AI_MODEL` 可以设置为 `gemini` 或 `qwen-vl`

### 3. 获取 Gemini API Key (可选)

如果你想使用 Gemini 模型：

1. 访问 https://aistudio.google.com/app/apikey
2. 登录 Google 账号
3. 创建新的 API Key
4. 复制 Key 到 `.env` 文件的 `GEMINI_API_KEY`

## 第二步：测试配置

运行测试脚本验证配置是否正确：

```bash
cd backend
python test_ai_models.py
```

预期输出示例：
```
🧪 AI Model Configuration Test

============================================================
Environment Variables Check
============================================================
GEMINI_API_KEY: ✗ Not set
QWEN_API_KEY: ✓ Set
  Value: sk-60709d...7b0b
DEFAULT_AI_MODEL: qwen-vl

============================================================
Testing Qwen VL Model
============================================================
✓ Model initialized: Qwen VL Max
  Model type: qwen-vl
  Model name: qwen-vl-max
  Base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1

============================================================
Testing PDFImportService Integration
============================================================

Available models: 2
  - Google Gemini 2.0 Flash (gemini): ✗ Not configured
  - Qwen VL Max (qwen-vl): ✓ Available

Testing service creation:
  ✓ Qwen VL service created: Qwen VL Max
  ✓ Default service created: Qwen VL Max

============================================================
Test Summary
============================================================
Qwen VL: ✓ PASS

✅ All tests passed!
```

## 第三步：启动服务

### 启动后端

```bash
cd backend
python main.py
```

你应该看到：
```
INFO     Starting HTTP server on 0.0.0.0:8080
INFO     Routes configured
```

### 启动前端

在新的终端窗口：

```bash
npm run dev
```

## 第四步：使用新功能

1. **打开浏览器**: 访问 http://localhost:5173

2. **登录系统**: 使用你的账号登录

3. **进入导入页面**: 点击"导入试卷"

4. **选择AI模型**: 
   - 在文件上传区域上方，你会看到"选择AI模型"下拉框
   - 选择可用的模型（例如 "Qwen VL Max"）

5. **上传PDF**: 
   - 拖拽PDF文件到上传区，或点击"选择文件"
   - 点击"开始解析"

6. **等待解析**: 
   - 系统会显示进度条
   - 通常需要 1-2 分钟

7. **预览和确认**: 
   - 解析完成后，预览提取的题目
   - 确认无误后点击"确认导入"

## 常见问题

### Q: 看不到模型选择框？
A: 确保前端已重新加载。按 Ctrl+R (或 Cmd+R) 刷新页面。

### Q: 所有模型都显示"未配置"？
A: 检查 `.env` 文件是否正确配置，并重启后端服务。

### Q: 解析失败？
A: 
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看后端日志了解详细错误
4. 尝试切换到其他模型

### Q: Qwen API 调用失败？
A: 
1. 确认使用的是提供的 API Key: `your_qwen_key_here`
2. 检查是否有网络限制（需要访问 dashscope-intl.aliyuncs.com）
3. 查看是否超出配额限制

### Q: 想添加更多模型？
A: 参考 [docs/AI_MODELS.md](./AI_MODELS.md) 中的"扩展新模型"部分。

## 性能建议

### 模型选择建议

**Gemini 2.0 Flash:**
- 速度: ⚡⚡⚡ 快
- 准确度: ⭐⭐⭐⭐ 高
- 适用: 清晰的PDF文档、英文试卷
- 成本: 免费额度较高

**Qwen VL Max:**
- 速度: ⚡⚡ 中等
- 准确度: ⭐⭐⭐⭐⭐ 很高
- 适用: 中文试卷、复杂版面、扫描件
- 成本: 按调用次数计费

### 优化建议

1. **清晰的PDF**: 优先使用文本模式（更快）
2. **扫描件**: 必须使用图像模式（较慢）
3. **大文件**: 系统会自动限制页数（最多15页）
4. **批量导入**: 建议分批处理，避免并发调用

## 下一步

- 📖 阅读完整文档: [docs/AI_MODELS.md](./AI_MODELS.md)
- 🔧 查看更新说明: [docs/MULTI_MODEL_UPDATE.md](./MULTI_MODEL_UPDATE.md)
- 🐛 报告问题: 在项目中创建 Issue

## 获取帮助

如遇到问题：

1. 查看后端日志: `backend/logs/ep.log.wf`
2. 运行测试脚本: `python backend/test_ai_models.py`
3. 检查浏览器控制台错误
4. 联系开发团队

---

**祝使用愉快！** 🎉

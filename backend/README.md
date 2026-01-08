# Exam Paper System - Python Backend

基于 ZeroMQ 的考试试卷系统后端服务。

## 架构

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│   Frontend      │     │              Backend                      │
│   (React)       │────▶│  ┌────────────┐                          │
└─────────────────┘     │  │ HTTP Server│ (aiohttp)                │
                        │  │ :8080      │                          │
                        │  └─────┬──────┘                          │
                        │        │ ZeroMQ                          │
                        │   ┌────┴────┐                            │
                        │   │         │                            │
                        │   ▼         ▼                            │
                        │ ┌─────────┐ ┌─────────┐                  │
                        │ │Question │ │ Queue   │                  │
                        │ │Service  │ │ Service │                  │
                        │ │ :5555   │ │ :5556   │                  │
                        │ └────┬────┘ └────┬────┘                  │
                        │      │           │                       │
                        │      └─────┬─────┘                       │
                        │            ▼                             │
                        │      ┌──────────┐                        │
                        │      │ Storage  │ (In-Memory/SQLite)     │
                        │      └──────────┘                        │
                        └──────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 运行服务

#### 开发模式（All-in-One）

```bash
python main.py
```

这会同时启动：
- HTTP 服务器 (http://localhost:8080)
- Question Service (tcp://127.0.0.1:5555)
- Queue Service (tcp://127.0.0.1:5556)

#### 生产模式（分离部署）

```bash
# 终端 1: Question Service
python main.py --question-service

# 终端 2: Queue Service
python main.py --queue-service

# 终端 3: HTTP Server
python main.py --http-only
```

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:8080/health

# 搜索题目
curl -X POST http://localhost:8080/api/questions/search \
  -H "Content-Type: application/json" \
  -d '{"query": "科技", "pagination": {"page": 1, "pageSize": 10}}'

# 获取所有标签
curl http://localhost:8080/api/questions/labels

# 获取所有年份
curl http://localhost:8080/api/questions/years
```

## 配置

通过环境变量配置（也可创建 `.env` 文件）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| HTTP_HOST | 0.0.0.0 | HTTP 服务器监听地址 |
| HTTP_PORT | 8080 | HTTP 服务器端口 |
| ZMQ_QUESTION_SERVICE_ADDR | tcp://127.0.0.1:5555 | Question Service 地址 |
| ZMQ_QUEUE_SERVICE_ADDR | tcp://127.0.0.1:5556 | Queue Service 地址 |
| LOG_LEVEL | INFO | 日志级别 |

## 项目结构

```
backend/
├── main.py              # 主入口，如果用微服务架构则用main.py启动
├── config.py            # 配置
├── models.py            # Pydantic 数据模型
├── server.py            # HTTP 服务器 & 路由，all in one
├── storage.py           # 数据存储（内存/数据库）
├── zmq_service.py       # ZeroMQ 通信层
├── handlers/
│   ├── __init__.py
│   ├── question_handlers.py  # 题目 API 处理器
│   └── queue_handlers.py     # 队列 API 处理器
├── services/
│   ├── __init__.py
│   ├── question_service.py   # 题目业务逻辑
│   └── queue_service.py      # 队列业务逻辑
└── requirements.txt     # Python 依赖
```

## API 文档

完整的 API 文档请参见 [idl/API.md](../idl/API.md)

## ZeroMQ 通信协议

### 消息格式

**请求 (Request)**
```json
{
  "id": "uuid",
  "action": "search_questions",
  "payload": { ... }
}
```

**响应 (Response)**
```json
{
  "id": "uuid",
  "success": true,
  "data": { ... },
  "error": null
}
```

### 支持的 Actions

#### Question Service
- `search_questions`
- `get_question`
- `batch_get_questions`
- `create_question`
- `update_question`
- `delete_question`
- `get_all_labels`
- `get_all_years`

#### Queue Service
- `list_queues`
- `get_queue`
- `create_queue`
- `update_queue`
- `delete_queue`
- `add_question_to_queue`
- `remove_question_from_queue`
- `reorder_queue_questions`
- `toggle_queue_freeze`
- `add_collaborator`
- `remove_collaborator`
- `export_queue`

## 扩展

### 添加数据库支持

1. 修改 `storage.py` 实现数据库存储
2. 支持 SQLite (开发) 或 PostgreSQL (生产)

### 添加认证

1. 在 `server.py` 添加认证中间件
2. 从请求头获取 JWT token 并验证

### 添加语义搜索

1. 集成向量数据库 (如 Milvus, Pinecone)
2. 在 `question_service.py` 中实现语义搜索逻辑


```
SERVICE_NAME=exam LOG_DIR=/var/log/exam python server.py
```
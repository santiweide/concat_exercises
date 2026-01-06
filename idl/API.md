# Exam Paper System - Backend API 接口文档

本文档描述了前端需要的后端 HTTP API 接口，基于 protobuf 定义。

## 基础信息

- **Base URL**: `http://localhost:8080` (开发环境)
- **Content-Type**: `application/json`
- **编码**: UTF-8

---

## 1. Question Service - 题目服务

### 1.1 搜索题目

支持语义搜索的题目查询接口。

```
POST /api/questions/search
```

**Request Body:**
```json
{
  "query": "科技发展",
  "year": 2023,
  "labels": ["科技", "社会"],
  "pagination": {
    "page": 1,
    "pageSize": 20
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 否 | 搜索关键词（语义搜索） |
| year | int | 否 | 年份过滤 |
| labels | string[] | 否 | 标签过滤（多选） |
| pagination.page | int | 是 | 页码，从1开始 |
| pagination.pageSize | int | 是 | 每页数量 |

**Response:**
```json
{
  "questions": [
    {
      "id": "q-001",
      "title": "2023年全国卷I",
      "year": 2023,
      "questionNumber": "A",
      "articleContent": "文章内容...",
      "questionContent": "题目和选项...",
      "labels": ["科技", "社会"],
      "createdAt": 1704067200000,
      "updatedAt": 1704067200000
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  }
}
```

---

### 1.2 获取单个题目

```
GET /api/questions/{id}
```

**Path Parameters:**
| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 题目ID |

**Response:**
```json
{
  "question": {
    "id": "q-001",
    "title": "2023年全国卷I",
    "year": 2023,
    "questionNumber": "A",
    "articleContent": "文章内容...",
    "questionContent": "题目和选项...",
    "labels": ["科技", "社会"],
    "createdAt": 1704067200000,
    "updatedAt": 1704067200000
  }
}
```

---

### 1.3 批量获取题目

```
POST /api/questions/batch
```

**Request Body:**
```json
{
  "ids": ["q-001", "q-002", "q-003"]
}
```

**Response:**
```json
{
  "questions": [
    { "id": "q-001", ... },
    { "id": "q-002", ... },
    { "id": "q-003", ... }
  ]
}
```

---

### 1.4 获取所有标签

```
GET /api/questions/labels
```

**Response:**
```json
{
  "labels": ["科技", "社会", "文化", "经济", "环境"]
}
```

---

### 1.5 获取所有年份

```
GET /api/questions/years
```

**Response:**
```json
{
  "years": [2024, 2023, 2022, 2021, 2020]
}
```

---

## 2. Queue Service - 队列服务

### 2.1 获取用户队列列表

```
GET /api/queues?userEmail={email}&page={page}&pageSize={pageSize}
```

**Query Parameters:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userEmail | string | 是 | 用户邮箱 |
| page | int | 否 | 页码 |
| pageSize | int | 否 | 每页数量 |

**Response:**
```json
{
  "queues": [
    {
      "id": "queue-001",
      "name": "2024高考模拟卷1",
      "questionIds": ["q-001", "q-002"],
      "frozen": false,
      "owner": "user@example.com",
      "collaborators": ["other@example.com"],
      "createdAt": 1704067200000,
      "updatedAt": 1704067200000
    }
  ],
  "pagination": {
    "total": 10,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

---

### 2.2 获取队列详情

```
GET /api/queues/{id}
```

**Response:**
```json
{
  "queue": {
    "queue": {
      "id": "queue-001",
      "name": "2024高考模拟卷1",
      "questionIds": ["q-001", "q-002"],
      "frozen": false,
      "owner": "user@example.com",
      "collaborators": []
    },
    "questions": [
      { "id": "q-001", "title": "2023年全国卷I", ... },
      { "id": "q-002", "title": "2023年全国卷II", ... }
    ]
  }
}
```

---

### 2.3 创建队列

```
POST /api/queues
```

**Request Body:**
```json
{
  "name": "新建模拟卷",
  "owner": "user@example.com"
}
```

**Response:**
```json
{
  "queue": {
    "id": "queue-002",
    "name": "新建模拟卷",
    "questionIds": [],
    "frozen": false,
    "owner": "user@example.com",
    "collaborators": [],
    "createdAt": 1704067200000,
    "updatedAt": 1704067200000
  }
}
```

---

### 2.4 更新队列

```
PATCH /api/queues/{id}
```

**Request Body:**
```json
{
  "id": "queue-001",
  "name": "更新后的名称"
}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.5 删除队列

```
DELETE /api/queues/{id}
```

**Response:** `204 No Content`

---

### 2.6 添加题目到队列

```
POST /api/queues/{queue_id}/questions
```

**Request Body:**
```json
{
  "questionId": "q-003",
  "position": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| questionId | string | 是 | 题目ID |
| position | int | 否 | 插入位置（0开始），不提供则添加到末尾 |

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.7 从队列移除题目

```
DELETE /api/queues/{queue_id}/questions/{question_id}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.8 重排队列题目顺序

```
PUT /api/queues/{queue_id}/reorder
```

**Request Body:**
```json
{
  "questionIds": ["q-002", "q-001", "q-003"]
}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.9 冻结/解冻队列

```
PUT /api/queues/{queue_id}/freeze
```

**Request Body:**
```json
{
  "frozen": true
}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.10 添加协作者

```
POST /api/queues/{queue_id}/collaborators
```

**Request Body:**
```json
{
  "collaboratorEmail": "collaborator@example.com"
}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.11 移除协作者

```
DELETE /api/queues/{queue_id}/collaborators/{email}
```

**Response:**
```json
{
  "queue": { ... }
}
```

---

### 2.12 导出队列

```
POST /api/queues/{queue_id}/export
```

**Request Body:**
```json
{
  "format": 1
}
```

| format 值 | 说明 |
|-----------|------|
| 1 | JSON 格式 |
| 2 | PDF 格式 |
| 3 | Word 文档 |

**Response:** 二进制文件流

---

## 错误响应格式

所有接口在发生错误时返回统一格式：

```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "details": {
    "field": "year",
    "reason": "must be a positive integer"
  }
}
```

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

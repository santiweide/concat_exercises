# 前端使用 Protocol Buffers 指南

本文档介绍如何在前端项目中使用 protobuf 与后端通信。

## 1. 安装依赖

```bash
# 使用 protobuf-ts 方案（推荐用于 TypeScript 项目）
npm install @protobuf-ts/runtime @protobuf-ts/grpc-transport
npm install -D @protobuf-ts/plugin @protobuf-ts/protoc

# 或者使用 protobuf.js 方案
npm install protobufjs
npm install -D protobufjs-cli
```

## 2. 生成 TypeScript 代码

### 方案 A: 使用 protobuf-ts（推荐）

在 `package.json` 中添加脚本：

```json
{
  "scripts": {
    "proto:generate": "protoc --ts_out=src/api/generated --proto_path=proto proto/*.proto"
  }
}
```

运行生成命令：
```bash
npm run proto:generate
```

### 方案 B: 使用 buf（更现代的工具链）

1. 安装 buf：
```bash
brew install bufbuild/buf/buf
# 或
npm install -D @bufbuild/buf @bufbuild/protoc-gen-es @bufbuild/protobuf
```

2. 创建 `buf.yaml`：
```yaml
version: v1
breaking:
  use:
    - FILE
lint:
  use:
    - DEFAULT
```

3. 创建 `buf.gen.yaml`：
```yaml
version: v1
plugins:
  - plugin: es
    out: src/api/generated
    opt: target=ts
  - plugin: connect-es
    out: src/api/generated
    opt: target=ts
```

4. 运行：
```bash
npx buf generate proto
```

## 3. 生成的代码结构

生成后的目录结构：

```
src/
├── api/
│   ├── generated/
│   │   ├── exam_paper.ts         # 消息类型定义
│   │   └── exam_paper.client.ts  # gRPC 客户端
│   ├── client.ts                  # API 客户端封装
│   └── hooks/                     # React Hooks
│       ├── useQuestions.ts
│       └── useQueue.ts
```

## 4. 通信方式选择

由于浏览器不直接支持 gRPC（需要 HTTP/2 trailers），有以下几种方案：

### 方案 A: gRPC-Web（推荐）

后端需要部署 Envoy 代理或使用 gRPC-Web 兼容的框架。

```bash
npm install @connectrpc/connect @connectrpc/connect-web
```

### 方案 B: Connect 协议（最简单）

Connect 是 gRPC 的 HTTP/1.1 兼容协议，支持 JSON 和二进制两种格式。

### 方案 C: REST + Protobuf

使用 HTTP REST API，但请求和响应体使用 protobuf 序列化。

## 5. 前端 API 客户端实现

参考 `src/api/client.ts` 和 `src/api/hooks/` 目录下的实现。

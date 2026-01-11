// 这是模拟 protobuf-ts 生成的类型定义
// 实际项目中应该通过 protoc 工具从 .proto 文件生成

// ============================================================================
// Common Types
// ============================================================================

export interface PaginationRequest {
  page: number;
  pageSize: number;
}

export interface PaginationResponse {
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ============================================================================
// Core Data Models
// ============================================================================

export interface ReadingQuestion {
  id: string;
  title: string;
  year: number;
  section?: string; // 第一部分 知识运用, 第二部分 阅读理解, 第三部分 书面表达
  subsection?: string; // 第一节, 第二节
  questionNumber: string;
  articleContent: string; // LaTeX格式
  questionContent: string; // LaTeX格式
  labels: string[];
  answers?: { number: number | string; answer: string }[]; // 答案列表
  subQuestionCount?: number; // 小题数量
  createdAt: bigint;
  updatedAt: bigint;
}

export interface Queue {
  id: string;
  name: string;
  questionIds: string[];
  frozen: boolean;
  owner: string;
  collaborators: string[];
  createdAt: bigint;
  updatedAt: bigint;
}

export interface QueueDetail {
  queue: Queue;
  questions: ReadingQuestion[];
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string;
  createdAt: bigint;
}

// ============================================================================
// Question Service Types
// ============================================================================

export interface SearchQuestionsRequest {
  query: string;
  year?: number;
  labels: string[];
  pagination?: PaginationRequest;
}

export interface SearchQuestionsResponse {
  questions: ReadingQuestion[];
  pagination?: PaginationResponse;
}

export interface GetQuestionRequest {
  id: string;
}

export interface GetQuestionResponse {
  question?: ReadingQuestion;
}

export interface BatchGetQuestionsRequest {
  ids: string[];
}

export interface BatchGetQuestionsResponse {
  questions: ReadingQuestion[];
}

export interface CreateQuestionRequest {
  title: string;
  year: number;
  questionNumber: string;
  articleContent: string;
  questionContent: string;
  labels: string[];
}

export interface CreateQuestionResponse {
  question?: ReadingQuestion;
}

export interface UpdateQuestionRequest {
  id: string;
  title?: string;
  year?: number;
  questionNumber?: string;
  articleContent?: string;
  questionContent?: string;
  labels?: string[];
}

export interface UpdateQuestionResponse {
  question?: ReadingQuestion;
}

export interface DeleteQuestionRequest {
  id: string;
}

export interface GetAllLabelsResponse {
  labels: string[];
}

export interface GetAllYearsResponse {
  years: number[];
}

// ============================================================================
// Queue Service Types
// ============================================================================

export interface ListQueuesRequest {
  userEmail: string;
  pagination?: PaginationRequest;
}

export interface ListQueuesResponse {
  queues: Queue[];
  pagination?: PaginationResponse;
}

export interface GetQueueRequest {
  id: string;
}

export interface GetQueueResponse {
  queue?: QueueDetail;
}

export interface CreateQueueRequest {
  name: string;
  owner: string;
}

export interface CreateQueueResponse {
  queue?: Queue;
}

export interface UpdateQueueRequest {
  id: string;
  name?: string;
}

export interface UpdateQueueResponse {
  queue?: Queue;
}

export interface DeleteQueueRequest {
  id: string;
}

export interface AddQuestionToQueueRequest {
  queueId: string;
  questionId: string;
  position?: number;
}

export interface AddQuestionToQueueResponse {
  queue?: Queue;
}

export interface RemoveQuestionFromQueueRequest {
  queueId: string;
  questionId: string;
}

export interface RemoveQuestionFromQueueResponse {
  queue?: Queue;
}

export interface ReorderQueueQuestionsRequest {
  queueId: string;
  questionIds: string[];
}

export interface ReorderQueueQuestionsResponse {
  queue?: Queue;
}

export interface ToggleQueueFreezeRequest {
  queueId: string;
  frozen: boolean;
}

export interface ToggleQueueFreezeResponse {
  queue?: Queue;
}

export interface AddCollaboratorRequest {
  queueId: string;
  collaboratorEmail: string;
}

export interface AddCollaboratorResponse {
  queue?: Queue;
}

export interface RemoveCollaboratorRequest {
  queueId: string;
  collaboratorEmail: string;
}

export interface RemoveCollaboratorResponse {
  queue?: Queue;
}

export enum ExportFormat {
  UNSPECIFIED = 0,
  JSON = 1,
  PDF = 2,
  WORD = 3,
}

export interface ExportQueueRequest {
  queueId: string;
  format: ExportFormat;
}

export interface ExportQueueResponse {
  data: Uint8Array;
  filename: string;
  contentType: string;
}

// ============================================================================
// Type Converters (用于前端类型和 protobuf 类型之间的转换)
// ============================================================================

import type { ReadingQuestion as FrontendQuestion, Queue as FrontendQueue } from '../../app/types';

/**
 * 将 protobuf ReadingQuestion 转换为前端类型
 */
export function toFrontendQuestion(proto: ReadingQuestion): FrontendQuestion {
  return {
    id: proto.id,
    title: proto.title,
    year: proto.year,
    questionNumber: proto.questionNumber,
    articleContent: proto.articleContent,
    questionContent: proto.questionContent,
    labels: proto.labels,
  };
}

/**
 * 将前端 ReadingQuestion 转换为 protobuf 类型
 */
export function toProtoQuestion(frontend: FrontendQuestion): Omit<ReadingQuestion, 'createdAt' | 'updatedAt'> {
  return {
    id: frontend.id,
    title: frontend.title,
    year: frontend.year,
    questionNumber: frontend.questionNumber,
    articleContent: frontend.articleContent,
    questionContent: frontend.questionContent,
    labels: frontend.labels,
  };
}

/**
 * 将 protobuf QueueDetail 转换为前端 Queue 类型
 */
export function toFrontendQueue(proto: QueueDetail): FrontendQueue {
  return {
    id: proto.queue.id,
    name: proto.queue.name,
    questions: proto.questions.map(toFrontendQuestion),
    frozen: proto.queue.frozen,
    owner: proto.queue.owner,
    collaborators: proto.queue.collaborators,
  };
}

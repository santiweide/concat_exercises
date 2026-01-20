import { createPromiseClient, Transport } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import * as pb from './generated/exam_paper';

// ============================================================================
// 配置
// ============================================================================
// In production: empty string means use current domain (frontend and backend same origin)
// In development: can be overridden via VITE_API_URL env var (e.g., http://localhost:8080)
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// 创建 Connect 传输层
const transport: Transport = createConnectTransport({
  baseUrl: API_BASE_URL,
  // 使用 JSON 格式（方便调试），生产环境可切换为 binary
  useBinaryFormat: import.meta.env.PROD,
});

// ============================================================================
// Question Service Client
// ============================================================================

export const questionService = {
  /**
   * 搜索题目（支持语义搜索）
   */
  async search(params: {
    query?: string;
    year?: number;
    labels?: string[];
    page?: number;
    pageSize?: number;
  }): Promise<pb.SearchQuestionsResponse> {
    const request: pb.SearchQuestionsRequest = {
      query: params.query || '',
      year: params.year,
      labels: params.labels || [],
      pagination: {
        page: params.page || 1,
        pageSize: params.pageSize || 20,
      },
    };

    const response = await fetch(`${API_BASE_URL}/api/questions/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 获取单个题目
   */
  async get(id: string): Promise<pb.GetQuestionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/questions/${id}`);
    
    if (!response.ok) {
      throw new Error(`Get question failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 批量获取题目
   */
  async batchGet(ids: string[]): Promise<pb.BatchGetQuestionsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/questions/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ids }),
    });

    if (!response.ok) {
      throw new Error(`Batch get questions failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 获取所有标签
   */
  async getAllLabels(): Promise<pb.GetAllLabelsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/questions/labels`);
    
    if (!response.ok) {
      throw new Error(`Get labels failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 获取所有年份
   */
  async getAllYears(): Promise<pb.GetAllYearsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/questions/years`);
    
    if (!response.ok) {
      throw new Error(`Get years failed: ${response.statusText}`);
    }

    return response.json();
  },
};

// ============================================================================
// Queue Service Client
// ============================================================================

export const queueService = {
  /**
   * 获取用户的队列列表
   */
  async list(userEmail: string, pagination?: pb.PaginationRequest): Promise<pb.ListQueuesResponse> {
    const params = new URLSearchParams({
      userEmail,
      ...(pagination && {
        page: String(pagination.page),
        pageSize: String(pagination.pageSize),
      }),
    });

    const response = await fetch(`${API_BASE_URL}/api/queues?${params}`);
    
    if (!response.ok) {
      throw new Error(`List queues failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 获取队列详情
   */
  async get(id: string): Promise<pb.GetQueueResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${id}`);
    
    if (!response.ok) {
      throw new Error(`Get queue failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 创建队列
   */
  async create(request: pb.CreateQueueRequest): Promise<pb.CreateQueueResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Create queue failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 更新队列
   */
  async update(request: pb.UpdateQueueRequest): Promise<pb.UpdateQueueResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${request.id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Update queue failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 删除队列
   */
  async delete(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Delete queue failed: ${response.statusText}`);
    }
  },

  /**
   * 添加题目到队列
   */
  async addQuestion(request: pb.AddQuestionToQueueRequest): Promise<pb.AddQuestionToQueueResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${request.queueId}/questions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        questionId: request.questionId,
        position: request.position,
      }),
    });

    if (!response.ok) {
      throw new Error(`Add question to queue failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 从队列移除题目
   */
  async removeQuestion(queueId: string, questionId: string): Promise<pb.RemoveQuestionFromQueueResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${queueId}/questions/${questionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Remove question from queue failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 重排队列题目顺序
   */
  async reorderQuestions(request: pb.ReorderQueueQuestionsRequest): Promise<pb.ReorderQueueQuestionsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${request.queueId}/reorder`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        questionIds: request.questionIds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Reorder queue questions failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 添加协作者
   */
  async addCollaborator(queueId: string, email: string): Promise<pb.AddCollaboratorResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${queueId}/collaborators`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ collaboratorEmail: email }),
    });

    if (!response.ok) {
      throw new Error(`Add collaborator failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 移除协作者
   */
  async removeCollaborator(queueId: string, email: string): Promise<pb.RemoveCollaboratorResponse> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${queueId}/collaborators/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Remove collaborator failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 导出队列
   */
  async export(queueId: string, format: pb.ExportFormat): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/queues/${queueId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ format }),
    });

    if (!response.ok) {
      throw new Error(`Export queue failed: ${response.statusText}`);
    }

    return response.blob();
  },
};

// ============================================================================
// 导出统一的 API 客户端
// ============================================================================

export const api = {
  questions: questionService,
  queues: queueService,
};

export default api;

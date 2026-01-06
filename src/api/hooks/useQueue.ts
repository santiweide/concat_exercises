import { useState, useEffect, useCallback } from 'react';
import { queueService } from '../client';
import * as pb from '../generated/exam_paper';
import { toFrontendQueue, toFrontendQuestion } from '../generated/exam_paper';
import type { ReadingQuestion, Queue } from '../../app/types';
import { toast } from 'sonner';

/**
 * 队列详情 Hook
 */
export function useQueue(queueId: string | null) {
  const [queue, setQueue] = useState<Queue | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchQueue = useCallback(async () => {
    if (!queueId) {
      setQueue(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await queueService.get(queueId);
      if (response.queue) {
        setQueue(toFrontendQueue(response.queue));
      }
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  return { queue, isLoading, error, refetch: fetchQueue };
}

/**
 * 用户队列列表 Hook
 */
export function useQueues(userEmail: string) {
  const [queues, setQueues] = useState<pb.Queue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchQueues = async () => {
      try {
        const response = await queueService.list(userEmail);
        setQueues(response.queues);
      } catch (e) {
        setError(e instanceof Error ? e : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchQueues();
  }, [userEmail]);

  return { queues, isLoading, error };
}

/**
 * 队列操作 Hook
 */
export function useQueueActions(queueId: string) {
  const [isLoading, setIsLoading] = useState(false);

  const addQuestion = useCallback(async (questionId: string, position?: number) => {
    setIsLoading(true);
    try {
      await queueService.addQuestion({
        queueId,
        questionId,
        position,
      });
      toast.success('题目已添加到队列');
    } catch (e) {
      toast.error('添加失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const removeQuestion = useCallback(async (questionId: string) => {
    setIsLoading(true);
    try {
      await queueService.removeQuestion(queueId, questionId);
      toast.success('题目已从队列移除');
    } catch (e) {
      toast.error('移除失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const reorderQuestions = useCallback(async (questionIds: string[]) => {
    setIsLoading(true);
    try {
      await queueService.reorderQuestions({
        queueId,
        questionIds,
      });
    } catch (e) {
      toast.error('重排序失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const toggleFreeze = useCallback(async (frozen: boolean) => {
    setIsLoading(true);
    try {
      await queueService.toggleFreeze(queueId, frozen);
      toast.success(frozen ? '队列已冻结' : '队列已解冻');
    } catch (e) {
      toast.error('操作失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const addCollaborator = useCallback(async (email: string) => {
    setIsLoading(true);
    try {
      await queueService.addCollaborator(queueId, email);
      toast.success('协作者已添加');
    } catch (e) {
      toast.error('添加协作者失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const removeCollaborator = useCallback(async (email: string) => {
    setIsLoading(true);
    try {
      await queueService.removeCollaborator(queueId, email);
      toast.success('协作者已移除');
    } catch (e) {
      toast.error('移除协作者失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  const exportQueue = useCallback(async (format: pb.ExportFormat) => {
    setIsLoading(true);
    try {
      const blob = await queueService.export(queueId, format);
      
      // 下载文件
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `queue-${queueId}.${format === pb.ExportFormat.JSON ? 'json' : format === pb.ExportFormat.PDF ? 'pdf' : 'docx'}`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast.success('队列已导出');
    } catch (e) {
      toast.error('导出失败');
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [queueId]);

  return {
    isLoading,
    addQuestion,
    removeQuestion,
    reorderQuestions,
    toggleFreeze,
    addCollaborator,
    removeCollaborator,
    exportQueue,
  };
}

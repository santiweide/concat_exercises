import { useState, useEffect, useCallback } from 'react';
import { questionService } from '../client';
import * as pb from '../generated/exam_paper';
import { toFrontendQuestion } from '../generated/exam_paper';
import type { ReadingQuestion } from '../../app/types';

interface UseQuestionsOptions {
  query?: string;
  year?: number;
  labels?: string[];
  page?: number;
  pageSize?: number;
  enabled?: boolean;
}

interface UseQuestionsResult {
  questions: ReadingQuestion[];
  pagination: pb.PaginationResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * 题目搜索 Hook
 */
export function useQuestions(options: UseQuestionsOptions = {}): UseQuestionsResult {
  const { query, year, labels, page = 1, pageSize = 20, enabled = true } = options;
  
  const [questions, setQuestions] = useState<ReadingQuestion[]>([]);
  const [pagination, setPagination] = useState<pb.PaginationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchQuestions = useCallback(async () => {
    if (!enabled) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await questionService.search({
        query,
        year,
        labels,
        page,
        pageSize,
      });
      
      // 转换为前端类型
      const frontendQuestions = response.questions.map(toFrontendQuestion);
      setQuestions(frontendQuestions);
      setPagination(response.pagination || null);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [query, year, labels, page, pageSize, enabled]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  return {
    questions,
    pagination,
    isLoading,
    error,
    refetch: fetchQuestions,
  };
}

/**
 * 单个题目 Hook
 */
export function useQuestion(id: string | null) {
  const [question, setQuestion] = useState<ReadingQuestion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!id) {
      setQuestion(null);
      return;
    }

    const fetchQuestion = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await questionService.get(id);
        if (response.question) {
          setQuestion(toFrontendQuestion(response.question));
        } else {
          setQuestion(null);
        }
      } catch (e) {
        setError(e instanceof Error ? e : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuestion();
  }, [id]);

  return { question, isLoading, error };
}

/**
 * 获取所有标签 Hook
 */
export function useLabels() {
  const [labels, setLabels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchLabels = async () => {
      try {
        const response = await questionService.getAllLabels();
        setLabels(response.labels);
      } catch (e) {
        setError(e instanceof Error ? e : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchLabels();
  }, []);

  return { labels, isLoading, error };
}

/**
 * 获取所有年份 Hook
 */
export function useYears() {
  const [years, setYears] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchYears = async () => {
      try {
        const response = await questionService.getAllYears();
        setYears(response.years);
      } catch (e) {
        setError(e instanceof Error ? e : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchYears();
  }, []);

  return { years, isLoading, error };
}

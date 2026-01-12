import React, { useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from './ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';
import { Alert, AlertDescription } from './ui/alert';
import { 
  ArrowLeft, Trash2, RotateCcw, Search, History, Eye, 
  ChevronLeft, ChevronRight, Loader2, AlertCircle, Info
} from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '../../api/config';
import { useAuth } from '../contexts/AuthContext';

// Types
interface QuestionAnswer {
  number: number;
  answer: string;
}

interface Question {
  id: string;
  title: string;
  year: number;
  questionNumber: string;
  articleContent: string;
  questionContent: string;
  labels: string[];
  answers: QuestionAnswer[];
  subQuestionCount: number;
  createdAt: number;
  updatedAt: number;
  deleted?: boolean;
  deletedAt?: number;
}

interface OperationLog {
  id: string;
  operationType: number; // 1=CREATE, 2=DELETE, 3=RESTORE
  questionId: string;
  questionTitle: string;
  questionNumber: string;
  articleContent: string;
  questionContent: string;
  answers: QuestionAnswer[];
  operatorEmail: string;
  operatedAt: number;
}

interface QuestionManagementPageProps {
  onBack: () => void;
}

export function QuestionManagementPage({ onBack }: QuestionManagementPageProps) {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('questions');
  
  // Questions state
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [questionsPage, setQuestionsPage] = useState(1);
  const [questionsTotalPages, setQuestionsTotalPages] = useState(1);
  const [questionsTotal, setQuestionsTotal] = useState(0);
  
  // Deleted questions state
  const [deletedQuestions, setDeletedQuestions] = useState<Question[]>([]);
  const [loadingDeleted, setLoadingDeleted] = useState(false);
  const [deletedPage, setDeletedPage] = useState(1);
  const [deletedTotalPages, setDeletedTotalPages] = useState(1);
  
  // Operation logs state
  const [logs, setLogs] = useState<OperationLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [logsPage, setLogsPage] = useState(1);
  const [logsTotalPages, setLogsTotalPages] = useState(1);
  
  // Dialog states
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [questionToDelete, setQuestionToDelete] = useState<Question | null>(null);
  const [showBatchDeleteDialog, setShowBatchDeleteDialog] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [questionToRestore, setQuestionToRestore] = useState<Question | null>(null);
  const [showLogDetail, setShowLogDetail] = useState(false);
  const [selectedLog, setSelectedLog] = useState<OperationLog | null>(null);
  const [showQuestionPreview, setShowQuestionPreview] = useState(false);
  const [previewQuestion, setPreviewQuestion] = useState<Question | null>(null);
  
  const PAGE_SIZE = 10;
  
  // Fetch questions
  const fetchQuestions = useCallback(async () => {
    if (!token) return;
    
    setLoadingQuestions(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/management/questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: searchQuery,
          page: questionsPage,
          pageSize: PAGE_SIZE,
          includeDeleted: false,
        }),
      });
      
      const data = await response.json();
      if (data.questions) {
        setQuestions(data.questions);
        setQuestionsTotalPages(data.totalPages || 1);
        setQuestionsTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      toast.error('加载题目失败');
    } finally {
      setLoadingQuestions(false);
    }
  }, [token, searchQuery, questionsPage]);
  
  // Fetch deleted questions
  const fetchDeletedQuestions = useCallback(async () => {
    if (!token) return;
    
    setLoadingDeleted(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/management/questions/deleted?page=${deletedPage}&pageSize=${PAGE_SIZE}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      const data = await response.json();
      if (data.questions) {
        setDeletedQuestions(data.questions);
        setDeletedTotalPages(data.totalPages || 1);
      }
    } catch (error) {
      console.error('Failed to fetch deleted questions:', error);
      toast.error('加载已删除题目失败');
    } finally {
      setLoadingDeleted(false);
    }
  }, [token, deletedPage]);
  
  // Fetch operation logs
  const fetchLogs = useCallback(async () => {
    if (!token) return;
    
    setLoadingLogs(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/management/logs?page=${logsPage}&pageSize=${PAGE_SIZE}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      const data = await response.json();
      if (data.logs) {
        setLogs(data.logs);
        setLogsTotalPages(data.totalPages || 1);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      toast.error('加载操作日志失败');
    } finally {
      setLoadingLogs(false);
    }
  }, [token, logsPage]);
  
  // Load data based on active tab
  useEffect(() => {
    if (activeTab === 'questions') {
      fetchQuestions();
    } else if (activeTab === 'deleted') {
      fetchDeletedQuestions();
    } else if (activeTab === 'logs') {
      fetchLogs();
    }
  }, [activeTab, fetchQuestions, fetchDeletedQuestions, fetchLogs]);
  
  // Handle search
  const handleSearch = () => {
    setQuestionsPage(1);
    fetchQuestions();
  };
  
  // Handle soft delete
  const handleDelete = async () => {
    if (!questionToDelete || !token) return;
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/management/questions/${questionToDelete.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      const data = await response.json();
      if (data.success) {
        toast.success('题目已删除');
        fetchQuestions();
        fetchDeletedQuestions();
        fetchLogs();
      } else {
        toast.error(data.error || '删除失败');
      }
    } catch (error) {
      console.error('Failed to delete question:', error);
      toast.error('删除失败');
    } finally {
      setShowDeleteDialog(false);
      setQuestionToDelete(null);
    }
  };
  
  // Handle batch delete
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0 || !token) return;
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/management/questions/batch-delete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ ids: Array.from(selectedIds) }),
        }
      );
      
      const data = await response.json();
      if (data.deletedCount > 0) {
        toast.success(`已删除 ${data.deletedCount} 道题目`);
        setSelectedIds(new Set());
        fetchQuestions();
        fetchDeletedQuestions();
        fetchLogs();
      } else {
        toast.error('批量删除失败');
      }
    } catch (error) {
      console.error('Failed to batch delete:', error);
      toast.error('批量删除失败');
    } finally {
      setShowBatchDeleteDialog(false);
    }
  };
  
  // Handle restore
  const handleRestore = async () => {
    if (!questionToRestore || !token) return;
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/management/questions/${questionToRestore.id}/restore`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      const data = await response.json();
      if (data.success) {
        toast.success('题目已恢复');
        fetchQuestions();
        fetchDeletedQuestions();
        fetchLogs();
      } else {
        toast.error(data.error || '恢复失败');
      }
    } catch (error) {
      console.error('Failed to restore question:', error);
      toast.error('恢复失败');
    } finally {
      setShowRestoreDialog(false);
      setQuestionToRestore(null);
    }
  };
  
  // Toggle selection
  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };
  
  // Toggle all selection
  const toggleSelectAll = () => {
    if (selectedIds.size === questions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(questions.map(q => q.id)));
    }
  };
  
  // Format timestamp
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  // Get operation type label
  const getOperationLabel = (type: number) => {
    switch (type) {
      case 1: return { label: '添加', variant: 'default' as const };
      case 2: return { label: '删除', variant: 'destructive' as const };
      case 3: return { label: '恢复', variant: 'secondary' as const };
      default: return { label: '未知', variant: 'outline' as const };
    }
  };
  
  // Get summary text
  const getSummary = (text: string, maxLength: number = 50) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };
  
  // Format answers for display
  const formatAnswers = (answers: QuestionAnswer[]) => {
    if (!answers || answers.length === 0) return '无答案';
    return answers.map(a => `${a.number}:${a.answer}`).join(', ');
  };
  
  return (
    <div className="size-full bg-gray-50">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={onBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回
              </Button>
              <div>
                <h1 className="text-2xl">题库编辑</h1>
                <p className="text-sm text-gray-500 mt-1">
                  管理题库中的题目，查看操作流水
                </p>
              </div>
            </div>
          </div>
        </header>
        
        {/* Main Content */}
        <div className="flex-1 overflow-hidden p-6">
          <Card className="h-full">
            <CardContent className="p-0 h-full flex flex-col">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                <TabsList className="w-full justify-start rounded-none border-b px-4">
                  <TabsTrigger value="questions" className="gap-2">
                    <Search className="h-4 w-4" />
                    题库列表
                  </TabsTrigger>
                  <TabsTrigger value="deleted" className="gap-2">
                    <Trash2 className="h-4 w-4" />
                    已删除
                  </TabsTrigger>
                  <TabsTrigger value="logs" className="gap-2">
                    <History className="h-4 w-4" />
                    操作流水
                  </TabsTrigger>
                </TabsList>
                
                {/* Questions Tab */}
                <TabsContent value="questions" className="flex-1 overflow-hidden m-0 p-4 flex flex-col">
                  {/* Info Alert */}
                  <Alert className="mb-4 border-blue-200 bg-blue-50">
                    <Info className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-sm text-blue-800">
                      删除的题目将在数据库中保留 <strong>3天</strong>，期间可在"已删除"标签页恢复。3天后系统会自动彻底删除。
                    </AlertDescription>
                  </Alert>
                  
                  {/* Search and Actions */}
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex-1 flex gap-2">
                      <Input
                        placeholder="搜索题目..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="max-w-md"
                      />
                      <Button onClick={handleSearch} variant="secondary">
                        <Search className="h-4 w-4 mr-2" />
                        搜索
                      </Button>
                    </div>
                    {selectedIds.size > 0 && (
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => setShowBatchDeleteDialog(true)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        批量删除 ({selectedIds.size})
                      </Button>
                    )}
                  </div>
                  
                  {/* Questions Table */}
                  <div className="flex-1 border rounded-lg overflow-hidden">
                    <ScrollArea className="h-full">
                      {loadingQuestions ? (
                        <div className="flex items-center justify-center h-64">
                          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                        </div>
                      ) : questions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                          <AlertCircle className="h-12 w-12 mb-4" />
                          <p>暂无题目</p>
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-12">
                                <Checkbox 
                                  checked={selectedIds.size === questions.length && questions.length > 0}
                                  onCheckedChange={toggleSelectAll}
                                />
                              </TableHead>
                              <TableHead className="w-32">题号</TableHead>
                              <TableHead className="w-48">来源</TableHead>
                              <TableHead>文章摘要</TableHead>
                              <TableHead className="w-32">标签</TableHead>
                              <TableHead className="w-40">创建时间</TableHead>
                              <TableHead className="w-24">操作</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {questions.map((q) => (
                              <TableRow key={q.id}>
                                <TableCell>
                                  <Checkbox 
                                    checked={selectedIds.has(q.id)}
                                    onCheckedChange={() => toggleSelection(q.id)}
                                  />
                                </TableCell>
                                <TableCell className="font-medium">{q.questionNumber}</TableCell>
                                <TableCell>{q.title} ({q.year})</TableCell>
                                <TableCell className="max-w-xs truncate">
                                  {getSummary(q.articleContent, 60)}
                                </TableCell>
                                <TableCell>
                                  <div className="flex gap-1 flex-wrap">
                                    {q.labels.slice(0, 2).map((label, idx) => (
                                      <Badge key={idx} variant="secondary" className="text-xs">
                                        {label}
                                      </Badge>
                                    ))}
                                    {q.labels.length > 2 && (
                                      <Badge variant="outline" className="text-xs">
                                        +{q.labels.length - 2}
                                      </Badge>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell className="text-gray-500 text-sm">
                                  {formatTime(q.createdAt)}
                                </TableCell>
                                <TableCell>
                                  <div className="flex gap-1">
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      onClick={() => {
                                        setPreviewQuestion(q);
                                        setShowQuestionPreview(true);
                                      }}
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-destructive hover:text-destructive"
                                      onClick={() => {
                                        setQuestionToDelete(q);
                                        setShowDeleteDialog(true);
                                      }}
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </ScrollArea>
                  </div>
                  
                  {/* Pagination */}
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-gray-500">
                      共 {questionsTotal} 道题目
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={questionsPage <= 1}
                        onClick={() => setQuestionsPage(p => p - 1)}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm">
                        {questionsPage} / {questionsTotalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={questionsPage >= questionsTotalPages}
                        onClick={() => setQuestionsPage(p => p + 1)}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </TabsContent>
                
                {/* Deleted Questions Tab */}
                <TabsContent value="deleted" className="flex-1 overflow-hidden m-0 p-4 flex flex-col">
                  {/* Warning Alert */}
                  <Alert className="mb-4 border-amber-200 bg-amber-50">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-sm text-amber-800">
                      已删除的题目会在数据库中保留 <strong>3天</strong>。超过3天后，系统将在服务器启动时自动彻底删除，无法恢复。
                    </AlertDescription>
                  </Alert>
                  
                  <div className="flex-1 border rounded-lg overflow-hidden">
                    <ScrollArea className="h-full">
                      {loadingDeleted ? (
                        <div className="flex items-center justify-center h-64">
                          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                        </div>
                      ) : deletedQuestions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                          <Trash2 className="h-12 w-12 mb-4" />
                          <p>暂无已删除题目</p>
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-32">题号</TableHead>
                              <TableHead className="w-48">来源</TableHead>
                              <TableHead>文章摘要</TableHead>
                              <TableHead className="w-40">删除时间</TableHead>
                              <TableHead className="w-24">操作</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {deletedQuestions.map((q) => (
                              <TableRow key={q.id} className="bg-gray-50">
                                <TableCell className="font-medium">{q.questionNumber}</TableCell>
                                <TableCell>{q.title} ({q.year})</TableCell>
                                <TableCell className="max-w-xs truncate text-gray-500">
                                  {getSummary(q.articleContent, 60)}
                                </TableCell>
                                <TableCell className="text-gray-500 text-sm">
                                  {q.deletedAt ? formatTime(q.deletedAt) : '-'}
                                </TableCell>
                                <TableCell>
                                  <div className="flex gap-1">
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      onClick={() => {
                                        setPreviewQuestion(q);
                                        setShowQuestionPreview(true);
                                      }}
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-green-600 hover:text-green-700"
                                      onClick={() => {
                                        setQuestionToRestore(q);
                                        setShowRestoreDialog(true);
                                      }}
                                    >
                                      <RotateCcw className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </ScrollArea>
                  </div>
                  
                  {/* Pagination */}
                  <div className="flex items-center justify-end mt-4">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={deletedPage <= 1}
                        onClick={() => setDeletedPage(p => p - 1)}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm">
                        {deletedPage} / {deletedTotalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={deletedPage >= deletedTotalPages}
                        onClick={() => setDeletedPage(p => p + 1)}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </TabsContent>
                
                {/* Operation Logs Tab */}
                <TabsContent value="logs" className="flex-1 overflow-hidden m-0 p-4 flex flex-col">
                  <div className="flex-1 border rounded-lg overflow-hidden">
                    <ScrollArea className="h-full">
                      {loadingLogs ? (
                        <div className="flex items-center justify-center h-64">
                          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                        </div>
                      ) : logs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                          <History className="h-12 w-12 mb-4" />
                          <p>暂无操作记录</p>
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-24">操作类型</TableHead>
                              <TableHead className="w-32">题目ID</TableHead>
                              <TableHead className="w-48">来源</TableHead>
                              <TableHead>文章摘要</TableHead>
                              <TableHead className="w-48">操作人</TableHead>
                              <TableHead className="w-40">操作时间</TableHead>
                              <TableHead className="w-20">详情</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {logs.map((log) => {
                              const opInfo = getOperationLabel(log.operationType);
                              return (
                                <TableRow key={log.id}>
                                  <TableCell>
                                    <Badge variant={opInfo.variant}>
                                      {opInfo.label}
                                    </Badge>
                                  </TableCell>
                                  <TableCell className="font-mono text-sm">
                                    {log.questionId}
                                  </TableCell>
                                  <TableCell>
                                    {log.questionTitle} - {log.questionNumber}
                                  </TableCell>
                                  <TableCell className="max-w-xs truncate">
                                    {getSummary(log.articleContent, 50)}
                                  </TableCell>
                                  <TableCell className="text-sm">
                                    {log.operatorEmail}
                                  </TableCell>
                                  <TableCell className="text-gray-500 text-sm">
                                    {formatTime(log.operatedAt)}
                                  </TableCell>
                                  <TableCell>
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      onClick={() => {
                                        setSelectedLog(log);
                                        setShowLogDetail(true);
                                      }}
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      )}
                    </ScrollArea>
                  </div>
                  
                  {/* Pagination */}
                  <div className="flex items-center justify-end mt-4">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={logsPage <= 1}
                        onClick={() => setLogsPage(p => p - 1)}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm">
                        {logsPage} / {logsTotalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={logsPage >= logsTotalPages}
                        onClick={() => setLogsPage(p => p + 1)}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除题目「{questionToDelete?.questionNumber}」吗？
              <br />
              来源：{questionToDelete?.title} ({questionToDelete?.year})
              <br />
              <span className="text-gray-500">删除后可在"已删除"标签页中恢复，题目将保留3天后自动彻底删除。</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Batch Delete Confirmation Dialog */}
      <AlertDialog open={showBatchDeleteDialog} onOpenChange={setShowBatchDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认批量删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除选中的 {selectedIds.size} 道题目吗？
              <br />
              <span className="text-gray-500">删除后可在"已删除"标签页中恢复，题目将保留3天后自动彻底删除。</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleBatchDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Restore Confirmation Dialog */}
      <AlertDialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认恢复</AlertDialogTitle>
            <AlertDialogDescription>
              确定要恢复题目「{questionToRestore?.questionNumber}」吗？
              <br />
              来源：{questionToRestore?.title} ({questionToRestore?.year})
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleRestore}>
              确认恢复
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Log Detail Dialog */}
      <Dialog open={showLogDetail} onOpenChange={setShowLogDetail}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              操作详情
              {selectedLog && (
                <Badge variant={getOperationLabel(selectedLog.operationType).variant}>
                  {getOperationLabel(selectedLog.operationType).label}
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">题目ID：</span>
                  <span className="font-mono">{selectedLog.questionId}</span>
                </div>
                <div>
                  <span className="text-gray-500">题号：</span>
                  <span>{selectedLog.questionNumber}</span>
                </div>
                <div>
                  <span className="text-gray-500">来源：</span>
                  <span>{selectedLog.questionTitle}</span>
                </div>
                <div>
                  <span className="text-gray-500">操作人：</span>
                  <span>{selectedLog.operatorEmail}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">操作时间：</span>
                  <span>{formatTime(selectedLog.operatedAt)}</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">文章内容</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap max-h-48 overflow-auto">
                  {selectedLog.articleContent}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">题目内容</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap max-h-48 overflow-auto">
                  {selectedLog.questionContent}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">答案</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm">
                  {formatAnswers(selectedLog.answers)}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Question Preview Dialog */}
      <Dialog open={showQuestionPreview} onOpenChange={setShowQuestionPreview}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>
              题目预览 - {previewQuestion?.questionNumber}
            </DialogTitle>
          </DialogHeader>
          {previewQuestion && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">来源：</span>
                  <span>{previewQuestion.title} ({previewQuestion.year})</span>
                </div>
                <div>
                  <span className="text-gray-500">小题数量：</span>
                  <span>{previewQuestion.subQuestionCount || '-'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">标签：</span>
                  <div className="inline-flex gap-1 ml-2">
                    {previewQuestion.labels.map((label, idx) => (
                      <Badge key={idx} variant="secondary">{label}</Badge>
                    ))}
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">文章内容</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap max-h-48 overflow-auto">
                  {previewQuestion.articleContent}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">题目内容</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap max-h-48 overflow-auto">
                  {previewQuestion.questionContent}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">答案</h4>
                <div className="bg-gray-50 p-4 rounded-lg text-sm">
                  {formatAnswers(previewQuestion.answers)}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

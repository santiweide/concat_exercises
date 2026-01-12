import React, { useState, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Progress } from './ui/progress';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { 
  ArrowLeft, Upload, FileText, CheckCircle2, AlertCircle, Loader2, 
  ChevronRight, Edit2, X, Plus, Save, Eye 
} from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '../../api/config';
import { useAuth } from '../contexts/AuthContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

// Types for answers
interface QuestionAnswer {
  number: number;
  answer: string;
}

// Types for preview data
interface PreviewQuestion {
  id: string;
  section: string;
  subsection: string;
  questionNumber: string;
  articleContent: string;
  questionContent: string;
  articleSummary: string;
  subQuestionCount: number;
  labels: string[];
  answers: QuestionAnswer[];
}

interface PreviewData {
  title: string;
  year: number;
  totalQuestions: number;
  questions: PreviewQuestion[];
}

interface ImportResult {
  success: boolean;
  title: string;
  questionsImported: number;
  questions: Array<{
    id: string;
    questionNumber: string;
    labels: string[];
  }>;
  error?: string;
}

interface ImportPaperPageProps {
  onBack: () => void;
  onImportComplete?: () => void;
}

export function ImportPaperPage({ onBack, onImportComplete }: ImportPaperPageProps) {
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  
  // Overwrite confirmation dialog state
  const [showOverwriteDialog, setShowOverwriteDialog] = useState(false);
  const [duplicateTitle, setDuplicateTitle] = useState<string>('');
  
  // Edit modal state
  const [editingQuestion, setEditingQuestion] = useState<PreviewQuestion | null>(null);
  const [editFormData, setEditFormData] = useState<{
    section: string;
    subsection: string;
    articleContent: string;
    questionContent: string;
    labels: string[];
    newLabel: string;
    answers: QuestionAnswer[];
  }>({
    section: '',
    subsection: '',
    articleContent: '',
    questionContent: '',
    labels: [],
    newLabel: '',
    answers: [],
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setImportResult(null);
    } else {
      toast.error('请上传PDF文件');
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setImportResult(null);
      } else {
        toast.error('请上传PDF文件');
      }
    }
  }, []);

  const handleUpload = async () => {
    if (!file || !token) return;

    setIsUploading(true);
    setUploadProgress(0);
    setPreviewData(null);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await fetch(`${API_BASE_URL}/api/papers/parse`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const result = await response.json();

      if (response.ok && result.success) {
        setPreviewData(result.preview);
        toast.success(`成功解析 ${result.preview.totalQuestions} 道试题，请确认后导入`);
      } else {
        toast.error(result.message || '解析失败');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('上传失败，请稍后重试');
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirmImport = async (forceOverwrite: boolean = false) => {
    if (!previewData || !token) return;

    setIsConfirming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/papers/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: previewData.title,
          year: previewData.year,
          questions: previewData.questions.map(q => ({
            section: q.section || '',
            subsection: q.subsection || '',
            questionNumber: q.questionNumber,
            articleContent: q.articleContent,
            questionContent: q.questionContent,
            labels: q.labels,
            answers: q.answers || [],
            subQuestionCount: q.subQuestionCount || 0,
          })),
          forceOverwrite,
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setImportResult({
          success: true,
          title: result.title,
          questionsImported: result.questionsImported,
          questions: result.questions || [],
        });
        setPreviewData(null);
        setShowOverwriteDialog(false);
        toast.success(`成功${forceOverwrite ? '覆盖' : ''}导入 ${result.questionsImported} 道试题`);
        
        // Notify parent component to refresh questions
        if (onImportComplete) {
          onImportComplete();
        }
      } else if (result.duplicate) {
        // Paper with same title already exists, show confirmation dialog
        setDuplicateTitle(previewData.title);
        setShowOverwriteDialog(true);
      } else {
        toast.error(result.message || result.error || '导入失败');
      }
    } catch (error) {
      console.error('Confirm error:', error);
      toast.error('导入失败，请稍后重试');
    } finally {
      setIsConfirming(false);
    }
  };

  const handleOverwriteConfirm = async () => {
    await handleConfirmImport(true);
  };

  const handleOverwriteCancel = () => {
    setShowOverwriteDialog(false);
    setDuplicateTitle('');
  };

  const handleEditQuestion = (question: PreviewQuestion) => {
    setEditingQuestion(question);
    setEditFormData({
      section: question.section || '',
      subsection: question.subsection || '',
      articleContent: question.articleContent,
      questionContent: question.questionContent,
      labels: [...question.labels],
      newLabel: '',
      answers: question.answers ? [...question.answers] : [],
    });
  };

  const handleSaveEdit = () => {
    if (!editingQuestion || !previewData) return;

    setPreviewData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        questions: prev.questions.map(q =>
          q.id === editingQuestion.id
            ? {
                ...q,
                section: editFormData.section,
                subsection: editFormData.subsection,
                articleContent: editFormData.articleContent,
                questionContent: editFormData.questionContent,
                labels: editFormData.labels,
                answers: editFormData.answers,
                articleSummary: editFormData.articleContent.split(' ').slice(0, 20).join(' ') + '...',
              }
            : q
        ),
      };
    });

    setEditingQuestion(null);
    toast.success('已保存修改');
  };

  const handleUpdateAnswer = (index: number, field: 'number' | 'answer', value: string) => {
    setEditFormData(prev => ({
      ...prev,
      answers: prev.answers.map((a, i) =>
        i === index
          ? { ...a, [field]: field === 'number' ? parseInt(value) || 0 : value.toUpperCase() }
          : a
      ),
    }));
  };

  const handleAddAnswer = () => {
    const lastNumber = editFormData.answers.length > 0
      ? Math.max(...editFormData.answers.map(a => a.number))
      : 20;
    setEditFormData(prev => ({
      ...prev,
      answers: [...prev.answers, { number: lastNumber + 1, answer: 'A' }],
    }));
  };

  const handleRemoveAnswer = (index: number) => {
    setEditFormData(prev => ({
      ...prev,
      answers: prev.answers.filter((_, i) => i !== index),
    }));
  };

  const handleAddLabel = () => {
    const label = editFormData.newLabel.trim();
    if (label && !editFormData.labels.includes(label)) {
      setEditFormData(prev => ({
        ...prev,
        labels: [...prev.labels, label],
        newLabel: '',
      }));
    }
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    setEditFormData(prev => ({
      ...prev,
      labels: prev.labels.filter(l => l !== labelToRemove),
    }));
  };

  const handleRemoveQuestion = (questionId: string) => {
    if (!previewData) return;
    
    setPreviewData(prev => {
      if (!prev) return prev;
      const newQuestions = prev.questions.filter(q => q.id !== questionId);
      return {
        ...prev,
        totalQuestions: newQuestions.length,
        questions: newQuestions,
      };
    });
    toast.success('已移除该题目');
  };

  const handleReset = () => {
    setFile(null);
    setPreviewData(null);
    setImportResult(null);
    setUploadProgress(0);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" size="sm" onClick={onBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回
          </Button>
          <h1 className="text-3xl font-bold">导入试卷</h1>
          <p className="text-gray-500 mt-2">
            上传试卷PDF，系统将自动提取试题和文章内容，并生成语义标签
          </p>
        </div>

        {/* Upload Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              上传试卷PDF
            </CardTitle>
            <CardDescription>
              支持高考英语试卷PDF格式，系统将使用AI自动识别和提取阅读理解题目
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center transition-colors
                ${isDragging 
                  ? 'border-blue-500 bg-blue-50' 
                  : file 
                    ? 'border-green-500 bg-green-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }
              `}
            >
              {file ? (
                <div className="flex flex-col items-center gap-3">
                  <FileText className="h-12 w-12 text-green-600" />
                  <div>
                    <p className="font-medium text-green-700">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {!isUploading && !importResult && (
                    <Button variant="outline" size="sm" onClick={handleReset}>
                      更换文件
                    </Button>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="h-12 w-12 text-gray-400" />
                  <div>
                    <p className="font-medium">拖拽PDF文件到此处</p>
                    <p className="text-sm text-gray-500">或点击下方按钮选择文件</p>
                  </div>
                  <label>
                    <input
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <Button variant="outline" asChild>
                      <span className="cursor-pointer">选择文件</span>
                    </Button>
                  </label>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {isUploading && (
              <div className="mt-6 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    正在解析试卷...
                  </span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
                <p className="text-xs text-gray-500">
                  AI正在分析PDF内容，提取试题和生成标签，这可能需要1-2分钟
                </p>
              </div>
            )}

            {/* Upload Button */}
            {file && !isUploading && !previewData && !importResult && (
              <div className="mt-6">
                <Button onClick={handleUpload} className="w-full" size="lg">
                  <Upload className="h-4 w-4 mr-2" />
                  开始解析
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Preview Card */}
        {previewData && (
          <Card className="mb-6 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5 text-blue-600" />
                <span className="text-blue-700">导入预览</span>
              </CardTitle>
              <CardDescription>
                请确认以下提取结果，点击题目可以预览和编辑内容
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-blue-50 rounded-lg mb-6">
                <div>
                  <p className="text-sm text-gray-500">试卷标题</p>
                  <p className="font-medium">{previewData.title}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">年份</p>
                  <p className="font-medium">{previewData.year}年</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">阅读大题</p>
                  <p className="font-medium">{previewData.totalQuestions} 道</p>
                </div>
              </div>

              {/* Question List */}
              <div className="space-y-3">
                {previewData.questions.map((question) => (
                  <div
                    key={question.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-lg">
                            {question.questionNumber}
                          </span>
                          <span className="text-sm text-gray-500">
                            ({question.subQuestionCount} 道小题)
                          </span>
                        </div>
                        {/* Display section and subsection */}
                        {(question.section || question.subsection) && (
                          <div className="flex items-center gap-2 mb-2">
                            {question.section && (
                              <Badge variant="outline" className="text-xs">
                                {question.section}
                              </Badge>
                            )}
                            {question.subsection && (
                              <Badge variant="outline" className="text-xs">
                                {question.subsection}
                              </Badge>
                            )}
                          </div>
                        )}
                        <p className="text-sm text-gray-600 truncate mb-2">
                          {question.articleSummary}
                        </p>
                        <div className="flex flex-wrap gap-1 mb-2">
                          {question.labels.map((label, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {label}
                            </Badge>
                          ))}
                        </div>
                        {question.answers && question.answers.length > 0 && (
                          <div className="text-xs text-gray-500">
                            答案: {question.answers.map(a => `${a.number}.${a.answer}`).join(' ')}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditQuestion(question)}
                        >
                          <Edit2 className="h-4 w-4 mr-1" />
                          查看/编辑
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleRemoveQuestion(question.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Confirm Buttons */}
              <div className="flex gap-3 mt-6">
                <Button variant="outline" onClick={handleReset} className="flex-1">
                  取消导入
                </Button>
                <Button 
                  onClick={() => handleConfirmImport(false)} 
                  className="flex-1"
                  disabled={isConfirming || previewData.questions.length === 0}
                >
                  {isConfirming ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      正在导入...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      确认导入 ({previewData.questions.length} 道)
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Result Card */}
        {importResult && (
          <Card className={importResult.success ? 'border-green-200' : 'border-red-200'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {importResult.success ? (
                  <>
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <span className="text-green-700">导入成功</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    <span className="text-red-700">导入失败</span>
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {importResult.success ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-500">试卷标题</p>
                      <p className="font-medium">{importResult.title}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">导入题目数</p>
                      <p className="font-medium">{importResult.questionsImported} 道</p>
                    </div>
                  </div>
                  
                  {importResult.questions.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">已导入的题目：</p>
                      <div className="space-y-2">
                        {importResult.questions.map((q, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                          >
                            <span className="font-medium">{q.questionNumber}</span>
                            <div className="flex gap-1">
                              {q.labels.map((label, i) => (
                                <span
                                  key={i}
                                  className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded"
                                >
                                  {label}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex gap-3">
                    <Button onClick={handleReset} variant="outline" className="flex-1">
                      继续导入
                    </Button>
                    <Button onClick={onBack} className="flex-1">
                      返回主页
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-red-600">{importResult.error}</p>
                  <Button onClick={handleReset} variant="outline">
                    重新选择文件
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Help Info */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-sm">使用说明</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 space-y-2">
            <p>1. 上传高考英语试卷的PDF文件（推荐清晰度较高的扫描件或原版PDF）</p>
            <p>2. 系统将使用Gemini AI自动识别并提取阅读理解部分的题目</p>
            <p>3. 解析完成后，您可以预览和编辑每道题目的内容和标签</p>
            <p>4. 确认无误后点击"确认导入"，题目将添加到题库中</p>
          </CardContent>
        </Card>
      </div>

      {/* Edit Question Dialog */}
      <Dialog open={!!editingQuestion} onOpenChange={(open) => !open && setEditingQuestion(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              编辑试题 {editingQuestion?.questionNumber}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Section and Subsection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">部分 (Section)</label>
                <Select 
                  value={editFormData.section} 
                  onValueChange={(value) => setEditFormData(prev => ({ ...prev, section: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择部分" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="第一部分 知识运用">第一部分 知识运用</SelectItem>
                    <SelectItem value="第二部分 阅读理解">第二部分 阅读理解</SelectItem>
                    <SelectItem value="第三部分 书面表达">第三部分 书面表达</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">小节 (Subsection)</label>
                <Select 
                  value={editFormData.subsection} 
                  onValueChange={(value) => setEditFormData(prev => ({ ...prev, subsection: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择小节" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="第一节">第一节</SelectItem>
                    <SelectItem value="第二节">第二节</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Article Content */}
            <div>
              <label className="block text-sm font-medium mb-2">文章内容</label>
              <Textarea
                value={editFormData.articleContent}
                onChange={(e) => setEditFormData(prev => ({ ...prev, articleContent: e.target.value }))}
                rows={10}
                className="font-mono text-sm"
                placeholder="文章原文..."
              />
            </div>

            {/* Question Content */}
            <div>
              <label className="block text-sm font-medium mb-2">题目和选项</label>
              <Textarea
                value={editFormData.questionContent}
                onChange={(e) => setEditFormData(prev => ({ ...prev, questionContent: e.target.value }))}
                rows={8}
                className="font-mono text-sm"
                placeholder="题目和选项..."
              />
            </div>

            {/* Labels */}
            <div>
              <label className="block text-sm font-medium mb-2">语义标签</label>
              <div className="flex flex-wrap gap-2 mb-3">
                {editFormData.labels.map((label, index) => (
                  <Badge key={index} variant="secondary" className="gap-1 pr-1">
                    {label}
                    <button
                      onClick={() => handleRemoveLabel(label)}
                      className="ml-1 hover:text-red-600 rounded-full"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
                {editFormData.labels.length === 0 && (
                  <span className="text-sm text-gray-400">暂无标签</span>
                )}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="添加新标签..."
                  value={editFormData.newLabel}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, newLabel: e.target.value }))}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddLabel())}
                  className="flex-1"
                />
                <Button onClick={handleAddLabel} size="sm" variant="outline">
                  <Plus className="h-4 w-4 mr-1" />
                  添加
                </Button>
              </div>
            </div>

            {/* Answers */}
            <div>
              <label className="block text-sm font-medium mb-2">答案（题号 + 选项）</label>
              <div className="space-y-2 mb-3">
                {editFormData.answers.map((answer, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      type="number"
                      value={answer.number}
                      onChange={(e) => handleUpdateAnswer(index, 'number', e.target.value)}
                      className="w-20"
                      placeholder="题号"
                    />
                    <span className="text-gray-500">.</span>
                    <select
                      value={answer.answer}
                      onChange={(e) => handleUpdateAnswer(index, 'answer', e.target.value)}
                      className="h-10 px-3 py-2 border border-gray-200 rounded-md bg-white text-sm"
                    >
                      <option value="A">A</option>
                      <option value="B">B</option>
                      <option value="C">C</option>
                      <option value="D">D</option>
                    </select>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => handleRemoveAnswer(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                {editFormData.answers.length === 0 && (
                  <span className="text-sm text-gray-400">暂无答案（可能未从试卷中提取到）</span>
                )}
              </div>
              <Button onClick={handleAddAnswer} size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-1" />
                添加答案
              </Button>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingQuestion(null)}>
              取消
            </Button>
            <Button onClick={handleSaveEdit}>
              <Save className="h-4 w-4 mr-2" />
              保存修改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Overwrite Confirmation Dialog */}
      <Dialog open={showOverwriteDialog} onOpenChange={setShowOverwriteDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <AlertCircle className="h-5 w-5" />
              试卷已存在
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-gray-700">
              试卷「<span className="font-semibold">{duplicateTitle}</span>」已存在于数据库中。
            </p>
            <p className="text-gray-600 mt-2">
              是否覆盖更新现有数据？此操作将删除该试卷的所有旧题目，并导入新的题目数据。
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={handleOverwriteCancel}
              disabled={isConfirming}
            >
              取消
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleOverwriteConfirm}
              disabled={isConfirming}
            >
              {isConfirming ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  覆盖中...
                </>
              ) : (
                '确认覆盖'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

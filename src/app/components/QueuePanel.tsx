import React, { useState } from 'react';
import { ReadingQuestion, Queue } from '../types';
import { QuestionCard } from './QuestionCard';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  Trash2, 
  Download, 
  Upload, 
  UserPlus,
  Save,
  BarChart3,
  FileText,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  Loader2,
  Sparkles,
  Copy,
  Check,
  FileCode,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { ExamProgressDashboard, EXAM_PAPER_CONFIG } from './ExamProgressDashboard';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { toast } from 'sonner';

interface ProofreadIssue {
  rule: string;
  severity: 'error' | 'warning' | 'info' | 'pass';
  description: string;
  location: string;
  suggestion: string;
}

interface ProofreadResult {
  success: boolean;
  error?: string;
  score: number;
  summary: string;
  issues: ProofreadIssue[];
  auto_fixes: { description: string; original: string; fixed: string }[];
  fixed_latex?: string | null;
}

interface QueuePanelProps {
  queue: Queue;
  onRemoveQuestion: (questionId: string) => void;
  onReorderQuestions: (newOrder: ReadingQuestion[]) => void;
  onSave?: () => void;
  saving?: boolean;
  hasUnsavedChanges?: boolean;
  onExport: () => void;
  onImport: (file: File) => void;
  onViewQuestion: (question: ReadingQuestion) => void;
  onAddCollaborator?: (email: string) => void;
  onProofread?: () => Promise<ProofreadResult | null>;
  onGenerateFixedLatex?: (proofreadResult: ProofreadResult) => Promise<{ success: boolean; fixed_latex?: string | null; error?: string } | null>;
}

interface DraggableQuestionProps {
  question: ReadingQuestion;
  index: number;
  moveQuestion: (dragIndex: number, hoverIndex: number) => void;
  onRemove: (question: ReadingQuestion) => void;
  onView: (question: ReadingQuestion) => void;
}

const DraggableQuestion: React.FC<DraggableQuestionProps> = ({
  question,
  index,
  moveQuestion,
  onRemove,
  onView
}) => {
  const [{ isDragging }, drag, preview] = useDrag({
    type: 'question',
    item: { index },
    canDrag: true,
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'question',
    hover: (item: { index: number }) => {
      if (item.index !== index) {
        moveQuestion(item.index, index);
        item.index = index;
      }
    },
  });

  return (
    <div
      ref={(node) => {
        drop(node);
        preview(node);
      }}
      style={{ opacity: isDragging ? 0.5 : 1 }}
    >
      <QuestionCard
        question={question}
        onView={onView}
        onRemove={onRemove}
        showRemoveButton={true}
        isDraggable={true}
        dragHandleProps={{ ref: drag }}
      />
    </div>
  );
};

function SeverityIcon({ severity }: { severity: string }) {
  switch (severity) {
    case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'info': return <Info className="h-4 w-4 text-blue-500" />;
    case 'pass': return <CheckCircle className="h-4 w-4 text-green-500" />;
    default: return <Info className="h-4 w-4 text-gray-500" />;
  }
}

function severityLabel(severity: string) {
  switch (severity) {
    case 'error': return { text: '错误', variant: 'destructive' as const };
    case 'warning': return { text: '警告', variant: 'secondary' as const };
    case 'info': return { text: '建议', variant: 'outline' as const };
    case 'pass': return { text: '通过', variant: 'default' as const };
    default: return { text: severity, variant: 'outline' as const };
  }
}

export function QueuePanel({
  queue,
  onRemoveQuestion,
  onReorderQuestions,
  onSave,
  saving,
  hasUnsavedChanges,
  onExport,
  onImport,
  onViewQuestion,
  onAddCollaborator,
  onProofread,
  onGenerateFixedLatex
}: QueuePanelProps) {
  const [collaboratorEmail, setCollaboratorEmail] = useState('');
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);
  const [proofreadDialogOpen, setProofreadDialogOpen] = useState(false);
  const [proofreadResult, setProofreadResult] = useState<ProofreadResult | null>(null);
  const [proofreadLoading, setProofreadLoading] = useState(false);
  const [proofreadFilter, setProofreadFilter] = useState<string>('all');
  const [fixedLatex, setFixedLatex] = useState<string | null>(null);
  const [fixLoading, setFixLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showLatexCode, setShowLatexCode] = useState(true);

  const handleProofread = async () => {
    if (!onProofread) return;
    setProofreadDialogOpen(true);
    setProofreadLoading(true);
    setProofreadResult(null);
    setFixedLatex(null);
    try {
      const result = await onProofread();
      setProofreadResult(result);
    } catch {
      setProofreadResult({
        success: false,
        error: 'AI校对请求失败，请稍后重试',
        score: 0,
        summary: '',
        issues: [],
        auto_fixes: [],
      });
    } finally {
      setProofreadLoading(false);
    }
  };

  const handleGenerateFixedLatex = async () => {
    if (!onGenerateFixedLatex || !proofreadResult) return;
    setFixLoading(true);
    setFixedLatex(null);
    try {
      const result = await onGenerateFixedLatex(proofreadResult);
      if (result?.success && result.fixed_latex) {
        setFixedLatex(result.fixed_latex);
        toast.success('修正版LaTeX已生成');
      } else {
        toast.error(result?.error || '生成修正版失败');
      }
    } catch {
      toast.error('生成修正版请求失败');
    } finally {
      setFixLoading(false);
    }
  };

  const handleCopyLatex = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast.success('LaTeX内容已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = content;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      toast.success('LaTeX内容已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadLatex = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'application/x-latex; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('文件已下载');
  };

  // 检查队列是否完成
  const isQueueComplete = () => {
    const progressData: { section: string; subsection: string; current: number; max: number }[] = [];
    
    EXAM_PAPER_CONFIG.sections.forEach((section) => {
      section.subsections.forEach((subsection) => {
        const count = queue.questions.filter(
          (q) => q.section === section.name && q.subsection === subsection.name
        ).length;
        
        progressData.push({
          section: section.name,
          subsection: subsection.name,
          current: count,
          max: subsection.maxQuestions,
        });
      });
    });
    
    const totalCurrent = progressData.reduce((sum, item) => sum + item.current, 0);
    const totalMax = progressData.reduce((sum, item) => sum + item.max, 0);
    const hasExceeded = progressData.some((item) => item.current > item.max);
    
    return totalCurrent === totalMax && !hasExceeded && totalMax > 0;
  };

  const queueComplete = isQueueComplete();

  const moveQuestion = (dragIndex: number, hoverIndex: number) => {
    const newQuestions = [...queue.questions];
    const [removed] = newQuestions.splice(dragIndex, 1);
    newQuestions.splice(hoverIndex, 0, removed);
    onReorderQuestions(newQuestions);
  };

  const handleAddCollaborator = () => {
    if (collaboratorEmail.trim() && onAddCollaborator) {
      onAddCollaborator(collaboratorEmail.trim());
      setCollaboratorEmail('');
    } else if (!onAddCollaborator) {
      toast.error('邀请功能暂不可用');
    }
  };

  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImport(file);
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-full flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{queue.name}</CardTitle>
                <div className="flex gap-2 mt-2 items-center">
                  {queueComplete && (
                  <Badge variant="default" className="bg-green-500">
                    <FileText className="h-3 w-3 mr-1" />
                    组卷完成
                  </Badge>
                )}                  <span className="text-sm text-gray-500">
                    {queue.questions.length} 道题目
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                {onSave && (
                  <Button
                    size="sm"
                    variant={hasUnsavedChanges ? "default" : "outline"}
                    onClick={onSave}
                    disabled={!hasUnsavedChanges || saving}
                  >
                    <Save className="size-4 mr-1" />
                    {saving ? '保存中...' : '保存'}
                  </Button>
                )}
                <Dialog open={progressDialogOpen} onOpenChange={setProgressDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline">
                      <BarChart3 className="size-4 mr-1" />
                      组卷进度
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>试卷组卷进度</DialogTitle>
                      <DialogDescription>
                        查看当前组卷进度和各部分题目配置情况
                      </DialogDescription>
                    </DialogHeader>
                    <ExamProgressDashboard questions={queue.questions} />
                  </DialogContent>
                </Dialog>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onExport}
                  disabled={!queueComplete}
                  title={
                    !queueComplete 
                      ? "请完成组卷后再导出" 
                      : "导出试卷为LaTeX格式"
                  }
                >
                  <Download className="size-4 mr-1" />
                  导出试卷
                </Button>
                {onProofread && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleProofread}
                    disabled={!queueComplete || proofreadLoading}
                    title={
                      !queueComplete
                        ? "请完成组卷后再校对"
                        : "使用AI校对LaTeX试卷格式"
                    }
                  >
                    {proofreadLoading ? (
                      <Loader2 className="size-4 mr-1 animate-spin" />
                    ) : (
                      <Sparkles className="size-4 mr-1" />
                    )}
                    AI校对
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => document.getElementById('file-import')?.click()}
                >
                  <Upload className="size-4 mr-1" />
                  导入
                </Button>
                <input
                  id="file-import"
                  type="file"
                  accept=".json"
                  className="hidden"
                  onChange={handleFileImport}
                />
              </div>
            </div>

            {/* Collaborator Section */}
            <div className="mt-4">
              <div className="flex gap-2">
                <Input
                  placeholder="输入协作者邮箱..."
                  value={collaboratorEmail}
                  onChange={(e) => setCollaboratorEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddCollaborator()}
                />
                <Button size="sm" onClick={handleAddCollaborator}>
                  <UserPlus className="size-4 mr-1" />
                  邀请
                </Button>
              </div>
              {queue.collaborators.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {queue.collaborators.map((email, idx) => (
                    <Badge key={idx} variant="outline">
                      {email}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardHeader>

          {/* Proofread Results Dialog */}
          <Dialog open={proofreadDialogOpen} onOpenChange={setProofreadDialogOpen}>
            <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  AI LaTeX格式校对报告
                </DialogTitle>
                <DialogDescription>
                  基于《组卷系统格式RFC》对生成的LaTeX试卷进行格式校对
                </DialogDescription>
              </DialogHeader>

              {proofreadLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-4">
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">AI正在校对试卷格式，请稍候...</p>
                  <p className="text-xs text-muted-foreground">通常需要15-30秒</p>
                </div>
              ) : proofreadResult ? (
                <div className="flex-1 overflow-y-auto space-y-4">
                  {!proofreadResult.success ? (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <p className="text-red-700 font-medium">校对失败</p>
                      <p className="text-red-600 text-sm mt-1">{proofreadResult.error}</p>
                    </div>
                  ) : (
                    <>
                      {/* Score Overview */}
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-600">格式规范评分</p>
                            <p className={`text-4xl font-bold mt-1 ${
                              proofreadResult.score >= 80 ? 'text-green-600' :
                              proofreadResult.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                              {proofreadResult.score}
                              <span className="text-lg text-gray-400">/100</span>
                            </p>
                          </div>
                          <div className="flex gap-3 text-sm">
                            <div className="text-center">
                              <p className="text-red-500 font-bold text-lg">
                                {proofreadResult.issues.filter(i => i.severity === 'error').length}
                              </p>
                              <p className="text-gray-500">错误</p>
                            </div>
                            <div className="text-center">
                              <p className="text-yellow-500 font-bold text-lg">
                                {proofreadResult.issues.filter(i => i.severity === 'warning').length}
                              </p>
                              <p className="text-gray-500">警告</p>
                            </div>
                            <div className="text-center">
                              <p className="text-green-500 font-bold text-lg">
                                {proofreadResult.issues.filter(i => i.severity === 'pass').length}
                              </p>
                              <p className="text-gray-500">通过</p>
                            </div>
                          </div>
                        </div>
                        {proofreadResult.summary && (
                          <p className="text-sm text-gray-600 mt-3 leading-relaxed">
                            {proofreadResult.summary}
                          </p>
                        )}
                      </div>

                      {/* Filter tabs */}
                      <div className="flex gap-1 border-b pb-2">
                        {['all', 'error', 'warning', 'info', 'pass'].map(f => (
                          <Button
                            key={f}
                            size="sm"
                            variant={proofreadFilter === f ? 'default' : 'ghost'}
                            onClick={() => setProofreadFilter(f)}
                            className="text-xs h-7"
                          >
                            {f === 'all' ? '全部' : severityLabel(f).text}
                            <span className="ml-1 opacity-60">
                              ({f === 'all'
                                ? proofreadResult.issues.length
                                : proofreadResult.issues.filter(i => i.severity === f).length})
                            </span>
                          </Button>
                        ))}
                      </div>

                      {/* Issues List */}
                      <div className="space-y-2">
                        {proofreadResult.issues
                          .filter(i => proofreadFilter === 'all' || i.severity === proofreadFilter)
                          .map((issue, idx) => {
                            const badge = severityLabel(issue.severity);
                            return (
                              <div
                                key={idx}
                                className={`border rounded-md p-3 ${
                                  issue.severity === 'error' ? 'border-red-200 bg-red-50/50' :
                                  issue.severity === 'warning' ? 'border-yellow-200 bg-yellow-50/50' :
                                  issue.severity === 'pass' ? 'border-green-200 bg-green-50/50' :
                                  'border-gray-200'
                                }`}
                              >
                                <div className="flex items-start gap-2">
                                  <SeverityIcon severity={issue.severity} />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                      <Badge variant={badge.variant} className="text-xs">
                                        {badge.text}
                                      </Badge>
                                      <span className="text-xs font-mono text-gray-500">
                                        规则 {issue.rule}
                                      </span>
                                      {issue.location && (
                                        <span className="text-xs text-gray-400">
                                          · {issue.location}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-sm text-gray-700">{issue.description}</p>
                                    {issue.suggestion && (
                                      <div className="mt-2 bg-white/70 border rounded p-2">
                                        <p className="text-xs text-gray-500 mb-1">修改建议：</p>
                                        <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono">
                                          {issue.suggestion}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                      </div>

                      {/* Auto-fixes */}
                      {proofreadResult.auto_fixes.length > 0 && (
                        <div className="border-t pt-4">
                          <h4 className="text-sm font-medium mb-2">可自动修复的问题 ({proofreadResult.auto_fixes.length})</h4>
                          <div className="space-y-2">
                            {proofreadResult.auto_fixes.map((fix, idx) => (
                              <div key={idx} className="border rounded-md p-3 bg-blue-50/50">
                                <p className="text-sm font-medium text-gray-700">{fix.description}</p>
                                {fix.original && (
                                  <div className="mt-2">
                                    <p className="text-xs text-gray-500">原始：</p>
                                    <pre className="text-xs bg-red-50 p-1 rounded mt-0.5 overflow-x-auto">
                                      {fix.original}
                                    </pre>
                                  </div>
                                )}
                                {fix.fixed && (
                                  <div className="mt-1">
                                    <p className="text-xs text-gray-500">修正：</p>
                                    <pre className="text-xs bg-green-50 p-1 rounded mt-0.5 overflow-x-auto">
                                      {fix.fixed}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Generate Fixed LaTeX Section */}
                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="text-sm font-medium flex items-center gap-1.5">
                              <FileCode className="h-4 w-4" />
                              AI 修正版 LaTeX
                            </h4>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              根据校对建议，AI自动生成符合RFC规范的完整LaTeX文件
                            </p>
                          </div>
                          {!fixedLatex && onGenerateFixedLatex && (
                            <Button
                              size="sm"
                              onClick={handleGenerateFixedLatex}
                              disabled={fixLoading}
                              className="shrink-0"
                            >
                              {fixLoading ? (
                                <Loader2 className="size-4 mr-1.5 animate-spin" />
                              ) : (
                                <Sparkles className="size-4 mr-1.5" />
                              )}
                              {fixLoading ? '生成中...' : '生成修正版'}
                            </Button>
                          )}
                        </div>

                        {fixLoading && (
                          <div className="flex flex-col items-center justify-center py-8 gap-3 bg-gray-50 rounded-lg border border-dashed">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p className="text-sm text-muted-foreground">AI正在根据校对建议生成修正版LaTeX...</p>
                            <p className="text-xs text-muted-foreground">通常需要20-40秒</p>
                          </div>
                        )}

                        {fixedLatex && (
                          <div className="space-y-2">
                            {/* Action buttons */}
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="default"
                                onClick={() => handleCopyLatex(fixedLatex)}
                                className="gap-1.5"
                              >
                                {copied ? (
                                  <Check className="size-4" />
                                ) : (
                                  <Copy className="size-4" />
                                )}
                                {copied ? '已复制' : '复制全部内容'}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDownloadLatex(fixedLatex, `${queue.name}_fixed.tex`)}
                                className="gap-1.5"
                              >
                                <Download className="size-4" />
                                下载 .tex 文件
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setShowLatexCode(!showLatexCode)}
                                className="gap-1 ml-auto"
                              >
                                {showLatexCode ? (
                                  <ChevronUp className="size-4" />
                                ) : (
                                  <ChevronDown className="size-4" />
                                )}
                                {showLatexCode ? '收起代码' : '展开代码'}
                              </Button>
                            </div>

                            {/* LaTeX code viewer */}
                            {showLatexCode && (
                              <div className="relative">
                                <div className="absolute top-2 right-2 z-10">
                                  <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={() => handleCopyLatex(fixedLatex)}
                                    className="h-7 text-xs gap-1 opacity-80 hover:opacity-100"
                                  >
                                    {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
                                    {copied ? '已复制' : '复制'}
                                  </Button>
                                </div>
                                <pre className="bg-gray-950 text-gray-100 rounded-lg p-4 text-xs font-mono leading-relaxed overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre">
                                  {fixedLatex}
                                </pre>
                              </div>
                            )}

                            {/* Re-generate button */}
                            {onGenerateFixedLatex && (
                              <div className="flex justify-end">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={handleGenerateFixedLatex}
                                  disabled={fixLoading}
                                  className="text-xs gap-1"
                                >
                                  <Sparkles className="size-3" />
                                  重新生成
                                </Button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ) : null}
            </DialogContent>
          </Dialog>

          <CardContent className="flex-1 overflow-y-auto p-4">
            {queue.questions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <Trash2 className="size-12 mb-2" />
                <p>队列为空</p>
                <p className="text-sm">从右侧搜索面板添加题目</p>
              </div>
            ) : (
              <div className="space-y-3">
                {queue.questions.map((question, index) => (
                  <DraggableQuestion
                    key={question.id}
                    question={question}
                    index={index}
                    moveQuestion={moveQuestion}
                    onRemove={(q) => onRemoveQuestion(q.id)}
                    onView={onViewQuestion}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DndProvider>
  );
}

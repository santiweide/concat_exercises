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
  FileText
} from 'lucide-react';
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
  onAddCollaborator
}: QueuePanelProps) {
  const [collaboratorEmail, setCollaboratorEmail] = useState('');
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);

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

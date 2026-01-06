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
  Lock, 
  Unlock, 
  UserPlus 
} from 'lucide-react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { toast } from 'sonner';

interface QueuePanelProps {
  queue: Queue;
  onRemoveQuestion: (questionId: string) => void;
  onReorderQuestions: (newOrder: ReadingQuestion[]) => void;
  onToggleFreeze: () => void;
  onExport: () => void;
  onImport: (file: File) => void;
  onViewQuestion: (question: ReadingQuestion) => void;
}

interface DraggableQuestionProps {
  question: ReadingQuestion;
  index: number;
  moveQuestion: (dragIndex: number, hoverIndex: number) => void;
  onRemove: (question: ReadingQuestion) => void;
  onView: (question: ReadingQuestion) => void;
  frozen: boolean;
}

const DraggableQuestion: React.FC<DraggableQuestionProps> = ({
  question,
  index,
  moveQuestion,
  onRemove,
  onView,
  frozen
}) => {
  const [{ isDragging }, drag, preview] = useDrag({
    type: 'question',
    item: { index },
    canDrag: !frozen,
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'question',
    hover: (item: { index: number }) => {
      if (item.index !== index && !frozen) {
        moveQuestion(item.index, index);
        item.index = index;
      }
    },
  });

  return (
    <div
      ref={(node) => preview(drop(node))}
      style={{ opacity: isDragging ? 0.5 : 1 }}
    >
      <QuestionCard
        question={question}
        onView={onView}
        onRemove={onRemove}
        showRemoveButton={!frozen}
        isDraggable={!frozen}
        dragHandleProps={!frozen ? { ref: drag } : undefined}
      />
    </div>
  );
};

export function QueuePanel({
  queue,
  onRemoveQuestion,
  onReorderQuestions,
  onToggleFreeze,
  onExport,
  onImport,
  onViewQuestion
}: QueuePanelProps) {
  const [collaboratorEmail, setCollaboratorEmail] = useState('');

  const moveQuestion = (dragIndex: number, hoverIndex: number) => {
    const newQuestions = [...queue.questions];
    const [removed] = newQuestions.splice(dragIndex, 1);
    newQuestions.splice(hoverIndex, 0, removed);
    onReorderQuestions(newQuestions);
  };

  const handleAddCollaborator = () => {
    if (collaboratorEmail.trim()) {
      toast.success(`已邀请 ${collaboratorEmail} 协作编辑`);
      setCollaboratorEmail('');
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
                  <Badge variant={queue.frozen ? 'destructive' : 'default'}>
                    {queue.frozen ? '已冻结' : '编辑中'}
                  </Badge>
                  <span className="text-sm text-gray-500">
                    {queue.questions.length} 道题目
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onToggleFreeze}
                >
                  {queue.frozen ? (
                    <>
                      <Unlock className="size-4 mr-1" />
                      解冻
                    </>
                  ) : (
                    <>
                      <Lock className="size-4 mr-1" />
                      冻结
                    </>
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onExport}
                >
                  <Download className="size-4 mr-1" />
                  导出
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
                    frozen={queue.frozen}
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

import React, { useState, useEffect } from 'react';
import { ReadingQuestion, Queue } from './types';
import { mockQuestions } from './data/mockData';
import { QueuePanel } from './components/QueuePanel';
import { SearchPanel } from './components/SearchPanel';
import { QuestionDetail } from './components/QuestionDetail';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';

const STORAGE_KEY = 'exam-queue-system';

export default function App() {
  const [questions, setQuestions] = useState<ReadingQuestion[]>(mockQuestions);
  const [queue, setQueue] = useState<Queue>({
    id: '1',
    name: '组卷队列',
    questions: [],
    frozen: false,
    owner: 'teacher@example.com',
    collaborators: []
  });
  const [selectedQuestion, setSelectedQuestion] = useState<ReadingQuestion | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.queue) setQueue(data.queue);
        if (data.questions) setQuestions(data.questions);
      } catch (e) {
        console.error('Failed to load saved data:', e);
      }
    }
  }, []);

  // Save to localStorage whenever queue or questions change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ queue, questions }));
  }, [queue, questions]);

  const handleAddToQueue = (question: ReadingQuestion) => {
    if (queue.frozen) {
      toast.error('队列已冻结，无法添加题目');
      return;
    }

    if (queue.questions.find(q => q.id === question.id)) {
      toast.warning('该题目已在队列中');
      return;
    }

    setQueue(prev => ({
      ...prev,
      questions: [...prev.questions, question]
    }));
    toast.success('题目已添加到队列');
  };

  const handleRemoveFromQueue = (questionId: string) => {
    setQueue(prev => ({
      ...prev,
      questions: prev.questions.filter(q => q.id !== questionId)
    }));
    toast.success('题目已从队列移除');
  };

  const handleReorderQuestions = (newOrder: ReadingQuestion[]) => {
    setQueue(prev => ({
      ...prev,
      questions: newOrder
    }));
  };

  const handleToggleFreeze = () => {
    setQueue(prev => ({
      ...prev,
      frozen: !prev.frozen
    }));
    toast.success(queue.frozen ? '队列已解冻' : '队列已冻结');
  };

  const handleExport = () => {
    const data = JSON.stringify(queue, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `queue-${queue.id}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('队列已导出');
  };

  const handleImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target?.result as string);
        setQueue(imported);
        toast.success('队列已导入');
      } catch (error) {
        toast.error('导入失败：文件格式错误');
      }
    };
    reader.readAsText(file);
  };

  const handleUpdateLabels = (questionId: string, labels: string[]) => {
    // Update in main questions list
    setQuestions(prev =>
      prev.map(q => q.id === questionId ? { ...q, labels } : q)
    );

    // Update in queue if present
    setQueue(prev => ({
      ...prev,
      questions: prev.questions.map(q =>
        q.id === questionId ? { ...q, labels } : q
      )
    }));

    // Update selected question if it's the one being edited
    if (selectedQuestion?.id === questionId) {
      setSelectedQuestion(prev => prev ? { ...prev, labels } : null);
    }
  };

  return (
    <div className="size-full bg-gray-50">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="bg-white border-b px-6 py-4">
          <h1 className="text-2xl">英语阅读题组卷系统</h1>
          <p className="text-sm text-gray-500 mt-1">
            从题库中选择题目，组织成试卷队列
          </p>
        </header>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full grid grid-cols-2 gap-4 p-4">
            {/* Left Panel - Queue */}
            <QueuePanel
              queue={queue}
              onRemoveQuestion={handleRemoveFromQueue}
              onReorderQuestions={handleReorderQuestions}
              onToggleFreeze={handleToggleFreeze}
              onExport={handleExport}
              onImport={handleImport}
              onViewQuestion={setSelectedQuestion}
            />

            {/* Right Panel - Search */}
            <SearchPanel
              questions={questions}
              onAddToQueue={handleAddToQueue}
              onViewQuestion={setSelectedQuestion}
            />
          </div>
        </div>
      </div>

      {/* Question Detail Modal */}
      {selectedQuestion && (
        <QuestionDetail
          question={selectedQuestion}
          onClose={() => setSelectedQuestion(null)}
          onUpdateLabels={handleUpdateLabels}
        />
      )}

      <Toaster />
    </div>
  );
}

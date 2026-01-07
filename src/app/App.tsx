import React, { useState, useEffect } from 'react';
import { ReadingQuestion, Queue } from './types';
import { mockQuestions } from './data/mockData';
import { QueuePanel } from './components/QueuePanel';
import { SearchPanel } from './components/SearchPanel';
import { QuestionDetail } from './components/QuestionDetail';
import { LoginPage } from './components/LoginPage';
import { VerifyPage } from './components/VerifyPage';
import { QueueDashboard } from './components/QueueDashboard';
import { ImportPaperPage } from './components/ImportPaperPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';
import { Button } from './components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './components/ui/alert-dialog';
import { LogOut, User, ArrowLeft, Save, FileUp } from 'lucide-react';
import { API_BASE_URL } from '../api/config';

const STORAGE_KEY = 'exam-queue-system';

// Simple router based on URL hash
function useHashRouter() {
  const [route, setRoute] = useState(() => {
    const hash = window.location.hash.slice(1) || '/';
    return hash;
  });

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(window.location.hash.slice(1) || '/');
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (path: string) => {
    window.location.hash = path;
  };

  return { route, navigate };
}

// Get query params from hash
function getHashParams(): URLSearchParams {
  const hash = window.location.hash.slice(1);
  const queryIndex = hash.indexOf('?');
  if (queryIndex === -1) return new URLSearchParams();
  return new URLSearchParams(hash.slice(queryIndex + 1));
}

function MainApp() {
  const { user, isAuthenticated, isLoading, logout, login, token } = useAuth();
  const { route, navigate } = useHashRouter();
  
  const [questions, setQuestions] = useState<ReadingQuestion[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [selectedQueueId, setSelectedQueueId] = useState<string | null>(null);
  const [queue, setQueue] = useState<Queue>({
    id: '1',
    name: '组卷队列',
    questions: [],
    frozen: false,
    owner: user?.email || 'teacher@example.com',
    collaborators: []
  });
  const [selectedQuestion, setSelectedQuestion] = useState<ReadingQuestion | null>(null);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const [originalQueue, setOriginalQueue] = useState<Queue | null>(null);

  // Load questions from backend API
  useEffect(() => {
    if (!token) return;
    
    setLoadingQuestions(true);
    fetch(`${API_BASE_URL}/api/questions/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ page: 1, pageSize: 100 }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.questions) {
          setQuestions(data.questions);
        }
      })
      .catch(err => {
        console.error('Failed to load questions:', err);
      })
      .finally(() => setLoadingQuestions(false));
  }, [token]);

  // Update queue owner when user changes
  useEffect(() => {
    if (user?.email) {
      setQueue(prev => ({ ...prev, owner: user.email }));
    }
  }, [user?.email]);

  // Load queue from backend when selectedQueueId changes
  useEffect(() => {
    if (!selectedQueueId || !token) return;
    
    setLoadingQueue(true);
    setHasUnsavedChanges(false);
    fetch(`${API_BASE_URL}/api/queues/${selectedQueueId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then(res => res.json())
      .then(data => {
        if (data.queue) {
          const loadedQueue = {
            id: data.queue.queue.id,
            name: data.queue.queue.name,
            questions: data.queue.questions || [],
            frozen: data.queue.queue.frozen,
            owner: data.queue.queue.owner,
            collaborators: data.queue.queue.collaborators || [],
          };
          setQueue(loadedQueue);
          setOriginalQueue(loadedQueue);
        }
      })
      .catch(err => {
        console.error('Failed to load queue:', err);
        toast.error('加载队列失败');
      })
      .finally(() => setLoadingQueue(false));
  }, [selectedQueueId, token]);

  // Save queue to localStorage whenever it changes (as backup)
  useEffect(() => {
    if (queue.id !== '1') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ queue }));
    }
  }, [queue]);

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
    setHasUnsavedChanges(true);
    toast.success('题目已添加到队列');
  };

  const handleRemoveFromQueue = (questionId: string) => {
    setQueue(prev => ({
      ...prev,
      questions: prev.questions.filter(q => q.id !== questionId)
    }));
    setHasUnsavedChanges(true);
    toast.success('题目已从队列移除');
  };

  const handleReorderQuestions = (newOrder: ReadingQuestion[]) => {
    setQueue(prev => ({
      ...prev,
      questions: newOrder
    }));
    setHasUnsavedChanges(true);
  };

  const handleToggleFreeze = async () => {
    if (!token || !selectedQueueId) {
      setQueue(prev => ({
        ...prev,
        frozen: !prev.frozen
      }));
      toast.success(queue.frozen ? '队列已解冻' : '队列已冻结');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/queues/${selectedQueueId}/freeze`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ frozen: !queue.frozen }),
      });
      
      if (!response.ok) throw new Error('Failed to toggle freeze');
      
      setQueue(prev => ({
        ...prev,
        frozen: !prev.frozen
      }));
      toast.success(queue.frozen ? '队列已解冻' : '队列已冻结');
    } catch (err) {
      toast.error('操作失败');
    }
  };

  const handleSaveQueue = async () => {
    if (!token || !selectedQueueId) return;
    
    setSaving(true);
    try {
      // Update queue question order
      const response = await fetch(`${API_BASE_URL}/api/queues/${selectedQueueId}/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          questionIds: queue.questions.map(q => q.id) 
        }),
      });
      
      if (!response.ok) throw new Error('Failed to save queue');
      
      setHasUnsavedChanges(false);
      setOriginalQueue(queue);
      toast.success('队列已保存');
    } catch (err) {
      toast.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleBackToDashboard = () => {
    if (hasUnsavedChanges) {
      setShowUnsavedDialog(true);
    } else {
      setSelectedQueueId(null);
    }
  };

  const handleConfirmLeave = () => {
    setShowUnsavedDialog(false);
    setHasUnsavedChanges(false);
    setSelectedQueueId(null);
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
    setQuestions(prev =>
      prev.map(q => q.id === questionId ? { ...q, labels } : q)
    );
    setQueue(prev => ({
      ...prev,
      questions: prev.questions.map(q =>
        q.id === questionId ? { ...q, labels } : q
      )
    }));
    if (selectedQuestion?.id === questionId) {
      setSelectedQuestion(prev => prev ? { ...prev, labels } : null);
    }
  };

  const handleLogout = async () => {
    await logout();
    setSelectedQueueId(null);
    navigate('/login');
    toast.success('已退出登录');
  };

  const handleSelectQueue = (queueId: string) => {
    setSelectedQueueId(queueId);
  };

  const handleAddCollaborator = async (email: string) => {
    if (!token || !selectedQueueId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/queues/${selectedQueueId}/collaborators`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ email }),
      });
      
      if (!response.ok) throw new Error('Failed to add collaborator');
      
      const data = await response.json();
      if (data.queue) {
        setQueue(prev => ({
          ...prev,
          collaborators: data.queue.collaborators || [],
        }));
        toast.success(`已邀请 ${email} 协作编辑`);
      }
    } catch (err) {
      toast.error('邀请失败');
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  // Route: Verify magic link
  if (route.startsWith('/auth/verify')) {
    const params = getHashParams();
    const token = params.get('token') || '';
    
    return (
      <VerifyPage
        token={token}
        onVerifySuccess={(jwtToken, userData) => {
          login(jwtToken, userData);
          navigate('/');
        }}
        onNavigateToLogin={() => navigate('/login')}
      />
    );
  }

  // Route: Login page (check this BEFORE showing dashboard)
  if (route === '/login' || !isAuthenticated) {
    return <LoginPage />;
  }

  // Route: Import paper page
  if (route === '/import') {
    return (
      <>
        <ImportPaperPage onBack={() => navigate('/')} />
        <Toaster />
      </>
    );
  }

  // Main app (authenticated)
  // Show dashboard if no queue selected
  if (!selectedQueueId) {
    return (
      <div className="size-full bg-gray-50">
        <div className="h-full flex flex-col">
          {/* Header */}
          <header className="bg-white border-b px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl">英语阅读题组卷系统</h1>
                <p className="text-sm text-gray-500 mt-1">
                  从题库中选择题目，组织成试卷队列
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Button variant="outline" size="sm" onClick={() => navigate('/import')}>
                  <FileUp className="h-4 w-4 mr-2" />
                  导入试卷
                </Button>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <User className="h-4 w-4" />
                  <span>{user?.email}</span>
                </div>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  退出
                </Button>
              </div>
            </div>
          </header>

          {/* Dashboard Content */}
          <div className="flex-1 overflow-auto">
            <QueueDashboard onSelectQueue={handleSelectQueue} />
          </div>
        </div>
        <Toaster />
      </div>
    );
  }

  // Show loading state when loading queue
  if (loadingQueue) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">加载队列中...</p>
        </div>
      </div>
    );
  }

  // Queue editor view
  return (
    <div className="size-full bg-gray-50">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={handleBackToDashboard}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回
              </Button>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl">{queue.name}</h1>
                  {hasUnsavedChanges && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                      未保存
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  编辑队列 - {queue.questions.length} 道题目
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Save Button */}
              <Button 
                variant={hasUnsavedChanges ? "default" : "outline"}
                size="sm" 
                onClick={handleSaveQueue}
                disabled={!hasUnsavedChanges || saving || queue.frozen}
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? '保存中...' : '保存'}
              </Button>
              
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User className="h-4 w-4" />
                <span>{user?.email}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                退出
              </Button>
            </div>
          </div>
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
              onAddCollaborator={handleAddCollaborator}
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

      {/* Unsaved Changes Dialog */}
      <AlertDialog open={showUnsavedDialog} onOpenChange={setShowUnsavedDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>有未保存的更改</AlertDialogTitle>
            <AlertDialogDescription>
              你对队列的修改还没有保存。如果离开此页面，更改将会丢失。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>继续编辑</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmLeave}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              放弃更改
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Toaster />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../../api/config';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Label } from './ui/label';
import { Plus, Users, User, FileText } from 'lucide-react';

interface Queue {
  id: string;
  name: string;
  questionIds: string[];
  frozen: boolean;
  owner: string;
  collaborators: string[];
  createdAt: number;
  updatedAt: number;
}

interface QueueDashboardProps {
  onSelectQueue: (queueId: string) => void;
}

export function QueueDashboard({ onSelectQueue }: QueueDashboardProps) {
  const { token, user } = useAuth();
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newQueueName, setNewQueueName] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchQueues = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/queues`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch queues');
      }
      
      const data = await response.json();
      setQueues(data.queues || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueues();
  }, [token]);

  const handleCreateQueue = async () => {
    if (!newQueueName.trim() || !token) return;
    
    setCreating(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/queues`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newQueueName.trim() }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create queue');
      }
      
      setNewQueueName('');
      setCreateDialogOpen(false);
      fetchQueues();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create queue');
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">组卷队列</h1>
          <p className="text-muted-foreground">管理你的所有试卷组卷队列</p>
        </div>
        
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              新建队列
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>新建组卷队列</DialogTitle>
              <DialogDescription>
                创建一个新的组卷队列来组织你的试题
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="queue-name">队列名称</Label>
              <Input
                id="queue-name"
                value={newQueueName}
                onChange={(e) => setNewQueueName(e.target.value)}
                placeholder="例如：2024高考模拟卷"
                className="mt-2"
              />
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
              >
                取消
              </Button>
              <Button
                onClick={handleCreateQueue}
                disabled={!newQueueName.trim() || creating}
              >
                {creating ? '创建中...' : '创建'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg">
          {error}
        </div>
      )}

      {queues.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">暂无组卷队列</h3>
            <p className="text-muted-foreground mb-4">
              点击上方"新建队列"按钮创建你的第一个组卷队列
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {queues.map((queue) => {
            const isOwner = queue.owner === user?.email;
            
            return (
              <Card
                key={queue.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => onSelectQueue(queue.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg line-clamp-1">
                      {queue.name}
                    </CardTitle>
                  </div>
                  <CardDescription>
                    更新于 {formatDate(queue.updatedAt)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <Badge variant={isOwner ? 'default' : 'secondary'}>
                      {isOwner ? (
                        <>
                          <User className="h-3 w-3 mr-1" />
                          所有者
                        </>
                      ) : (
                        <>
                          <Users className="h-3 w-3 mr-1" />
                          协作者
                        </>
                      )}
                    </Badge>
                  </div>
                  
                  {/* 题目数量 */}
                  <div className="flex items-center gap-2 text-sm mb-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{queue.questionIds.length}</span>
                    <span className="text-muted-foreground">道题目</span>
                  </div>
                  
                  {/* 所有者信息 */}
                  <div className="text-xs text-muted-foreground mb-1">
                    <span className="font-medium">所有者：</span>
                    {queue.owner}
                  </div>
                  
                  {/* 协作者列表 */}
                  {queue.collaborators.length > 0 && (
                    <div className="text-xs text-muted-foreground">
                      <span className="font-medium">协作者：</span>
                      {queue.collaborators.length <= 2 
                        ? queue.collaborators.join(', ')
                        : `${queue.collaborators.slice(0, 2).join(', ')} 等${queue.collaborators.length}人`
                      }
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { ReadingQuestion } from '../types';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { X, Plus } from 'lucide-react';
import { toast } from 'sonner';

interface QuestionDetailProps {
  question: ReadingQuestion;
  onClose: () => void;
  onUpdateLabels: (questionId: string, labels: string[]) => void;
}

export function QuestionDetail({ question, onClose, onUpdateLabels }: QuestionDetailProps) {
  const [labels, setLabels] = useState<string[]>(question.labels);
  const [newLabel, setNewLabel] = useState('');

  const handleAddLabel = () => {
    if (newLabel.trim() && !labels.includes(newLabel.trim())) {
      const updatedLabels = [...labels, newLabel.trim()];
      setLabels(updatedLabels);
      onUpdateLabels(question.id, updatedLabels);
      setNewLabel('');
      toast.success('标签已添加');
    }
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    const updatedLabels = labels.filter(l => l !== labelToRemove);
    setLabels(updatedLabels);
    onUpdateLabels(question.id, updatedLabels);
    toast.success('标签已删除');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader className="sticky top-0 bg-white border-b z-10">
          <div className="flex items-center justify-between">
            <CardTitle>
              {question.title} - 阅读题{question.questionNumber}
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="size-4" />
            </Button>
          </div>
          <div className="flex gap-2 text-sm text-gray-500 mt-2">
            <span>{question.year}年</span>
            <span>·</span>
            <span>ID: {question.id}</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          {/* Labels Section */}
          <div>
            <h3 className="mb-2">标签</h3>
            <div className="flex flex-wrap gap-2 mb-3">
              {labels.map((label, index) => (
                <Badge key={index} variant="secondary" className="gap-1">
                  {label}
                  <button
                    onClick={() => handleRemoveLabel(label)}
                    className="ml-1 hover:text-red-600"
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="添加新标签..."
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddLabel()}
              />
              <Button onClick={handleAddLabel} size="sm">
                <Plus className="size-4 mr-1" />
                添加
              </Button>
            </div>
          </div>

          {/* Article Content */}
          <div>
            <h3 className="mb-2">文章内容</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="whitespace-pre-wrap">{question.articleContent}</p>
            </div>
          </div>

          {/* Questions */}
          <div>
            <h3 className="mb-2">题目</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap font-sans">{question.questionContent}</pre>
            </div>
          </div>

          {/* Answers */}
          {question.answers && question.answers.length > 0 && (
            <div>
              <h3 className="mb-2">答案</h3>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex flex-wrap gap-4">
                  {question.answers.map((answer, index) => (
                    <div key={index} className="flex items-center gap-1">
                      <span className="font-medium text-gray-700">{answer.number}.</span>
                      <span className="font-bold text-green-700">{answer.answer}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

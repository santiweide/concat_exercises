import React from 'react';
import { ReadingQuestion } from '../types';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Eye, Plus, X, GripVertical } from 'lucide-react';

interface QuestionCardProps {
  question: ReadingQuestion;
  onView: (question: ReadingQuestion) => void;
  onAdd?: (question: ReadingQuestion) => void;
  onRemove?: (question: ReadingQuestion) => void;
  showAddButton?: boolean;
  showRemoveButton?: boolean;
  isDraggable?: boolean;
  dragHandleProps?: any;
}

export function QuestionCard({
  question,
  onView,
  onAdd,
  onRemove,
  showAddButton = false,
  showRemoveButton = false,
  isDraggable = false,
  dragHandleProps
}: QuestionCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2 flex-1">
            {isDraggable && (
              <div {...dragHandleProps} className="cursor-grab active:cursor-grabbing pt-1">
                <GripVertical className="size-4 text-gray-400" />
              </div>
            )}
            <div className="flex-1">
              <CardTitle className="text-base">
                {question.title} - 题{question.questionNumber}
              </CardTitle>
              <div className="text-sm text-gray-500 mt-1">
                {question.year}年 · ID: {question.id}
              </div>
            </div>
          </div>
          <div className="flex gap-1">
            {showAddButton && onAdd && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onAdd(question)}
              >
                <Plus className="size-4" />
              </Button>
            )}
            {showRemoveButton && onRemove && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onRemove(question)}
              >
                <X className="size-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onView(question)}
            >
              <Eye className="size-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1">
          {question.labels.map((label, index) => (
            <Badge key={index} variant="secondary">
              {label}
            </Badge>
          ))}
        </div>
        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
          {question.articleContent.substring(0, 100)}...
        </p>
      </CardContent>
    </Card>
  );
}

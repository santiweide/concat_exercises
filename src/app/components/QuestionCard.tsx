import React, { useState } from 'react';
import { ReadingQuestion } from '../types';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Eye, Plus, X, GripVertical, ChevronDown, ChevronUp } from 'lucide-react';

interface QuestionCardProps {
  question: ReadingQuestion;
  onView: (question: ReadingQuestion) => void;
  onAdd?: (question: ReadingQuestion) => void;
  onRemove?: (question: ReadingQuestion) => void;
  showAddButton?: boolean;
  showRemoveButton?: boolean;
  isDraggable?: boolean;
  dragHandleProps?: any;
  showDetails?: boolean; // 是否显示详情展开功能
}

export function QuestionCard({
  question,
  onView,
  onAdd,
  onRemove,
  showAddButton = false,
  showRemoveButton = false,
  isDraggable = false,
  dragHandleProps,
  showDetails = false
}: QuestionCardProps) {
  const [expanded, setExpanded] = useState(false);

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
                {question.subQuestionCount && question.subQuestionCount > 0 && (
                  <span> · {question.subQuestionCount} 道小题</span>
                )}
                {question.section && (
                  <span> · {question.section}</span>
                )}
                {question.subsection && (
                  <span> · {question.subsection}</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-1">
            {showDetails && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setExpanded(!expanded)}
                title={expanded ? '收起详情' : '展开详情'}
              >
                {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
              </Button>
            )}
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
              title="查看完整详情"
            >
              <Eye className="size-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1 mb-2">
          {question.labels.map((label, index) => (
            <Badge key={index} variant="secondary">
              {label}
            </Badge>
          ))}
        </div>
        
        {/* 简略预览 */}
        {!expanded && (
          <p className="text-sm text-gray-600 line-clamp-2">
            {question.articleContent.substring(0, 100)}...
          </p>
        )}
        
        {/* 展开的详情 */}
        {expanded && showDetails && (
          <div className="space-y-3 mt-2">
            {/* 文章内容 */}
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">文章内容</h4>
              <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md max-h-40 overflow-y-auto whitespace-pre-wrap">
                {question.articleContent}
              </div>
            </div>
            
            {/* 题目内容 */}
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">题目内容</h4>
              <div className="text-sm text-gray-700 bg-blue-50 p-3 rounded-md max-h-40 overflow-y-auto whitespace-pre-wrap">
                {question.questionContent}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

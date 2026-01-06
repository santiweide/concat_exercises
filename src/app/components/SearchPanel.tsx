import React, { useState, useMemo } from 'react';
import { ReadingQuestion } from '../types';
import { QuestionCard } from './QuestionCard';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Search } from 'lucide-react';

interface SearchPanelProps {
  questions: ReadingQuestion[];
  onAddToQueue: (question: ReadingQuestion) => void;
  onViewQuestion: (question: ReadingQuestion) => void;
}

export function SearchPanel({ questions, onAddToQueue, onViewQuestion }: SearchPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [labelFilter, setLabelFilter] = useState<string>('all');

  // Get unique years and labels
  const years = useMemo(() => {
    const yearSet = new Set(questions.map(q => q.year));
    return Array.from(yearSet).sort((a, b) => b - a);
  }, [questions]);

  const allLabels = useMemo(() => {
    const labelSet = new Set<string>();
    questions.forEach(q => q.labels.forEach(label => labelSet.add(label)));
    return Array.from(labelSet).sort();
  }, [questions]);

  // Filter and search logic
  const filteredQuestions = useMemo(() => {
    return questions.filter(question => {
      // Year filter
      if (yearFilter !== 'all' && question.year.toString() !== yearFilter) {
        return false;
      }

      // Label filter
      if (labelFilter !== 'all' && !question.labels.includes(labelFilter)) {
        return false;
      }

      // Search query - semantic-like search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const searchableText = [
          question.title,
          question.articleContent,
          question.questionContent,
          ...question.labels
        ].join(' ').toLowerCase();

        // Split query into words for better matching
        const queryWords = query.split(/\s+/);
        return queryWords.some(word => searchableText.includes(word));
      }

      return true;
    });
  }, [questions, searchQuery, yearFilter, labelFilter]);

  return (
    <div className="h-full flex flex-col">
      <Card className="flex-1 flex flex-col">
        <CardHeader className="border-b">
          <CardTitle>题库搜索</CardTitle>
          <div className="space-y-3 mt-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 size-4 text-gray-400" />
              <Input
                placeholder="输入关键词进行语义检索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <Select value={yearFilter} onValueChange={setYearFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="年份" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有年份</SelectItem>
                  {years.map(year => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}年
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={labelFilter} onValueChange={setLabelFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="标签" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有标签</SelectItem>
                  {allLabels.map(label => (
                    <SelectItem key={label} value={label}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Active Filters Display */}
            {(searchQuery || yearFilter !== 'all' || labelFilter !== 'all') && (
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-sm text-gray-500">筛选条件:</span>
                {searchQuery && (
                  <Badge variant="outline">
                    关键词: {searchQuery}
                  </Badge>
                )}
                {yearFilter !== 'all' && (
                  <Badge variant="outline">
                    {yearFilter}年
                  </Badge>
                )}
                {labelFilter !== 'all' && (
                  <Badge variant="outline">
                    {labelFilter}
                  </Badge>
                )}
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-4">
          <div className="mb-3 text-sm text-gray-500">
            找到 {filteredQuestions.length} 道题目
          </div>
          <div className="space-y-3">
            {filteredQuestions.length === 0 ? (
              <div className="text-center text-gray-400 py-12">
                <Search className="size-12 mx-auto mb-2" />
                <p>未找到匹配的题目</p>
                <p className="text-sm">尝试调整搜索条件</p>
              </div>
            ) : (
              filteredQuestions.map(question => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  onView={onViewQuestion}
                  onAdd={onAddToQueue}
                  showAddButton={true}
                />
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

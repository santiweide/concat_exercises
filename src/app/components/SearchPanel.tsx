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
  const [sectionFilter, setSectionFilter] = useState<string>('all');
  const [subsectionFilter, setSubsectionFilter] = useState<string>('all');
  const [labelFilter, setLabelFilter] = useState<string>('all');

  // Section options
  const sectionOptions = [
    '第一部分 知识运用',
    '第二部分 阅读理解',
    '第三部分 书面表达',
  ];

  const subsectionOptions = ['第一节', '第二节'];

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

      // Section filter
      if (sectionFilter !== 'all' && question.section !== sectionFilter) {
        return false;
      }

      // Subsection filter
      if (subsectionFilter !== 'all' && question.subsection !== subsectionFilter) {
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
  }, [questions, searchQuery, yearFilter, sectionFilter, subsectionFilter, labelFilter]);

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
            <div className="flex flex-wrap gap-2">
              <Select value={yearFilter} onValueChange={setYearFilter}>
                <SelectTrigger className="w-[120px]">
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

              <Select value={sectionFilter} onValueChange={setSectionFilter}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="第几部分" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有部分</SelectItem>
                  {sectionOptions.map(section => (
                    <SelectItem key={section} value={section}>
                      {section}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={subsectionFilter} onValueChange={setSubsectionFilter}>
                <SelectTrigger className="w-[100px]">
                  <SelectValue placeholder="第几节" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有节</SelectItem>
                  {subsectionOptions.map(subsection => (
                    <SelectItem key={subsection} value={subsection}>
                      {subsection}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={labelFilter} onValueChange={setLabelFilter}>
                <SelectTrigger className="w-[120px]">
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
            {(searchQuery || yearFilter !== 'all' || sectionFilter !== 'all' || subsectionFilter !== 'all' || labelFilter !== 'all') && (
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
                {sectionFilter !== 'all' && (
                  <Badge variant="outline">
                    {sectionFilter}
                  </Badge>
                )}
                {subsectionFilter !== 'all' && (
                  <Badge variant="outline">
                    {subsectionFilter}
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
                {questions.length === 0 ? (
                  <>
                    <p className="text-lg font-medium mb-1">空空如也</p>
                    <p className="text-sm">题库中暂无题目</p>
                  </>
                ) : (
                  <>
                    <p>未找到匹配的题目</p>
                    <p className="text-sm">尝试调整搜索条件</p>
                  </>
                )}
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

import React from 'react';
import { ReadingQuestion } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { CheckCircle2, Circle, AlertCircle } from 'lucide-react';

// 试卷配置
export const EXAM_PAPER_CONFIG = {
  sections: [
    {
      name: '第一部分 知识运用',
      subsections: [
        { name: '第一节', maxQuestions: 1, description: '完形填空' },
        { name: '第二节', maxQuestions: 3, description: '语法填空A/B/C' }
      ]
    },
    {
      name: '第二部分 阅读理解',
      subsections: [
        { name: '第一节', maxQuestions: 4, description: '阅读理解A-D' },
        { name: '第二节', maxQuestions: 1, description: '七选五' }
      ]
    },
    {
      name: '第三部分 书面表达',
      subsections: [
        { name: '第一节', maxQuestions: 1, description: '应用文写作' },
        { name: '第二节', maxQuestions: 1, description: '读后续写/概要写作' }
      ]
    }
  ]
};

interface ExamProgressDashboardProps {
  questions: ReadingQuestion[];
}

interface SectionProgress {
  section: string;
  subsection: string;
  current: number;
  max: number;
  description?: string;
  status: 'empty' | 'partial' | 'complete' | 'exceeded';
}

export function ExamProgressDashboard({ questions }: ExamProgressDashboardProps) {
  // 计算每个小节的进度
  const calculateProgress = (): SectionProgress[] => {
    const progress: SectionProgress[] = [];
    
    EXAM_PAPER_CONFIG.sections.forEach((section) => {
      section.subsections.forEach((subsection) => {
        // 统计该小节的题目数量
        const count = questions.filter(
          (q) => q.section === section.name && q.subsection === subsection.name
        ).length;
        
        let status: SectionProgress['status'] = 'empty';
        if (count === 0) {
          status = 'empty';
        } else if (count < subsection.maxQuestions) {
          status = 'partial';
        } else if (count === subsection.maxQuestions) {
          status = 'complete';
        } else {
          status = 'exceeded';
        }
        
        progress.push({
          section: section.name,
          subsection: subsection.name,
          current: count,
          max: subsection.maxQuestions,
          description: subsection.description,
          status
        });
      });
    });
    
    return progress;
  };

  const progressData = calculateProgress();
  const totalCurrent = progressData.reduce((sum, item) => sum + item.current, 0);
  const totalMax = progressData.reduce((sum, item) => sum + item.max, 0);
  const overallProgress = totalMax > 0 ? (totalCurrent / totalMax) * 100 : 0;
  const hasExceeded = progressData.some((item) => item.status === 'exceeded');

  const getStatusIcon = (status: SectionProgress['status']) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'partial':
        return <Circle className="h-5 w-5 text-blue-500" />;
      case 'exceeded':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-300" />;
    }
  };

  const getStatusBadge = (status: SectionProgress['status']) => {
    switch (status) {
      case 'complete':
        return <Badge variant="default" className="bg-green-500">完成</Badge>;
      case 'partial':
        return <Badge variant="secondary">进行中</Badge>;
      case 'exceeded':
        return <Badge variant="destructive">超额</Badge>;
      default:
        return <Badge variant="outline">未开始</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>组卷进度</CardTitle>
          <Badge variant={hasExceeded ? 'destructive' : overallProgress === 100 ? 'default' : 'secondary'}>
            {totalCurrent} / {totalMax} 题
          </Badge>
        </div>
        <Progress value={Math.min(overallProgress, 100)} className="mt-2" />
        <p className="text-sm text-muted-foreground mt-2">
          整体进度: {Math.round(overallProgress)}%
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {EXAM_PAPER_CONFIG.sections.map((section, sectionIdx) => (
            <div key={sectionIdx} className="space-y-2">
              <h3 className="font-semibold text-sm text-primary">{section.name}</h3>
              <div className="space-y-2 pl-4">
                {section.subsections.map((subsection, subsectionIdx) => {
                  const progressItem = progressData.find(
                    (item) => item.section === section.name && item.subsection === subsection.name
                  );
                  
                  if (!progressItem) return null;
                  
                  return (
                    <div
                      key={subsectionIdx}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        {getStatusIcon(progressItem.status)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{subsection.name}</span>
                            {subsection.description && (
                              <span className="text-xs text-muted-foreground">
                                ({subsection.description})
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <Progress
                              value={Math.min((progressItem.current / progressItem.max) * 100, 100)}
                              className="h-1.5 flex-1 max-w-[120px]"
                            />
                            <span className="text-xs text-muted-foreground">
                              {progressItem.current} / {progressItem.max}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="ml-3">
                        {getStatusBadge(progressItem.status)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        
        {hasExceeded && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-red-900">警告：部分题目超额</p>
                <p className="text-red-700 mt-1">
                  某些小节的题目数量已超过配置上限，请调整题目分布。
                </p>
              </div>
            </div>
          </div>
        )}
        
        {overallProgress === 100 && !hasExceeded && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-green-900">组卷完成！</p>
                <p className="text-green-700 mt-1">
                  所有题目已按照要求配置完成，可以导出试卷。
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// 验证函数：检查是否可以添加题目
export function canAddQuestion(
  questions: ReadingQuestion[],
  newQuestion: ReadingQuestion
): { canAdd: boolean; reason?: string } {
  if (!newQuestion.section || !newQuestion.subsection) {
    return { canAdd: true }; // 如果没有section信息，允许添加
  }
  
  // 查找对应的配置
  let maxQuestions = 0;
  for (const section of EXAM_PAPER_CONFIG.sections) {
    if (section.name === newQuestion.section) {
      for (const subsection of section.subsections) {
        if (subsection.name === newQuestion.subsection) {
          maxQuestions = subsection.maxQuestions;
          break;
        }
      }
      break;
    }
  }
  
  if (maxQuestions === 0) {
    return { canAdd: true }; // 找不到配置，允许添加
  }
  
  // 统计当前该小节的题目数量
  const currentCount = questions.filter(
    (q) => q.section === newQuestion.section && q.subsection === newQuestion.subsection
  ).length;
  
  if (currentCount >= maxQuestions) {
    return {
      canAdd: false,
      reason: `${newQuestion.section} - ${newQuestion.subsection} 已达到上限（${maxQuestions}题）`
    };
  }
  
  return { canAdd: true };
}

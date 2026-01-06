export interface ReadingQuestion {
  id: string;
  title: string; // 来源题目
  year: number;
  questionNumber: string; // 阅读题编号
  articleContent: string; // 文章内容
  questionContent: string; // 题目和选项
  labels: string[]; // 标签
}

export interface Queue {
  id: string;
  name: string;
  questions: ReadingQuestion[];
  frozen: boolean;
  owner: string;
  collaborators: string[];
}

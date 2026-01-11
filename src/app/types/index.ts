export interface QuestionAnswer {
  number: number | string; // 题号，如 21, 22, 23 或 "40"
  answer: string; // 答案，A/B/C/D 或填空答案文字
}

export interface ReadingQuestion {
  id: string;
  title: string; // 来源题目
  year: number;
  section?: string; // 第一部分 知识运用, 第二部分 阅读理解, 第三部分 书面表达
  subsection?: string; // 第一节, 第二节
  questionNumber: string; // 阅读题编号（A/B/C/D）、完形填空、语法填空、七选五、阅读表达、作文
  articleContent: string; // 文章内容（LaTeX格式）
  questionContent: string; // 题目和选项（LaTeX格式）
  labels: string[]; // 标签
  answers?: QuestionAnswer[]; // 答案列表
  subQuestionCount?: number; // 小题数量
}

export interface Queue {
  id: string;
  name: string;
  questions: ReadingQuestion[];
  frozen: boolean;
  owner: string;
  collaborators: string[];
}

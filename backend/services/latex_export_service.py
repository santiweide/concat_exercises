"""
LaTeX Export Service for generating exam papers from queue data.
"""
import structlog
from typing import Dict, List
from models import QueueDetail, ReadingQuestion

logger = structlog.get_logger()


class LatexExportService:
    """Service for exporting queue data to LaTeX format."""
    
    # LaTeX模板头部
    LATEX_HEADER = r"""\documentclass[11pt, a4paper]{article}

%--- 宏包引用 ---
\usepackage[UTF8]{ctex}          % 处理中文
\usepackage{geometry}            % 页面设置
\usepackage{fontspec}            % 字体设置
\usepackage{titlesec}            % 标题格式
\usepackage{enumitem}            % 列表格式
\usepackage{multicol}            % 多栏排版
\usepackage{fancyhdr}            % 页眉页脚
\usepackage{amsmath}             % 数学公式（备用）
\usepackage{ulem}                % 下划线支持
\usepackage[UTF8, fontset=windows]{ctex}

%--- 页面设置 ---
\geometry{left=2.0cm, right=2.0cm, top=2.5cm, bottom=2.5cm}
\setmainfont{Times New Roman}    % 英文主体字体

%--- 自定义命令 ---
\newcommand{\myblank}[1][1.5cm]{\underline{\makebox[#1]{}}} % 填空下划线
\newcommand{\clozeblank}[1]{\textbf{\underline{ #1 }}}      % 完形填空题号
\newcommand{\option}[4]{         % 选择题选项格式化（自动四栏）
    \begin{enumerate}[label=\Alph{*}., itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
        \begin{multicols}{4}
            \item #1 \item #2 \item #3 \item #4
        \end{multicols}
    \end{enumerate}
}
\newcommand{\optiontwo}[4]{      % 选择题选项格式化（自动两栏）
    \begin{enumerate}[label=\Alph{*}., itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
        \begin{multicols}{2}
            \item #1 \item #2 \item #3 \item #4
        \end{multicols}
    \end{enumerate}
}
\newcommand{\optionone}[4]{      % 选择题选项格式化（单栏）
    \begin{enumerate}[label=\Alph{*}., itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
        \item #1 
        \item #2 
        \item #3 
        \item #4
    \end{enumerate}
}

%--- 标题格式设置 ---
\titleformat{\section}{\large\bfseries\heiti}{}{0em}{}
\titleformat{\subsection}{\normalsize\bfseries\heiti}{}{0em}{}

%--- 页眉页脚 ---
\pagestyle{plain} % 简单页码

\begin{document}
"""

    # LaTeX模板尾部
    LATEX_FOOTER = r"""
\end{document}
"""

    def __init__(self):
        """Initialize the LaTeX export service."""
        pass

    def _escape_latex(self, text: str) -> str:
        """
        Escape special LaTeX characters in text.
        Note: Since content might already contain LaTeX commands, we need to be careful.
        """
        # 如果文本已经包含LaTeX命令，可能不需要转义
        # 这里简单处理，实际使用时可能需要更复杂的逻辑
        if not text:
            return ""
        
        # 只转义确实需要转义的字符，不影响已有的LaTeX命令
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        
        # 如果文本看起来已经是LaTeX格式（包含反斜杠命令），则不转义
        if '\\' in text or text.strip().startswith('\\'):
            return text
            
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        
        return text

    def _generate_exam_header(self, queue_name: str, year: int = 2025, month: int = 3) -> str:
        """Generate exam paper header section."""
        header = r"""
%--- 试卷抬头 ---
\begin{center}
    {\Large \textbf{""" + self._escape_latex(queue_name) + r"""}} \\[0.5cm]
    {\Large \textbf{高三英语试卷}} \hfill \textbf{""" + f"{year}. {month}" + r"""} \\[0.5cm]
    （考试时间 90 分钟 \quad 满分 100 分）
\end{center}

\noindent \textbf{注意事项：}本试卷共 10 页。考生务必在答题卡指定区域作答，在试卷上作答无效。

\hrulefill

"""
        return header

    def _group_questions_by_section(self, questions: List[ReadingQuestion]) -> Dict[str, Dict[str, List[ReadingQuestion]]]:
        """
        Group questions by section and subsection.
        Returns: {section: {subsection: [questions]}}
        """
        grouped = {}
        
        for question in questions:
            section = question.section or "未分类"
            subsection = question.subsection or "默认"
            
            if section not in grouped:
                grouped[section] = {}
            if subsection not in grouped[section]:
                grouped[section][subsection] = []
            
            grouped[section][subsection].append(question)
        
        return grouped

    def _generate_section_content(self, questions: List[ReadingQuestion]) -> str:
        """Generate content for a list of questions."""
        content = ""
        
        for question in questions:
            # 添加文章内容
            if question.articleContent:
                content += "\n" + question.articleContent + "\n\n"
            
            # 添加题目内容
            if question.questionContent:
                content += question.questionContent + "\n\n"
            
            content += r"\vspace{0.5cm}" + "\n\n"
        
        return content

    def export_queue_to_latex(self, queue_detail: QueueDetail) -> str:
        """
        Export a queue to LaTeX format.
        
        Args:
            queue_detail: QueueDetail object containing queue info and questions
            
        Returns:
            LaTeX formatted string
        """
        try:
            logger.info("Exporting queue to LaTeX", queue_id=queue_detail.queue.id)
            
            # 开始构建LaTeX文档
            latex_content = self.LATEX_HEADER
            
            # 添加试卷抬头
            latex_content += self._generate_exam_header(queue_detail.queue.name)
            
            # 按section和subsection分组题目
            grouped_questions = self._group_questions_by_section(queue_detail.questions)
            
            # 定义固定的section顺序
            section_order = [
                '第一部分 知识运用',
                '第二部分 阅读理解',
                '第三部分 书面表达'
            ]
            
            # 按照固定顺序生成各部分内容
            for section_name in section_order:
                if section_name not in grouped_questions:
                    continue
                    
                subsections = grouped_questions[section_name]
                
                # 添加section标题
                latex_content += f"\n%{'='*60}\n"
                latex_content += f"% {section_name}\n"
                latex_content += f"%{'='*60}\n"
                latex_content += f"\\section*{{{section_name}}}\n\n"
                
                # 定义subsection顺序
                subsection_order = ['第一节', '第二节', '默认']
                
                for subsection_name in subsection_order:
                    if subsection_name not in subsections:
                        continue
                        
                    questions = subsections[subsection_name]
                    
                    # 添加subsection标题
                    if subsection_name != "默认":
                        latex_content += f"\\subsection*{{{subsection_name}}}\n"
                    
                    # 添加题目内容
                    latex_content += self._generate_section_content(questions)
                
                # 处理其他未在固定顺序中的subsection
                for subsection_name, questions in subsections.items():
                    if subsection_name not in subsection_order:
                        if subsection_name != "默认":
                            latex_content += f"\\subsection*{{{subsection_name}}}\n"
                        latex_content += self._generate_section_content(questions)
            
            # 处理不在固定section顺序中的其他section
            for section_name, subsections in grouped_questions.items():
                if section_name not in section_order:
                    latex_content += f"\n%{'='*60}\n"
                    latex_content += f"% {section_name}\n"
                    latex_content += f"%{'='*60}\n"
                    latex_content += f"\\section*{{{section_name}}}\n\n"
                    
                    for subsection_name, questions in subsections.items():
                        if subsection_name != "默认":
                            latex_content += f"\\subsection*{{{subsection_name}}}\n"
                        latex_content += self._generate_section_content(questions)
            
            # 添加文档尾部
            latex_content += self.LATEX_FOOTER
            
            logger.info("LaTeX export completed successfully", 
                       queue_id=queue_detail.queue.id,
                       questions_count=len(queue_detail.questions))
            
            return latex_content
            
        except Exception as e:
            logger.error("Error exporting queue to LaTeX", 
                        queue_id=queue_detail.queue.id,
                        error=str(e))
            raise


# 全局服务实例
latex_export_service = LatexExportService()

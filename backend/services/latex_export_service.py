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
\usepackage{geometry}            % 页面设置
\usepackage{fontspec}            % 字体设置
\usepackage{titlesec}            % 标题格式
\usepackage{enumitem}            % 列表格式
\usepackage{multicol}            % 多栏排版
\usepackage{fancyhdr}            % 页眉页脚
\usepackage{amsmath}             % 数学公式（备用）
\usepackage{ulem}                % 下划线支持
\usepackage{pifont}              % 带圈数字支持
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

    def _process_text_formatting(self, text: str) -> str:
        """
        Process text formatting including:
        1. Replace \\n and \n with empty space
        2. Replace circled numbers ①②③④⑤ with \ding{172-176}
        """
        if not text:
            return text
        
        # Replace \\n and \n with empty space
        text = text.replace('\\n', ' ')
        text = text.replace('\n', ' ')
        
        # Replace circled numbers with \ding commands
        circled_numbers = {
            '①': r'\ding{172}',
            '②': r'\ding{173}',
            '③': r'\ding{174}',
            '④': r'\ding{175}',
            '⑤': r'\ding{176}'
        }
        
        for circled, ding_cmd in circled_numbers.items():
            text = text.replace(circled, ding_cmd)
        
        return text
    
    def _add_par_after_questions(self, text: str) -> str:
        """
        Add \\par after each question ending (after options or question content).
        This ensures proper spacing between individual questions.
        
        Example:
            \\textbf{1.} What...? \\option{...}{...}{...}{...}
            \\textbf{2.} Where...? \\option{...}{...}{...}{...}
            
            becomes:
            
            \\textbf{1.} What...? \\option{...}{...}{...}{...}\\par
            \\textbf{2.} Where...? \\option{...}{...}{...}{...}\\par
        """
        import re
        
        if not text:
            return text
        
        # 匹配选项命令结束位置（4个大括号闭合后）
        # 在 \option{}{}{}{} 或 \optiontwo{}{}{}{} 或 \optionone{}{}{}{} 后添加 \par
        def add_par_after_option(match):
            return match.group(0) + r'\par'
        
        # 匹配选项命令并在其后添加 \par
        pattern = r'\\(?:option|optiontwo|optionone)\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}'
        text = re.sub(pattern, add_par_after_option, text)
        
        return text
    
    def _clean_option_prefixes(self, text: str) -> str:
        """
        Remove A. B. C. D. prefixes from option content to avoid duplication.
        Since \\option{}, \\optiontwo{}, \\optionone{} already add A. B. C. D. labels,
        we need to remove them from the content.
        
        Examples:
            \\option{A. apple}{B. banana}{C. orange}{D. grape}
            → \\option{apple}{banana}{orange}{grape}
            
            \\optiontwo{A. To protect}{B. To promote}{C. To study}{D. To develop}
            → \\optiontwo{To protect}{To promote}{To study}{To develop}
        """
        if not text:
            return text
        
        import re
        
        def clean_single_option(match):
            """清理单个 \option{}{}{}{} 或类似命令"""
            full_match = match.group(0)
            command = match.group(1)  # option, optiontwo, 或 optionone
            
            # 使用简单的方法：找到命令后面的4个 {...} 块
            # 然后清理每个块内开头的 A. B. C. D. 等前缀
            result = f"\\{command}"
            
            # 从命令后面开始查找大括号
            pos = len(f"\\{command}")
            i = pos
            options_found = 0
            
            while i < len(full_match) and options_found < 4:
                if full_match[i] == '{':
                    # 找到匹配的右大括号
                    brace_count = 1
                    j = i + 1
                    while j < len(full_match) and brace_count > 0:
                        if full_match[j] == '{':
                            brace_count += 1
                        elif full_match[j] == '}':
                            brace_count -= 1
                        j += 1
                    
                    # 提取选项内容
                    option_content = full_match[i+1:j-1]
                    
                    # 清理 A. B. C. D. E. F. G. 前缀
                    cleaned_content = re.sub(r'^\s*[A-G]\.\s*', '', option_content)
                    
                    # 添加到结果
                    result += '{' + cleaned_content + '}'
                    
                    options_found += 1
                    i = j
                else:
                    i += 1
            
            return result
        
        # 处理三种选项命令，使用非贪婪匹配
        # 匹配 \option{...}{...}{...}{...}
        pattern = r'\\(option|optiontwo|optionone)\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}'
        text = re.sub(pattern, clean_single_option, text)
        
        return text

    def _generate_section_content(self, questions: List[ReadingQuestion], start_number: int = 1) -> tuple[str, int]:
        """
        Generate content for a list of questions with automatic numbering.
        
        Args:
            questions: List of questions to generate content for
            start_number: Starting question number
            
        Returns:
            Tuple of (generated_content, next_number)
            - generated_content: LaTeX formatted content
            - next_number: The next available question number after this section
        """
        import re
        
        content = ""
        current_number = start_number
        
        for question in questions:
            # 添加文章内容
            if question.articleContent:
                article_text = self._process_text_formatting(question.articleContent)
                content += "\n" + article_text + "\n\n"
            
            # 添加题目内容，自动重新编号
            if question.questionContent:
                question_text = question.questionContent
                
                # 方案1: 如果使用了 subQuestions 结构（未来优化）
                if hasattr(question, 'subQuestions') and question.subQuestions:
                    for sub_q in question.subQuestions:
                        if sub_q.get('content'):
                            content += f"\\textbf{{{current_number}.}} {sub_q['content']}\n"
                        if sub_q.get('options'):
                            content += sub_q['options'] + "\n"
                        content += "\\par\n"
                        current_number += 1
                else:
                    # 方案2: 当前格式 - 替换现有题号
                    # 匹配并替换题号格式: \textbf{21.} 或 \textbf{1.} 等
                    def replace_number(match):
                        nonlocal current_number
                        replacement = f"\\textbf{{{current_number}.}}"
                        current_number += 1
                        return replacement
                    
                    # 1. 替换所有 \textbf{数字.} 格式的题号
                    question_text = re.sub(
                        r'\\textbf\{(\d+)\.\}',
                        replace_number,
                        question_text
                    )
                    
                    # 2. 清理选项内容中的 A. B. C. D. 前缀（避免与LaTeX命令重复）
                    question_text = self._clean_option_prefixes(question_text)
                    
                    # 3. 处理文本格式（换行符和带圈数字）
                    question_text = self._process_text_formatting(question_text)
                    
                    # 4. 在每道题后添加 \par（在 \textbf{数字.} ... 内容结束后）
                    # 将题目按 \textbf{数字.} 分割，然后在每个部分后添加 \par
                    question_text = self._add_par_after_questions(question_text)
                    
                    # 如果没有找到题号，但有 subQuestionCount，则根据数量推进编号
                    if current_number == start_number and question.subQuestionCount > 0:
                        current_number += question.subQuestionCount
                    
                    content += question_text + "\n\n"
            elif question.subQuestionCount > 0:
                # 如果没有 questionContent 但有 subQuestionCount（如语法填空只有文章）
                # 编号仍需推进
                current_number += question.subQuestionCount
            
            content += r"\vspace{0.5cm}" + "\n\n"
        
        return content, current_number

    def export_queue_to_latex(self, queue_detail: QueueDetail) -> str:
        """
        Export a queue to LaTeX format with automatic question numbering.
        
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
            
            # 定义每个部分的起始题号
            section_start_numbers = {
                '第一部分 知识运用': 1,      # 完形填空从1开始，语法填空继续
                '第二部分 阅读理解': None,    # 继续上一部分的编号
                '第三部分 书面表达': None     # 继续上一部分的编号
            }
            
            # 追踪当前题号
            current_question_number = 1
            
            # 按照固定顺序生成各部分内容
            for section_name in section_order:
                if section_name not in grouped_questions:
                    continue
                
                # 设置该部分的起始题号
                if section_start_numbers.get(section_name) is not None:
                    current_question_number = section_start_numbers[section_name]
                    
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
                    
                    # 添加题目内容，并更新题号
                    section_content, current_question_number = self._generate_section_content(
                        questions, 
                        current_question_number
                    )
                    latex_content += section_content
                
                # 处理其他未在固定顺序中的subsection
                for subsection_name, questions in subsections.items():
                    if subsection_name not in subsection_order:
                        if subsection_name != "默认":
                            latex_content += f"\\subsection*{{{subsection_name}}}\n"
                        section_content, current_question_number = self._generate_section_content(
                            questions,
                            current_question_number
                        )
                        latex_content += section_content
            
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
                        section_content, current_question_number = self._generate_section_content(
                            questions,
                            current_question_number
                        )
                        latex_content += section_content
            
            # 添加文档尾部
            latex_content += self.LATEX_FOOTER
            
            logger.info("LaTeX export completed successfully", 
                       queue_id=queue_detail.queue.id,
                       questions_count=len(queue_detail.questions),
                       total_sub_questions=current_question_number - 1)
            
            return latex_content
            
        except Exception as e:
            logger.error("Error exporting queue to LaTeX", 
                        queue_id=queue_detail.queue.id,
                        error=str(e))
            raise


# 全局服务实例
latex_export_service = LatexExportService()

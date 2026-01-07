#!/usr/bin/env python3
"""Script to update the extraction prompt in pdf_import_service.py"""

import re

def main():
    with open('pdf_import_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the _get_extraction_prompt method
    old_pattern = r'def _get_extraction_prompt\(self\) -> str:.*?"""你是一个专业的高考英语试卷分析助手。请仔细分析试卷内容，提取其中的阅读理解部分。.*?"""'
    
    new_method = '''def _get_extraction_prompt(self) -> str:
        """Get the prompt for extracting reading questions and answers."""
        return """你是一个专业的高考英语试卷分析助手。请仔细分析试卷内容，提取其中的阅读理解部分及其答案。

请按照以下JSON格式返回结果：

```json
{
    "title": "试卷标题（如：2023年全国卷I）",
    "year": 2023,
    "questions": [
        {
            "questionNumber": "A",
            "articleContent": "阅读文章的完整原文内容...",
            "questionContent": "题目和选项的完整内容，包括所有小题...",
            "labels": ["主题标签1", "主题标签2", "主题标签3"],
            "answers": [
                {"number": 21, "answer": "B"},
                {"number": 22, "answer": "A"},
                {"number": 23, "answer": "D"}
            ]
        }
    ]
}
```

要求：
1. 识别试卷来源和年份（从试卷标题或页眉提取）
2. 提取所有阅读理解题目（通常在大标题"第二部分 阅读理解"下的第一节，通常标记为A、B、C、D四篇）
3. articleContent：完整提取每篇阅读的文章原文
4. questionContent：提取该篇文章对应的所有题目和选项，通常题目序号分别为21-23，24-27，28-31，32-35。注意每个编号表示一个小题，而不是每个选项代表一个小题（因为是选择题）。
5. labels：根据文章内容生成3-5个语义标签，描述文章的主题、体裁、话题等
   - 主题标签示例：科技、环境、文化、教育、健康、社会、历史、艺术、体育、经济
   - 体裁标签示例：记叙文、说明文、议论文、新闻报道、人物传记
   - 话题标签示例：人工智能、气候变化、传统文化、青少年成长等
6. answers：从"英语参考答案"部分的"第二部分 阅读理解"中提取每个小题的答案
   - number：小题题号（如21, 22, 23等整数）
   - answer：该小题的正确答案（A、B、C或D）
   - 如果找不到答案部分，answers数组可以为空

请只返回JSON格式的结果，不要包含其他文字说明。如果无法识别为英语试卷，返回：
```json
{"error": "无法识别为英语试卷"}
```
\"\"\""""'''
    
    new_content = re.sub(old_pattern, new_method, content, flags=re.DOTALL)
    
    if new_content != content:
        with open('pdf_import_service.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated prompt!")
    else:
        print("Pattern not found, trying alternative approach...")
        # Try line-by-line approach
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if 'def _get_extraction_prompt(self)' in line:
                start_idx = i
            if start_idx is not None and '{"error": "无法识别为英语试卷"}' in line:
                # Find the closing """
                for j in range(i, min(i+5, len(lines))):
                    if '"""' in lines[j]:
                        end_idx = j
                        break
                if end_idx:
                    break
        
        if start_idx is not None and end_idx is not None:
            print(f"Found method from line {start_idx} to {end_idx}")
            # Replace lines
            new_lines = lines[:start_idx] + [new_method] + lines[end_idx+1:]
            with open('pdf_import_service.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print("Updated using line-by-line approach!")
        else:
            print(f"Could not locate method. start={start_idx}, end={end_idx}")

if __name__ == '__main__':
    main()

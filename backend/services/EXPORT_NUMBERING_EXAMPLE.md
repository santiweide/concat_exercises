# 导出自动重新编号功能说明

## 功能概述

导出时会自动重新编号所有题目，不依赖原试卷的题号。支持灵活调整题目顺序后重新编号。

## 工作原理

### 1. 自动编号逻辑

```python
def _generate_section_content(questions, start_number=1):
    current_number = start_number
    
    for question in questions:
        # 输出文章内容
        output(question.articleContent)
        
        # 自动替换题号
        # 原文: \textbf{21.} What is...
        # 替换为: \textbf{1.} What is...  (如果 start_number=1)
        question_text = re.sub(
            r'\\textbf\{(\d+)\.\}',  # 匹配 \textbf{任意数字.}
            lambda m: f'\\textbf{{{current_number}.}}',  # 替换为当前编号
            question.questionContent
        )
        
        current_number += 1  # 每个小题编号递增
    
    return content, current_number  # 返回下一个可用编号
```

### 2. 跨部分连续编号

```python
# 第一部分 知识运用
current_num = 1
content1, current_num = generate_section(完形填空, start=current_num)  
# 完形填空 1-10 题，current_num 变为 11

content2, current_num = generate_section(语法填空, start=current_num)
# 语法填空 11-20 题，current_num 变为 21

# 第二部分 阅读理解
content3, current_num = generate_section(阅读A, start=current_num)
# 阅读A 21-23 题，current_num 变为 24

content4, current_num = generate_section(阅读B, start=current_num)
# 阅读B 24-27 题，current_num 变为 28
```

## 使用示例

### 场景 1：原顺序导出

**队列中的题目：**
```
1. 完形填空 (原试卷 1-10 题，共10小题)
2. 语法填空A (原试卷 11-13 题，共3小题)
3. 阅读A (原试卷 21-23 题，共3小题)
4. 阅读B (原试卷 24-27 题，共4小题)
```

**导出结果：**
```latex
% 第一部分 知识运用
\section*{第一部分 知识运用}
\subsection*{第一节}
...完形填空文章...
\textbf{1.} ...  % 原来是 1
\option{A}{B}{C}{D}
\textbf{2.} ...  % 原来是 2
\option{A}{B}{C}{D}
...
\textbf{10.} ... % 原来是 10

\subsection*{第二节}
...语法填空文章...
% 题号从 11 开始继续
\textbf{11.} ... % 原来是 11
\textbf{12.} ... % 原来是 12
\textbf{13.} ... % 原来是 13

% 第二部分 阅读理解
\section*{第二部分 阅读理解}
\subsection*{第一节}
...阅读A文章...
\textbf{14.} ... % 原来是 21，现在变成 14
\option{A}{B}{C}{D}
\textbf{15.} ... % 原来是 22，现在变成 15
\textbf{16.} ... % 原来是 23，现在变成 16

...阅读B文章...
\textbf{17.} ... % 原来是 24，现在变成 17
\textbf{18.} ... % 原来是 25，现在变成 18
\textbf{19.} ... % 原来是 26，现在变成 19
\textbf{20.} ... % 原来是 27，现在变成 20
```

### 场景 2：调整顺序后导出

**队列中的题目（用户重新排序）：**
```
1. 阅读A (原试卷 21-23 题，共3小题)
2. 阅读B (原试卷 24-27 题，共4小题)
3. 完形填空 (原试卷 1-10 题，共10小题)
4. 语法填空A (原试卷 11-13 题，共3小题)
```

**导出结果：**
```latex
% 第一部分 知识运用 (空，因为完形填空被移到后面了)

% 第二部分 阅读理解
\section*{第二部分 阅读理解}
\subsection*{第一节}
...阅读A文章...
\textbf{1.} ...  % 原来是 21，现在变成 1（因为它在队列第一位）
\textbf{2.} ...  % 原来是 22，现在变成 2
\textbf{3.} ...  % 原来是 23，现在变成 3

...阅读B文章...
\textbf{4.} ...  % 原来是 24，现在变成 4
\textbf{5.} ...  % 原来是 25，现在变成 5
\textbf{6.} ...  % 原来是 26，现在变成 6
\textbf{7.} ...  % 原来是 27，现在变成 7

% 第一部分 知识运用（现在才出现）
\section*{第一部分 知识运用}
\subsection*{第一节}
...完形填空文章...
\textbf{8.} ...  % 原来是 1，现在变成 8
\textbf{9.} ...  % 原来是 2，现在变成 9
...
\textbf{17.} ... % 原来是 10，现在变成 17

\subsection*{第二节}
...语法填空文章...
\textbf{18.} ... % 原来是 11，现在变成 18
\textbf{19.} ... % 原来是 12，现在变成 19
\textbf{20.} ... % 原来是 13，现在变成 20
```

### 场景 3：只选择部分题目导出

**队列中的题目：**
```
1. 阅读A (原试卷 21-23 题，共3小题)
2. 阅读C (原试卷 28-31 题，共4小题)
```

**导出结果：**
```latex
% 第二部分 阅读理解
\section*{第二部分 阅读理解}
\subsection*{第一节}
...阅读A文章...
\textbf{1.} ...  % 原来是 21，现在是 1
\textbf{2.} ...  % 原来是 22，现在是 2
\textbf{3.} ...  % 原来是 23，现在是 3

...阅读C文章...
\textbf{4.} ...  % 原来是 28，现在是 4
\textbf{5.} ...  % 原来是 29，现在是 5
\textbf{6.} ...  % 原来是 30，现在是 6
\textbf{7.} ...  % 原来是 31，现在是 7
```

## 关键特性

### ✅ 已实现功能

1. **自动题号替换**
   - 使用正则表达式匹配 `\textbf{数字.}` 格式
   - 替换为按顺序递增的新题号
   - 支持跨部分连续编号

2. **基于 subQuestionCount 的编号**
   - 即使题目内容中没有明确题号
   - 也能根据 `subQuestionCount` 正确推进编号

3. **灵活的部分起始编号**
   - 可以为每个大部分设置不同的起始题号
   - 默认从1开始连续编号

### 🔄 兼容性

支持两种格式：

**格式1：包含题号（当前格式）**
```json
{
    "questionContent": "\\textbf{21.} What is the main idea?\\n\\option{A}{B}{C}{D}",
    "subQuestionCount": 1
}
```
导出时会替换 `21` 为实际编号。

**格式2：不包含题号（推荐未来格式）**
```json
{
    "questionContent": "What is the main idea?\\n\\option{A}{B}{C}{D}",
    "subQuestionCount": 1
}
```
导出时会自动添加题号 `\textbf{1.}`。

### 📊 subQuestionCount 的重要性

`subQuestionCount` 字段非常关键，用于：

1. **正确推进编号**
   ```python
   # 阅读理解A有3个小题
   question.subQuestionCount = 3
   # 处理后，current_number 从 1 变为 4
   ```

2. **处理无题号内容**
   ```python
   # 语法填空只有文章，没有题干
   question.articleContent = "...\\clozeblank{1}...\\clozeblank{2}..."
   question.questionContent = ""  # 空
   question.subQuestionCount = 2  # 但有2个填空
   # 编号仍会从1推进到3
   ```

3. **验证数据完整性**
   ```python
   # 检查实际题号数量是否匹配 subQuestionCount
   actual_count = len(re.findall(r'\\textbf\{\d+\.\}', question.questionContent))
   assert actual_count == question.subQuestionCount
   ```

## 未来优化方向

### 使用 subQuestions 结构

```python
# 当前格式（文本拼接）
{
    "questionContent": "\\textbf{21.} Q1?\\n\\option{A}{B}{C}{D}\\n\\textbf{22.} Q2?\\n\\option{A}{B}{C}{D}",
    "subQuestionCount": 2
}

# 未来格式（结构化）
{
    "subQuestions": [
        {
            "content": "Q1?",
            "options": "\\option{A}{B}{C}{D}",
            "answer": "A"
        },
        {
            "content": "Q2?",
            "options": "\\option{B}{C}{D}{E}",
            "answer": "B"
        }
    ]
}
```

优势：
- 更清晰的数据结构
- 更容易维护和处理
- 题号完全由导出逻辑控制
- 答案与题目一一对应

## 测试建议

### 测试用例

1. ✅ **正常顺序导出**：验证编号从1开始连续
2. ✅ **调整顺序导出**：验证重新排序后编号正确
3. ✅ **跨部分编号**：验证不同section间编号连续
4. ✅ **部分题目导出**：验证只选择部分题目时编号从1开始
5. ✅ **混合格式**：验证有题号和无题号内容都能正确处理
6. ✅ **subQuestionCount**：验证编号推进与 subQuestionCount 一致

### 验证脚本

```python
def test_export_numbering():
    # 创建测试队列
    questions = [
        ReadingQuestion(
            questionContent="\\textbf{21.} Q1\\n\\option{A}{B}{C}{D}",
            subQuestionCount=1
        ),
        ReadingQuestion(
            questionContent="\\textbf{22.} Q2\\n\\option{A}{B}{C}{D}",
            subQuestionCount=1
        ),
    ]
    
    # 导出
    content, next_num = _generate_section_content(questions, start_number=1)
    
    # 验证
    assert "\\textbf{1.}" in content  # 21 被替换为 1
    assert "\\textbf{2.}" in content  # 22 被替换为 2
    assert next_num == 3  # 下一个题号应该是 3
    assert "\\textbf{21.}" not in content  # 原题号不应存在
    assert "\\textbf{22.}" not in content
```

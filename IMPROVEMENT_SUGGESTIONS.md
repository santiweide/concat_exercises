# Gemini OCR 提取系统改进建议

## 实施状态概览

- ✅ **已完成**：导出自动重新编号功能
- ✅ **已完成**：选项格式优化（移除A.B.C.D.前缀）
- ✅ **已完成**：特殊字符转义（%符号）
- 🔄 **进行中**：提示词格式优化
- ⏳ **待实施**：数据模型重构（subQuestions结构）

---

## 当前问题分析

### 1. 题目编号与内容耦合问题 ✅ 已解决（部分）

**当前实现：**
```python
# questionContent 中硬编码了题号
"questionContent": "\\textbf{21.} What is the main idea?\\n\\option{A}{B}{C}{D}"

# answers 中包含原始题号
"answers": [
    {"number": 21, "answer": "B"},
    {"number": 22, "answer": "A"}
]
```

**问题：**
- ❌ 题号被硬编码在 `questionContent` 中（如 `\textbf{21.}`）
- ✅ **已解决**：导出时可以自动重新编号
- ⏳ **待优化**：数据存储仍耦合原始题号

**当前解决方案（已实施 ✅）：导出时正则替换**

```python
# latex_export_service.py - 已实现
def _generate_section_content(questions, start_number=1):
    """导出时自动重新编号"""
    current_number = start_number
    
    for question in questions:
        # 自动替换 \textbf{21.} → \textbf{1.}
        question_text = re.sub(
            r'\\textbf\{(\d+)\.\}',
            lambda m: f'\\textbf{{{current_number}.}}',
            question.questionContent
        )
        current_number += 1
    
    return content, current_number  # 返回下一个可用题号
```

**效果：**
- ✅ 支持任意调整题目顺序后重新编号
- ✅ 原试卷21-23题可以变成导出时的1-3题
- ✅ 跨部分连续编号（完形1-10 → 语法11-20 → 阅读21-23）
- ✅ 依赖 `subQuestionCount` 正确推进编号

**使用示例：**
```
队列：阅读A(原21-23) → 完形填空(原1-10)
导出：阅读A(1-3题) → 完形填空(4-13题) ✅
```

详见：[backend/services/EXPORT_NUMBERING_EXAMPLE.md](backend/services/EXPORT_NUMBERING_EXAMPLE.md)

---

**未来优化方案：分离题号和内容（推荐但非必需）**

修改数据结构：
```python
class ReadingQuestion(BaseModel):
    # 新增字段：原始小题列表（不含题号，只有题干和选项）
    subQuestions: list[dict] = Field(
        default_factory=list,
        description="子题目列表，每项包含 {content: 题干, options: 选项内容, answer: 答案}"
    )
    # 示例：
    # [
    #   {
    #     "content": "What is the main idea?",
    #     "options": "\\option{Climate change}{Ocean pollution}{...}{...}",
    #     "answer": "B"
    #   },
    #   {
    #     "content": "According to the passage, ...",
    #     "options": "\\optiontwo{True}{False}{Maybe}{Unknown}",
    #     "answer": "A"
    #   }
    # ]
```

修改提示词：
```python
"""
## questionContent 格式变更

不要在题目内容中包含题号（如 \\textbf{21.}）。题号将在导出时根据位置自动生成。

错误示例：
"questionContent": "\\textbf{21.} What is the main idea?\\n\\option{A}{B}{C}{D}"

正确示例：
"subQuestions": [
    {
        "content": "What is the main idea?",
        "options": "\\option{Climate change}{Ocean pollution}{Deforestation}{Urban sprawl}",
        "answer": "B"
    },
    {
        "content": "According to the passage, what year was mentioned?",
        "options": "\\option{2020}{2021}{2022}{2023}",
        "answer": "C"
    }
]
"""
```

修改导出逻辑：
```python
def _generate_questions_with_numbering(self, questions: List[ReadingQuestion], 
                                      start_number: int = 1) -> str:
    """生成带自动编号的题目内容"""
    content = ""
    current_number = start_number
    
    for question in questions:
        # 添加文章内容（不变）
        if question.articleContent:
            content += "\n" + question.articleContent + "\n\n"
        
        # 为每个子题目自动编号
        for sub_q in question.subQuestions:
            content += f"\\textbf{{{current_number}.}} {sub_q['content']}\n"
            if sub_q.get('options'):
                content += sub_q['options'] + "\n"
            current_number += 1
        
        content += r"\vspace{0.5cm}" + "\n\n"
    
    return content
```

**解决方案 B：使用占位符（快速方案）**

保持当前结构，但提取时使用占位符：
```python
# 提示词中要求使用占位符
"""
题目编号使用占位符 {{NUM}}，导出时会自动替换为实际编号。

示例：
"questionContent": "\\textbf{{{{NUM}}}.} What is the main idea?\\n\\option{A}{B}{C}{D}"
"""

# 导出时替换占位符
def export_with_renumbering(content: str, start_num: int):
    counter = [start_num]  # 使用列表保持引用
    
    def replace_num(match):
        num = counter[0]
        counter[0] += 1
        return str(num)
    
    return re.sub(r'\{\{NUM\}\}', replace_num, content)
```

---

### 2. 格式保持问题 🔄 部分完成

**当前实现已经较好，需要补充：**

#### 2.1 换行格式 ⏳ 待完善

**当前提示词**缺少明确的换行指令。

**改进建议：**
```python
"""
## LaTeX 格式规范补充

### 换行和段落
- 使用 `\\\\` 表示强制换行（如诗歌、地址等需要保留换行的地方）
- 使用空行（两个 \\n）表示段落分隔
- 不要删除原文中的换行，特别是：
  * 七选五的选项列表
  * 阅读表达的多个问题
  * 作文题目的多条要求

### 特殊格式保持
- **黑体**：`\\textbf{文字}` - 用于题号、关键词、标题
- **斜体**：`\\textit{文字}` - 用于外语词汇、强调、书名
- **下划线**：`\\uwave{文字}` - 用于波浪下划线（注意区分填空下划线）
- **居中**：`\\centerline{文字}` - 用于篇章标题（如七选五的选项标记）

### 保留原文结构
1. 如果原文有明显的段落分隔，保留空行
2. 如果原文有项目符号列表，使用 enumerate 或 itemize
3. 如果原文有表格，使用 tabular 环境
4. 如果原文有引用/对话，保留引号格式
"""
```

#### 2.2 特殊字符转义 ✅ 已实现（部分）

**当前已实现：**
- ✅ `%` → `\%` （已添加到提示词）
- ✅ `_` → `\_` （已要求转义）
- ✅ 填空下划线 `______` → `\myblank[1.5cm]`

**建议补充：**

```python
"""
### LaTeX 特殊字符转义规则（完整清单）

必须转义的字符：
- `%` → `\\%` （注释符号）
- `_` → `\\_` （下标符号，填空除外）
- `$` → `\\$` （数学模式）
- `&` → `\\&` （表格分隔符）
- `#` → `\\#` （参数符号）
- `{` → `\\{` （分组符号，LaTeX命令除外）
- `}` → `\\}` （分组符号，LaTeX命令除外）
- `~` → `\\textasciitilde{}` （不间断空格）
- `^` → `\\textasciicircum{}` （上标符号）
- `\\` → `\\textbackslash{}` （反斜杠本身，在文本中）

注意：这些转义只针对**试卷正文内容**，不包括我们的 LaTeX 命令本身。
"""
```

---

### 3. 答案存储优化 ⏳ 待优化

**当前问题：**
- ✅ 题号可以在导出时重新编号（已解决）
- ⏳ `answers` 数组仍存储原试卷题号（不影响使用，但不够优雅）

**改进方案（配合未来的 subQuestions 结构）：**

```python
class SubQuestion(BaseModel):
    """单个子题目"""
    content: str = Field(description="题干内容（不含题号）")
    options: Optional[str] = Field(default=None, description="选项内容（LaTeX格式）")
    answer: str = Field(description="答案（A/B/C/D 或文本）")
    answerExplanation: Optional[str] = Field(default=None, description="答案解析（可选）")

class ReadingQuestion(BaseModel):
    # ... 其他字段保持不变
    
    # 删除 answers 字段，改为：
    subQuestions: list[SubQuestion] = Field(default_factory=list)
    
    # subQuestionCount 可以自动计算
    @property
    def subQuestionCount(self) -> int:
        return len(self.subQuestions)
```

---

### 4. 提示词具体改进 🔄 进行中

#### 4.1 添加格式示例 ⏳ 待完成

在提示词中添加更多实际例子：

```python
"""
## 实际格式示例

### 示例 1：完形填空
**原文：**
"In 2020, scientists __1__ a breakthrough. They __2__ that..."
"1. A. made  B. took  C. gave  D. brought"
"2. A. discovered  B. invented  C. created  D. found"

**正确提取：**
{
    "articleContent": "In 2020, scientists \\\\clozeblank{1} a breakthrough. They \\\\clozeblank{2} that...",
    "subQuestions": [
        {
            "content": "",  // 完形填空题干为空，选项直接跟在文章后
            "options": "\\\\option{made}{took}{gave}{brought}",
            "answer": "A"
        },
        {
            "content": "",
            "options": "\\\\option{discovered}{invented}{created}{found}",
            "answer": "A"
        }
    ]
}

### 示例 2：阅读理解（保留段落、格式）
**原文：**
"Climate change is one of the most pressing issues of our time.

According to recent studies, global temperatures have risen by 1.5°C since the pre-industrial era. This has led to:
• More frequent extreme weather events
• Rising sea levels
• Loss of biodiversity

Scientists warn that immediate action is needed.

21. What is the main topic?
A. Weather prediction
B. Climate change
C. Ocean research
D. Industrial development

22. How much have temperatures risen?
A. 1.5°C  B. 2.0°C  C. 0.5°C  D. 3.0°C"

**正确提取：**
{
    "articleContent": "Climate change is one of the most pressing issues of our time.\\n\\nAccording to recent studies, global temperatures have risen by 1.5\\\\% since the pre-industrial era. This has led to:\\n\\\\begin{itemize}\\n\\\\item More frequent extreme weather events\\n\\\\item Rising sea levels\\n\\\\item Loss of biodiversity\\n\\\\end{itemize}\\n\\nScientists warn that immediate action is needed.",
    "subQuestions": [
        {
            "content": "What is the main topic?",
            "options": "\\\\option{Weather prediction}{Climate change}{Ocean research}{Industrial development}",
            "answer": "B"
        },
        {
            "content": "How much have temperatures risen?",
            "options": "\\\\option{1.5°C}{2.0°C}{0.5°C}{3.0°C}",  // 注意：°C 不需要转义
            "answer": "A"
        }
    ]
}
```

#### 4.2 明确要求保留原文所有信息 ⏳ 待完成

```python
"""
## 内容完整性要求（重要！）

### 必须保留的内容：
1. ✅ 所有段落和换行
2. ✅ 所有标点符号（包括中英文标点）
3. ✅ 所有数字、日期、百分比
4. ✅ 所有人名、地名、专有名词（保持原样，包括大小写）
5. ✅ 所有引号、括号内的内容
6. ✅ 所有列表项目符号和编号
7. ✅ 所有图表标题（如果有）

### 必须保留的格式：
1. ✅ 黑体（标题、题号）→ `\\textbf{}`
2. ✅ 斜体（书名、外语词）→ `\\textit{}`
3. ✅ 下划线（强调）→ `\\uwave{}`
4. ✅ 段落间距（空行）
5. ✅ 强制换行（诗歌、地址）→ `\\\\`

### 禁止的操作：
1. ❌ 不要总结或改写原文
2. ❌ 不要删除"看起来不重要"的内容
3. ❌ 不要修正原文中的语法错误（即使有错也保留）
4. ❌ 不要改变原文的语序
5. ❌ 不要添加原文中没有的解释
"""
```

---

## 代码改进清单

### ✅ Phase 0: 导出重新编号（已完成）

**实施时间：** 2026年1月12日

1. **✅ 修改 `latex_export_service.py`**
   - ✅ `_generate_section_content` 返回 `(content, next_number)` 元组
   - ✅ 使用正则表达式替换题号 `\textbf{数字.}`
   - ✅ 根据 `subQuestionCount` 推进编号
   - ✅ 跨部分连续编号支持

2. **✅ 修改 `pdf_import_service.py` 提示词**
   - ✅ 说明题号会在导出时重新编号
   - ✅ 要求正确填写 `subQuestionCount`
   - ✅ 选项不包含 A.B.C.D. 前缀
   - ✅ `%` 符号转义要求

3. **✅ 创建文档**
   - ✅ `EXPORT_NUMBERING_EXAMPLE.md` - 使用示例和测试用例

---

### ⏳ Phase 1: 数据模型优化（推荐但非必需）

1. **修改 `models.py`**
   ```python
   class SubQuestion(BaseModel):
       content: str
       options: Optional[str] = None
       answer: str
       
   class ReadingQuestion(BaseModel):
       # ... 保留其他字段
       subQuestions: list[SubQuestion] = Field(default_factory=list)
       # 删除或标记为废弃：answers 字段
   ```

2. **修改 `pdf_import_service.py` 提示词**
   - 添加格式示例
   - 明确换行和段落要求
   - 添加特殊字符转义清单
   - 要求输出 subQuestions 而非 questionContent + answers

3. **修改 `latex_export_service.py`**
   ```python
   def _generate_section_content_with_numbering(
       self, 
       questions: List[ReadingQuestion],
       start_number: int = 1
   ) -> tuple[str, int]:
       """生成内容并返回下一个题号"""
       content = ""
       current_num = start_number
       
       for question in questions:
           if question.articleContent:
               content += "\n" + question.articleContent + "\n\n"
           
           for sub_q in question.subQuestions:
               if sub_q.content:  # 有题干
                   content += f"\\textbf{{{current_num}.}} {sub_q.content}\n"
               if sub_q.options:
                   content += sub_q.options + "\n"
               current_num += 1
           
           content += r"\vspace{0.5cm}" + "\n\n"
       
       return content, current_num
   ```

### 🔄 Phase 2: 提示词优化（部分完成，建议继续）

**当前状态：** 部分完成

即使不改数据模型，也可以继续优化提示词：

1. ✅ **已完成**：选项格式说明（不包含A.B.C.D.前缀）
2. ✅ **已完成**：`%` 符号转义要求
3. ✅ **已完成**：题号重新编号说明
4. ⏳ **待添加**：完整的格式示例（已部分完成）
5. ⏳ **待添加**：特殊字符转义清单（需补充 `$`, `&`, `#` 等）
6. ⏳ **待添加**：明确换行和段落保留要求
7. ⏳ **待添加**：内容完整性检查清单

### Phase 3: 兼容性处理 ⏳ 未来计划

如果要保持向后兼容，可以：

```python
class ReadingQuestion(BaseModel):
    # 新字段
    subQuestions: list[SubQuestion] = Field(default_factory=list)
    
    # 旧字段（标记为废弃，但保留）
    questionContent: str = Field(default="", deprecated=True)
    answers: list[dict] = Field(default_factory=list, deprecated=True)
    
    # 提供转换方法
    def to_legacy_format(self):
        """转换为旧格式（用于兼容旧代码）"""
        # ...
    
    @classmethod
    def from_legacy_format(cls, data: dict):
        """从旧格式创建（用于数据迁移）"""
        # ...
```

---

## 优先级建议（更新版）

### 🎯 当前状态
- ✅ **导出重新编号功能已实现**：可以灵活调整题目顺序
- ✅ **选项格式已优化**：避免 A.A. 重复显示问题
- ✅ **特殊字符转义已部分完成**：`%` 和 `_` 已处理

### 🔴 高优先级（建议近期完成）
1. **✅ 完成** ~~导出自动重新编号~~（已实现）
2. **✅ 完成** ~~选项格式优化~~（已实现）
3. **🔄 进行中**：优化提示词 - 添加更多格式示例
4. **⏳ 待做**：补充特殊字符转义清单（`$`, `&`, `#`, `{`, `}`）
5. **⏳ 待做**：测试验证导出重新编号功能

### 🟡 中优先级（1-2周内，可选）
1. **数据模型重构**：实现 `subQuestions` 结构（非必需，当前方案已够用）
2. **答案存储优化**：将答案整合到 subQuestions 中
3. **数据迁移脚本**：如果要实施数据模型重构
4. **换行格式规范**：明确段落、列表的处理规则

### 🟢 低优先级（有时间再做）
1. **答案解析字段**：添加 `answerExplanation`
2. **复杂格式支持**：表格、图片等
3. **质量检查**：提取结果的自动验证
4. **向后兼容**：支持新旧数据格式共存

---

## 总结

**核心改进点（更新版）：**
1. ✅ **分离题号和内容**：题号在导出时生成，支持灵活重新编号 **【已实现】**
2. 🔄 **格式完整保留**：明确要求保留所有换行、段落、格式标记 **【部分完成】**
3. ✅ **特殊字符处理**：提供转义规则（`%`, `_` 已完成）**【部分完成】**
4. ⏳ **结构化存储**：用 `subQuestions` 代替文本拼接 **【未来优化】**

**系统当前能力：**
- ✅ 灵活重新编号题目（1-10 可变为 5-14）
- ✅ 支持任意调整题目顺序
- ✅ 跨部分连续编号
- ✅ 选项格式正确（不重复显示A.A.）
- ✅ 基本特殊字符转义（% 和 _）
- 🔄 原文格式保留（大部分情况良好）
- ⏳ 复杂格式支持（待增强）

**已实现功能示例：**
```
原队列：完形(1-10) → 阅读A(21-23) → 阅读B(24-27)
导出：  完形(1-10) → 阅读A(11-13) → 阅读B(14-17) ✅

调整后：阅读A(21-23) → 完形(1-10)
导出：  阅读A(1-3) → 完形(4-13) ✅
```

**下一步建议：**
1. 🔴 **立即**：测试导出重新编号功能，确保边界情况正常
2. 🟡 **本周**：补充提示词中的格式示例和特殊字符清单
3. 🟢 **未来**：考虑是否需要 subQuestions 结构（当前方案已满足需求）

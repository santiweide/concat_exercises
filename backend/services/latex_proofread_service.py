"""
LaTeX Proofread Service - Uses AI models to validate LaTeX exam paper formatting
against the standard exam paper format RFC.
"""
import structlog
from typing import Optional, Dict, Any
from config import config
from services.ai_models import GeminiModel, QwenVLModel

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────
# 组卷系统格式 RFC —— 校对 Prompt
# ─────────────────────────────────────────────────────────────────────
PROOFREAD_PROMPT = r"""你是一位专业的高考英语试卷LaTeX排版校对专家。请根据以下《组卷系统格式RFC》对给出的LaTeX源码进行逐项校对，并给出详细的校对报告。

## 组卷系统格式RFC

### 一、试卷首页整体排版结构

#### 1. 标题区
1. 页面顶部居中放置一行中文标题（字体：黑体，字号：小三，加粗）
   - 内容示例：北京市丰台区2024—2025学年度第二学期综合练习（一）
2. 下一行居中放置科目名称（字体：黑体，字号：三号，加粗）
   - 内容：高三英语
3. 在同一行的最右侧放置考试时间（字体：宋体，字号：小四）
   - 内容示例：2025.03
4. 标题区下方换行，居中显示考试信息（字体：宋体，字号：小四）
   - 内容示例：本试卷共12页，100分。考试时长90分钟。
5. 再换一行，居中显示试卷结构（字体：黑体，字号：小四，加粗）
   - 内容：笔试  共三部分（100分）

### 二、部分标题格式
每一部分标题统一格式：左对齐、黑体、小四号、加粗、标题前后各空一行
- 示例：第一部分  知识运用（共两节，30分）

### 三、小节标题格式
每一节的标题格式：左对齐、黑体、小四、加粗
- 示例：第一节  完形填空（共10小题，每小题1.5分，共15分）

### 四、题干说明格式
说明文字：左对齐、宋体、小四、不加粗、与正文之间空一行
- 示例：阅读下面短文，掌握其大意，从每题所给的A、B、C、D四个选项中，选出最佳选项。

### 五、完形填空版式规则
1. 文章排版：左对齐、宋体、小四、段落首行缩进两个汉字、行距1.25
2. 空格格式：使用下划线，宽度约等于1.5个英文单词
3. 空格编号：在下划线前插入编号，使用阿拉伯数字，与下划线之间留一个空格
4. 选项列表格式：左对齐、宋体、小四、每行两个题目
   - 题号后有句点，选项字母后有句点，选项之间用4个空格分隔

### 六、语法填空版式
- 分为A/B/C三段材料
- 材料标题：居中、黑体、小四、单个大写字母
- 材料正文：左对齐、宋体、小四、首行缩进2字符
- 空格格式：编号在前，下划线约2厘米，括号中给提示词

### 七、阅读理解版式
- 文章标题：居中、全部大写、黑体、小四
- 文章正文：宋体、小四、首行缩进2字符、段落之间空一行
- 题号从21开始
- 题干：左对齐、宋体、小四
- 选项：每行一个、左缩进两个字符

### 八、七选五版式
- 文章空格编号：____35____（前后均为下划线，中间为题号）
- 选项列表：A-G，每行一个选项，左对齐

### 九、阅读表达版式（第三部分 第一节）
- 文章：宋体、小四、首行缩进2字符
- 题号40-43
- **不需要** \rule{\linewidth}{0.4pt} 横线，题目之间保持正常间距即可

### 十、书面表达版式（第三部分 第二节）
- 标题：第二节（20分）
- 写作说明：宋体、小四
- 写作区域：仅保留 **5行** \rule{\linewidth}{0.4pt} 横线示意写作空间，不要多也不要少

### 十一、页脚
- 居中：高三英语  第X页（共12页）
- 宋体、五号

### 十二、多语言排版规则（关键）
- 中文字体：宋体，行距1.25
- 英文字体：Times New Roman，字号与中文一致
- 中英文混排：中文与英文之间留半角空格，英文标点保持半角

### 十三、题号统一规则
| 类型 | 编号 |
|------|------|
| 完形填空 | 1–10 |
| 语法填空 | 11–20 |
| 阅读理解 | 21–34 |
| 七选五 | 35–39 |
| 阅读表达 | 40–43 |

### 十四、自动生成LaTeX的关键结构
标题区 → 第一部分(完形填空+语法填空) → 第二部分(阅读理解A-D+七选五) → 第三部分(阅读表达+写作) → 页脚

---

## 校对要求

请逐项检查以上RFC中的每一条规则，对照LaTeX源码给出校对报告。报告格式要求：

1. **使用JSON格式**返回校对结果
2. 每个问题包含以下字段：
   - `rule`: 对应的RFC规则编号（如"一.1", "五.4"等）
   - `severity`: 严重程度（"error" | "warning" | "info"）
     - error: 严重格式问题，必须修改
     - warning: 格式不够规范，建议修改
     - info: 建议优化项
   - `description`: 问题描述（中文）
   - `location`: 问题在LaTeX中的大致位置描述
   - `suggestion`: 修改建议（中文），如果可能，给出修正后的LaTeX片段
3. 如果某条规则完全符合，也列出，severity设为"pass"
4. 最后给出一个总体评分（0-100），以及总结

返回JSON格式如下：
```json
{
  "score": 85,
  "summary": "总体格式基本规范，存在X个错误，Y个警告...",
  "issues": [
    {
      "rule": "一.1",
      "severity": "pass",
      "description": "标题区格式正确",
      "location": "文档头部",
      "suggestion": ""
    },
    {
      "rule": "五.4",
      "severity": "error",
      "description": "完形填空选项格式不正确，应为每行两个题目",
      "location": "完形填空选项部分",
      "suggestion": "将\\option改为\\optiontwo，或调整multicols为2栏"
    }
  ],
  "auto_fixes": [
    {
      "description": "修复描述",
      "original": "原始LaTeX片段",
      "fixed": "修正后的LaTeX片段"
    }
  ]
}
```

请仅返回JSON，不要添加其他文字。
"""


class LatexProofreadService:
    """Service for proofreading LaTeX exam papers using AI models."""

    def __init__(self):
        """Initialize the proofread service."""
        self._model = None

    def _get_model(self, model_type: str = None):
        """Get AI model instance (lazy initialization)."""
        if model_type is None:
            model_type = config.DEFAULT_AI_MODEL

        model_type = model_type.lower()

        if model_type == "gemini":
            api_key = config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY is required for Gemini model")
            return GeminiModel(api_key)
        elif model_type == "qwen-vl":
            api_key = config.QWEN_API_KEY
            if not api_key:
                raise ValueError("QWEN_API_KEY is required for Qwen VL model")
            return QwenVLModel(api_key)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    async def proofread_latex(
        self,
        latex_content: str,
        model_type: str = None,
    ) -> Dict[str, Any]:
        """
        Proofread LaTeX content against the exam paper format RFC.

        Args:
            latex_content: The generated LaTeX source code to proofread
            model_type: AI model to use ("gemini" or "qwen-vl")

        Returns:
            Dict with proofreading results including score, issues, and auto_fixes
        """
        model = self._get_model(model_type)

        logger.info(
            "Starting LaTeX proofreading",
            model=model.name,
            latex_length=len(latex_content),
        )

        try:
            # Use the model's text extraction capability with our proofread prompt
            result = await model.extract_from_text(
                text_content=latex_content,
                filename="exam_paper.tex",
                prompt=PROOFREAD_PROMPT,
            )

            if result is None:
                logger.error("AI model returned no result for proofreading")
                return {
                    "success": False,
                    "error": "AI模型未返回有效结果，请稍后重试",
                    "score": 0,
                    "summary": "",
                    "issues": [],
                    "auto_fixes": [],
                }

            # Validate the response structure
            score = result.get("score", 0)
            summary = result.get("summary", "")
            issues = result.get("issues", [])
            auto_fixes = result.get("auto_fixes", [])

            # Normalize issues
            normalized_issues = []
            for issue in issues:
                normalized_issues.append({
                    "rule": issue.get("rule", ""),
                    "severity": issue.get("severity", "info"),
                    "description": issue.get("description", ""),
                    "location": issue.get("location", ""),
                    "suggestion": issue.get("suggestion", ""),
                })

            # Normalize auto_fixes
            normalized_fixes = []
            for fix in auto_fixes:
                normalized_fixes.append({
                    "description": fix.get("description", ""),
                    "original": fix.get("original", ""),
                    "fixed": fix.get("fixed", ""),
                })

            logger.info(
                "LaTeX proofreading completed",
                score=score,
                issues_count=len(normalized_issues),
                fixes_count=len(normalized_fixes),
                errors=len([i for i in normalized_issues if i["severity"] == "error"]),
                warnings=len([i for i in normalized_issues if i["severity"] == "warning"]),
            )

            return {
                "success": True,
                "score": score,
                "summary": summary,
                "issues": normalized_issues,
                "auto_fixes": normalized_fixes,
            }

        except Exception as e:
            logger.exception("LaTeX proofreading failed", error=str(e))
            return {
                "success": False,
                "error": f"校对失败: {str(e)}",
                "score": 0,
                "summary": "",
                "issues": [],
                "auto_fixes": [],
            }

    async def proofread_and_fix(
        self,
        latex_content: str,
        model_type: str = None,
    ) -> Dict[str, Any]:
        """
        Proofread and automatically apply fixes to LaTeX content.

        Args:
            latex_content: The generated LaTeX source code
            model_type: AI model to use

        Returns:
            Dict with proofread result and optionally the fixed LaTeX
        """
        # First, proofread
        result = await self.proofread_latex(latex_content, model_type)

        if not result.get("success"):
            return result

        # If there are auto_fixes, apply them
        fixed_latex = latex_content
        fixes_applied = 0

        for fix in result.get("auto_fixes", []):
            original = fix.get("original", "")
            fixed = fix.get("fixed", "")
            if original and fixed and original in fixed_latex:
                fixed_latex = fixed_latex.replace(original, fixed, 1)
                fixes_applied += 1

        result["fixed_latex"] = fixed_latex if fixes_applied > 0 else None
        result["fixes_applied"] = fixes_applied

        logger.info(
            "Auto-fix applied",
            fixes_applied=fixes_applied,
            total_fixes=len(result.get("auto_fixes", [])),
        )

        return result

    async def generate_fixed_latex(
        self,
        latex_content: str,
        proofread_result: Dict[str, Any],
        model_type: str = None,
    ) -> Dict[str, Any]:
        """
        Use AI to generate a fully corrected LaTeX file based on the proofread issues.

        This sends the original LaTeX + the proofread issues to the AI and asks it
        to produce a corrected, complete LaTeX document.

        Args:
            latex_content: The original LaTeX source code
            proofread_result: The proofread result containing issues and suggestions
            model_type: AI model to use

        Returns:
            Dict with success status and fixed_latex content
        """
        model = self._get_model(model_type)

        # Build a summary of issues for the AI
        issues_summary = []
        for issue in proofread_result.get("issues", []):
            if issue.get("severity") in ("error", "warning"):
                issues_summary.append(
                    f"- [{issue.get('severity')}] 规则{issue.get('rule')}: "
                    f"{issue.get('description')} "
                    f"(位置: {issue.get('location', '未知')})"
                    + (f"\n  建议: {issue.get('suggestion')}" if issue.get("suggestion") else "")
                )

        issues_text = "\n".join(issues_summary) if issues_summary else "无需修复的问题"

        fix_prompt = r"""你是一位专业的高考英语试卷LaTeX排版专家。

我有一份LaTeX试卷源码，经过校对后发现了以下格式问题。请根据校对问题列表，对LaTeX源码进行修正，生成一份完整的、符合《组卷系统格式RFC》的LaTeX文件。

## 校对发现的问题：
""" + issues_text + r"""

## 修正要求：
1. **输出完整的LaTeX文件**：从 \documentclass 到 \end{document}，可以直接编译
2. **只修正校对中指出的问题**，不要改变试卷内容本身（题目、文章、选项等）
3. **保持所有原始题目内容不变**，只调整格式、排版命令
4. **确保符合以下关键规则**：
   - 标题区：居中，黑体标题，科目+时间同行
   - 部分标题：左对齐，黑体，小四，加粗，前后空行
   - 小节标题：左对齐，黑体，小四，加粗
   - 完形填空选项：每行两个题目（\optiontwo）
   - 阅读理解选项：每行一个（\optionone）
   - 中文用宋体(SimSun/songti)，英文用Times New Roman
   - 页脚居中：高三英语 第X页（共Y页）
   - 题号连续：完形1-10，语法11-20，阅读21-34，七选五35-39，阅读表达40-43
   - 第三部分第一节（阅读表达）：不需要 \rule{\linewidth}{0.4pt} 横线
   - 第三部分第二节（书面表达/写作）：写作区域仅保留5行 \rule{\linewidth}{0.4pt} 横线示意
5. **仅输出LaTeX代码**，不要添加任何解释文字、markdown标记或代码块标记（不要```latex```）
"""

        logger.info(
            "Generating fixed LaTeX with AI",
            model=model.name,
            issues_count=len(issues_summary),
        )

        try:
            raw_text = await model.generate_text_raw(
                prompt=fix_prompt,
                content=latex_content,
            )

            if raw_text is None:
                logger.error("AI model returned no result for LaTeX fix generation")
                return {
                    "success": False,
                    "error": "AI模型未返回有效结果，请稍后重试",
                    "fixed_latex": None,
                }

            # Clean up: remove markdown code block markers if present
            fixed_latex = raw_text.strip()
            if fixed_latex.startswith("```latex"):
                fixed_latex = fixed_latex[len("```latex"):].strip()
            elif fixed_latex.startswith("```tex"):
                fixed_latex = fixed_latex[len("```tex"):].strip()
            elif fixed_latex.startswith("```"):
                fixed_latex = fixed_latex[3:].strip()
            if fixed_latex.endswith("```"):
                fixed_latex = fixed_latex[:-3].strip()

            # Validate it looks like a LaTeX document
            if r"\documentclass" not in fixed_latex:
                logger.warning("Generated text doesn't look like LaTeX, returning as-is")

            logger.info(
                "Fixed LaTeX generated successfully",
                original_length=len(latex_content),
                fixed_length=len(fixed_latex),
            )

            return {
                "success": True,
                "fixed_latex": fixed_latex,
            }

        except Exception as e:
            logger.exception("Failed to generate fixed LaTeX", error=str(e))
            return {
                "success": False,
                "error": f"生成修正版失败: {str(e)}",
                "fixed_latex": None,
            }


# Global service instance
latex_proofread_service = LatexProofreadService()

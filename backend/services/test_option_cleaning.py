#!/usr/bin/env python3
"""Test script for option prefix cleaning functionality"""

import re

def clean_option_prefixes(text: str) -> str:
    """
    Remove A. B. C. D. prefixes from option content to avoid duplication.
    """
    if not text:
        return text
    
    def clean_single_option(match):
        """清理单个 \option{}{}{}{} 或类似命令"""
        full_match = match.group(0)
        command = match.group(1)
        
        result = f"\\{command}"
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
    
    # 处理三种选项命令
    pattern = r'\\(option|optiontwo|optionone)\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}'
    text = re.sub(pattern, clean_single_option, text)
    
    return text


# 测试用例
test_cases = [
    {
        "name": "带 A.B.C.D. 前缀的 \\option",
        "input": r"\option{A. apple}{B. banana}{C. orange}{D. grape}",
        "expected": r"\option{apple}{banana}{orange}{grape}"
    },
    {
        "name": "带 A.B.C.D. 前缀的 \\optiontwo",
        "input": r"\optiontwo{A. To protect}{B. To promote}{C. To study}{D. To develop}",
        "expected": r"\optiontwo{To protect}{To promote}{To study}{To develop}"
    },
    {
        "name": "带 A.B.C.D. 前缀的 \\optionone",
        "input": r"\optionone{A. First option}{B. Second option}{C. Third option}{D. Fourth option}",
        "expected": r"\optionone{First option}{Second option}{Third option}{Fourth option}"
    },
    {
        "name": "混合：有些有前缀，有些没有",
        "input": r"\option{A. apple}{banana}{C. orange}{grape}",
        "expected": r"\option{apple}{banana}{orange}{grape}"
    },
    {
        "name": "完整题目内容",
        "input": r"\textbf{21.} What is the main idea?\n\option{A. Climate change}{B. Ocean pollution}{C. Deforestation}{D. Urban sprawl}",
        "expected": r"\textbf{21.} What is the main idea?\n\option{Climate change}{Ocean pollution}{Deforestation}{Urban sprawl}"
    },
    {
        "name": "多个选项命令",
        "input": r"\textbf{1.} Q1\n\option{A. a1}{B. b1}{C. c1}{D. d1}\n\textbf{2.} Q2\n\optiontwo{A. a2}{B. b2}{C. c2}{D. d2}",
        "expected": r"\textbf{1.} Q1\n\option{a1}{b1}{c1}{d1}\n\textbf{2.} Q2\n\optiontwo{a2}{b2}{c2}{d2}"
    },
    {
        "name": "没有前缀的选项（不应改变）",
        "input": r"\option{apple}{banana}{orange}{grape}",
        "expected": r"\option{apple}{banana}{orange}{grape}"
    },
    {
        "name": "带空格的前缀",
        "input": r"\option{A.  apple}{B.  banana}{C.  orange}{D.  grape}",
        "expected": r"\option{apple}{banana}{orange}{grape}"
    },
]


def run_tests():
    """运行所有测试用例"""
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("Testing Option Prefix Cleaning")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        result = clean_option_prefixes(test["input"])
        
        if result == test["expected"]:
            print(f"✅ Test {i}: {test['name']}")
            passed += 1
        else:
            print(f"❌ Test {i}: {test['name']}")
            print(f"   Input:    {test['input']}")
            print(f"   Expected: {test['expected']}")
            print(f"   Got:      {result}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

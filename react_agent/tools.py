"""内置工具集：计算器、字数统计、本地 mock 搜索。

每个工具是一个名字 -> (函数, 描述) 的注册表，Agent 据此选择并调用。
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List

from .calculator import safe_calc, CalcError


# ---- 工具实现 ---------------------------------------------------------------

def word_count(text: str) -> str:
    """统计文本：汉字字数 + 英文单词数。"""
    if not text:
        return "0"
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_words = len(re.findall(r"[a-zA-Z0-9]+", text))
    total = cjk + ascii_words
    return f"汉字 {cjk} 个，英文/数字词 {ascii_words} 个，合计约 {total} 个"


# 内置 mock 知识库（本地数据，不联网）
_MOCK_KB: List[Dict[str, str]] = [
    {"keywords": "python,编程语言,guido",
     "fact": "Python 由 Guido van Rossum 创建，1991 年首次发布，强调可读性。"},
    {"keywords": "光速,light,speed",
     "fact": "真空中光速约为 299,792,458 米/秒（约 3e8 m/s）。"},
    {"keywords": "地球,公转,一年",
     "fact": "地球绕太阳公转一周约 365.25 天。"},
    {"keywords": "水,沸点,boiling",
     "fact": "标准大气压下，水的沸点是 100 摄氏度。"},
    {"keywords": "react,框架,meta",
     "fact": "React 是 Meta 开源的前端 UI 库，核心概念是组件与单向数据流。"},
]


def mock_search(query: str) -> str:
    """在本地内置知识库中做关键词匹配，返回命中的事实。"""
    q = query.lower()
    hits: List[str] = []
    for item in _MOCK_KB:
        kws = [k.strip() for k in item["keywords"].split(",")]
        if any(k in q for k in kws):
            hits.append(item["fact"])
    if not hits:
        return f"（本地知识库）未找到与「{query}」直接相关的条目。"
    return "；".join(hits)


def _run_calculator(expression: str) -> str:
    try:
        return str(safe_calc(expression))
    except CalcError as exc:
        return f"计算失败: {exc}"


# ---- 工具注册表 -------------------------------------------------------------

TOOLS: Dict[str, Dict[str, object]] = {
    "calculator": {
        "func": _run_calculator,
        "description": "算术计算器。输入一个算术表达式，如 (12 + 8) * 3，返回数值结果。",
    },
    "word_count": {
        "func": word_count,
        "description": "字数统计。输入一段文本，返回其中的汉字与英文单词数量。",
    },
    "mock_search": {
        "func": mock_search,
        "description": "本地搜索。输入关键词，在内置小知识库中查找相关事实。",
    },
}


def call_tool(name: str, argument: str) -> str:
    """按名字调用工具；未知工具返回错误说明。"""
    tool = TOOLS.get(name)
    if tool is None:
        return f"未知工具: {name}（可用: {', '.join(TOOLS)}）"
    func: Callable[[str], str] = tool["func"]  # type: ignore[assignment]
    return func(argument)

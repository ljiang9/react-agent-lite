"""ReAct 循环：Thought / Action / Observation / Final Answer。

有 LLM（OPENAI_API_KEY）时由 LLMBrain 决策；否则用 RuleBasedBrain 按脚本规则
走完整套 ReAct 流程，轨迹同样完整打印。
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Protocol

from .tools import TOOLS, call_tool


@dataclass
class Action:
    """下一步：调用某个工具。"""
    thought: str
    tool: str
    tool_input: str


@dataclass
class FinalAnswer:
    """终止：给出最终答案。"""
    thought: str
    answer: str


class Brain(Protocol):
    """决策器接口：根据问题与历史观察，决定下一步动作。"""

    def start(self, question: str) -> None: ...
    def next_step(self, observations: List[str]) -> object: ...  # -> Action | FinalAnswer


# ---- 规则式本地大脑（无 LLM） ----------------------------------------------

class RuleBasedBrain:
    """不依赖 LLM 的脚本决策器：按关键词制定一个工具调用计划并逐步执行。"""

    def __init__(self) -> None:
        self.question = ""
        self.plan: List[Action] = []

    def start(self, question: str) -> None:
        self.question = question
        self.plan = self._make_plan(question)

    def _make_plan(self, q: str) -> List[Action]:
        plan: List[Action] = []
        # 1) 需要事实 -> 先搜索
        if re.search(r"(什么是|谁|哪里|什么时候|搜索|查一下|关于|介绍)", q):
            plan.append(Action(
                thought="我需要先从本地知识库查一下相关事实。",
                tool="mock_search", tool_input=q,
            ))
        # 2) 需要计算 -> 提取算式
        expr = self._extract_expr(q)
        if expr:
            plan.append(Action(
                thought="题目包含算术运算，我用计算器算一下。",
                tool="calculator", tool_input=expr,
            ))
        # 3) 需要字数统计
        if re.search(r"(几个字|字数|多少字|多长)", q):
            plan.append(Action(
                thought="这是一个字数统计问题，我调用字数统计工具。",
                tool="word_count", tool_input=q,
            ))
        return plan

    @staticmethod
    def _extract_expr(q: str) -> Optional[str]:
        # 截取含数字与运算符的片段作为算式
        m = re.search(r"[\d+\-*/().\s]+", q)
        if m and re.search(r"\d", m.group(0)) and re.search(r"[+\-*/]", m.group(0)):
            return m.group(0).strip()
        return None

    def next_step(self, observations: List[str]) -> object:
        if self.plan:
            return self.plan.pop(0)
        obs_text = "；".join(observations) if observations else "没有可参考的观察。"
        return FinalAnswer(
            thought="工具已给出足够信息，我可以总结最终答案了。",
            answer=f"基于以下观察作答：{obs_text}",
        )


# ---- LLM 大脑（可选） -------------------------------------------------------

class LLMBrain:
    """调用 OpenAI 兼容接口做 ReAct 决策。输出约定格式的 Thought/Action。"""

    def __init__(self) -> None:
        self.question = ""
        base_url = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.messages: List[dict] = []

    def _system_prompt(self) -> str:
        tools_desc = "\n".join(f"- {n}: {t['description']}" for n, t in TOOLS.items())
        return (
            "你是一个使用工具进行推理的 ReAct 智能体。请严格按以下格式逐行输出：\n"
            "Thought: 你的思考\n"
            "Action: 工具名（必须是下面之一）\n"
            "Action Input: 传给工具的参数\n"
            "当信息足够时输出：\n"
            "Thought: 你的思考\n"
            "Final Answer: 最终答案\n"
            f"可用工具：\n{tools_desc}"
        )

    def start(self, question: str) -> None:
        self.question = question
        self.messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": question},
        ]

    def _call_llm(self) -> str:
        payload = {"model": self.model, "messages": self.messages, "temperature": 0}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": text})
        return text

    def next_step(self, observations: List[str]) -> object:
        if observations:
            self.messages.append({"role": "user",
                                  "content": f"Observation: {observations[-1]}"})
        raw = self._call_llm()
        return self._parse(raw)

    @staticmethod
    def _parse(text: str) -> object:
        thought_m = re.search(r"Thought:\s*(.+)", text)
        thought = thought_m.group(1).strip() if thought_m else ""
        final_m = re.search(r"Final Answer:\s*(.+)", text, re.S)
        if final_m:
            return FinalAnswer(thought=thought, answer=final_m.group(1).strip())
        action_m = re.search(r"Action:\s*([^\n]+)", text)
        input_m = re.search(r"Action Input:\s*(.+)", text)
        if action_m and input_m:
            return Action(thought=thought, tool=action_m.group(1).strip(),
                          tool_input=input_m.group(1).strip())
        # 解析失败时直接把原文当最终答案，避免死循环
        return FinalAnswer(thought="无法解析工具调用，直接作答。", answer=text.strip())


# ---- Agent 主循环 ----------------------------------------------------------

class Agent:
    """ReAct 智能体：循环 Thought -> Action -> Observation 直到 Final Answer。"""

    def __init__(self, brain: Optional[Brain] = None, max_steps: int = 6,
                 verbose: bool = True) -> None:
        self.brain = brain or RuleBasedBrain()
        self.max_steps = max_steps
        self.verbose = verbose

    def run(self, question: str) -> str:
        self.brain.start(question)
        observations: List[str] = []
        for _ in range(self.max_steps):
            step = self.brain.next_step(observations)
            if isinstance(step, FinalAnswer):
                self._print(f"Thought: {step.thought}")
                self._print(f"Final Answer: {step.answer}")
                return step.answer
            if isinstance(step, Action):
                self._print(f"Thought: {step.thought}")
                self._print(f"Action: {step.tool}")
                self._print(f"Action Input: {step.tool_input}")
                obs = call_tool(step.tool, step.tool_input)
                observations.append(obs)
                self._print(f"Observation: {obs}")
                continue
            raise TypeError(f"未知的决策类型: {type(step)}")
        return "（达到最大步数仍未得出最终答案）"

    def _print(self, line: str) -> None:
        if self.verbose:
            print(line)

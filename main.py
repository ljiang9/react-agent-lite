"""命令行入口：python3 main.py "你的问题"

有 OPENAI_API_KEY 时用 LLM 决策；否则自动使用规则式本地大脑走完整 ReAct 流程。
"""

from __future__ import annotations

import os

from react_agent.agent import Agent, RuleBasedBrain, LLMBrain


def main() -> None:
    question = input("请输入你的问题: ").strip()
    if not question:
        print("问题不能为空")
        return

    if os.environ.get("OPENAI_API_KEY"):
        print("（模式：LLM 决策）")
        brain = LLMBrain()
    else:
        print("（模式：本地规则大脑，未检测到 OPENAI_API_KEY）")
        brain = RuleBasedBrain()

    print("=== ReAct 轨迹 ===")
    Agent(brain=brain).run(question)


if __name__ == "__main__":
    main()

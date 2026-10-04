import io
import contextlib
import unittest

from react_agent.agent import (
    Agent, RuleBasedBrain, LLMBrain, Action, FinalAnswer,
)


class TestRuleBasedAgent(unittest.TestCase):
    def test_calculation_question(self):
        brain = RuleBasedBrain()
        agent = Agent(brain=brain, verbose=False)
        out = agent.run("请计算 (12 + 8) * 3 等于多少")
        # 计划里应有 calculator 动作，最终答案引用观察 60
        self.assertTrue(brain.plan == [])  # 计划已被消费完
        self.assertIn("60", out)

    def test_search_question(self):
        brain = RuleBasedBrain()
        agent = Agent(brain=brain, verbose=False)
        out = agent.run("搜索一下 Python 是谁创造的")
        self.assertIn("Guido", out)

    def test_full_trace_prints(self):
        brain = RuleBasedBrain()
        agent = Agent(brain=brain, verbose=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agent.run("计算 2 ** 10，顺便介绍一下 React 框架")
        text = buf.getvalue()
        self.assertIn("Thought:", text)
        self.assertIn("Action:", text)
        self.assertIn("Observation:", text)
        self.assertIn("Final Answer:", text)
        self.assertIn("1024", text)

    def test_no_plan_then_final(self):
        brain = RuleBasedBrain()
        agent = Agent(brain=brain, verbose=False)
        out = agent.run("今天天气真好")  # 无工具可调用
        self.assertTrue(out.startswith("基于以下观察"))


class TestLLMBrainParser(unittest.TestCase):
    def test_parse_action(self):
        text = "Thought: 我要算一下\nAction: calculator\nAction Input: 1+1"
        step = LLMBrain._parse(text)
        self.assertIsInstance(step, Action)
        self.assertEqual(step.tool, "calculator")
        self.assertEqual(step.tool_input, "1+1")

    def test_parse_final(self):
        text = "Thought: 信息够了\nFinal Answer: 答案是 42"
        step = LLMBrain._parse(text)
        self.assertIsInstance(step, FinalAnswer)
        self.assertIn("42", step.answer)

    def test_parse_garbage_falls_back(self):
        step = LLMBrain._parse("随便一段没有格式的话")
        self.assertIsInstance(step, FinalAnswer)


if __name__ == "__main__":
    unittest.main()

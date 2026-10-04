import unittest

from react_agent.tools import word_count, mock_search, call_tool, TOOLS


class TestWordCount(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(word_count(""), "0")

    def test_mixed(self):
        out = word_count("你好世界 hello python")
        self.assertIn("4", out)   # 4 个汉字
        self.assertIn("2", out)   # 2 个英文词

    def test_only_cjk(self):
        out = word_count("我爱编程")
        self.assertIn("4", out)


class TestMockSearch(unittest.TestCase):
    def test_hit_python(self):
        out = mock_search("什么是 Python 编程语言")
        self.assertIn("Guido", out)

    def test_hit_light(self):
        out = mock_search("光速是多少")
        self.assertIn("299", out)

    def test_miss(self):
        out = mock_search("量子坍缩理论")
        self.assertIn("未找到", out)


class TestCallTool(unittest.TestCase):
    def test_unknown_tool(self):
        out = call_tool("nonexistent", "x")
        self.assertIn("未知工具", out)

    def test_calculator_tool(self):
        self.assertEqual(call_tool("calculator", "(1+2)*4"), "12")

    def test_registry_not_empty(self):
        self.assertGreaterEqual(len(TOOLS), 3)


if __name__ == "__main__":
    unittest.main()

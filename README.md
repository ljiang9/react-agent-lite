# react-agent-lite

一个**零第三方依赖**的最小 ReAct 智能体原型：完整打印 `Thought / Action / Observation / Final Answer` 轨迹。内置三个工具——**ast 白名单安全计算器**、字数统计、本地 mock 搜索。有 API Key 时由 LLM 决策，无 Key 时用脚本规则大脑走完整套 ReAct 流程。

## 功能特性

- **ReAct 循环**：Thought → Action（调用工具）→ Observation（观察结果）→ … → Final Answer，全程打印轨迹。
- **安全计算器**：基于 `ast` 白名单求值，**严禁裸 `eval`/`exec`**，拒绝任何名字、函数调用、属性/下标访问。
- **内置工具**：
  - `calculator`：算术表达式求值（`(12+8)*3`）；
  - `word_count`：统计汉字与英文单词数；
  - `mock_search`：本地内置小知识库关键词检索，不联网。
- **双模式大脑**：
  - 有 `OPENAI_API_KEY`：`LLMBrain` 按约定格式输出 Thought/Action，循环调用；
  - 无 Key：`RuleBasedBrain` 按关键词制定计划，同样走完完整 ReAct 轨迹。

## 快速开始

环境要求：Python 3.10+（开发于 3.12）。无需安装任何依赖。

```bash
cd react-agent-lite

# 无 Key：本地规则大脑模式
python3 main.py
# 然后按提示输入问题，例如：请计算 (12 + 8) * 3 等于多少
```

### 接入 LLM（可选）

```bash
export OPENAI_API_KEY="sk-xxxx"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # 可选
export OPENAI_MODEL="gpt-4o-mini"                    # 可选
python3 main.py
```

## 使用示例

无 Key 时的实际运行效果：

```
$ printf '请计算 (12 + 8) * 3 等于多少，并搜索一下 Python\n' | python3 main.py
（模式：本地规则大脑，未检测到 OPENAI_API_KEY）
=== ReAct 轨迹 ===
Thought: 题目包含算术运算，我用计算器算一下。
Action: calculator
Action Input: (12 + 8) * 3
Observation: 60
Thought: 我需要先从本地知识库查一下相关事实。
Action: mock_search
Action Input: 请计算 (12 + 8) * 3 等于多少，并搜索一下 Python
Observation: Python 由 Guido van Rossum 创建，1991 年首次发布，强调可读性。
Thought: 工具已给出足够信息，我可以总结最终答案了。
Final Answer: 基于以下观察作答：60；Python 由 Guido van Rossum 创建，...
```

## 无 API Key 如何运行？

直接 `python3 main.py` 即可。程序检测不到 `OPENAI_API_KEY` 时自动使用 `RuleBasedBrain`：根据问题关键词（计算 / 搜索 / 字数）制定工具调用计划并逐步执行，Thought/Action/Observation/Final Answer 轨迹完整可见，不联网。

## 运行测试

```bash
python3 -m unittest discover -s tests
```

重点覆盖：
- `test_calculator.py`：ast 计算器的**正确性**（四则、幂、取余、一元）与**安全性**（拒绝 `__import__`、`open(...)`、属性访问、下标、赋值、布尔常量）；
- `test_tools.py`：字数统计、mock 搜索命中/未命中、未知工具；
- `test_agent.py`：规则大脑完整 ReAct 轨迹、LLM 输出解析（Action / Final / 兜底）。

## 目录结构

```
react-agent-lite/
├── main.py               # 命令行入口
├── react_agent/
│   ├── __init__.py
│   ├── calculator.py      # ast 白名单安全计算器
│   ├── tools.py          # 工具注册表：calculator / word_count / mock_search
│   └── agent.py          # ReAct 循环 + RuleBasedBrain / LLMBrain
├── tests/
│   ├── test_calculator.py
│   ├── test_tools.py
│   └── test_agent.py
├── README.md
├── LICENSE               # MIT
└── .gitignore
```

## 安全说明

计算器只通过 `ast.parse(..., mode="eval")` 并遍历语法树，白名单允许的节点仅限数字常量与二元/一元算术运算；任何其他节点（名字、调用、下标、属性、比较等）一律抛出 `CalcError`。**代码中不存在 `eval` / `exec` 调用。**

## 许可证

[MIT](./LICENSE) © ljiang9

"""react-agent-lite：一个最小可运行的 ReAct 智能体原型。"""

from .calculator import safe_calc, CalcError
from .tools import TOOLS, word_count, mock_search
from .agent import Agent, RuleBasedBrain, LLMBrain, Action, FinalAnswer

__all__ = [
    "safe_calc", "CalcError",
    "TOOLS", "word_count", "mock_search",
    "Agent", "RuleBasedBrain", "LLMBrain", "Action", "FinalAnswer",
]
__version__ = "0.1.0"

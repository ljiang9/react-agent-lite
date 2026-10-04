"""安全计算器：用 ast 白名单求值，严禁裸 eval / exec。

只允许：数字常量、加减乘除、整除、取余、幂运算、一元正负号。
任何名字、函数调用、下标、属性访问等一律拒绝。
"""

from __future__ import annotations

import ast
import operator
from typing import Any

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalcError(Exception):
    """表达式不合法或求值失败。"""


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise CalcError(f"不支持的常量类型: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise CalcError(f"不支持的运算符: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise CalcError(f"不支持的一元运算符: {type(node.op).__name__}")
        return op(_eval_node(node.operand))

    raise CalcError(f"不允许的语法节点: {type(node).__name__}")


def safe_calc(expression: str) -> float:
    """对算术表达式做白名单求值，返回数值结果。

    示例:
        safe_calc("(12 + 8) * 3") -> 60.0
    抛 CalcError 表示表达式非法（含危险语法）。
    """
    if not isinstance(expression, str) or not expression.strip():
        raise CalcError("表达式为空")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalcError(f"语法错误: {exc}") from exc
    result = _eval_node(tree)
    if not isinstance(result, (int, float)) or isinstance(result, bool):
        raise CalcError("结果不是数值")
    # 整数值用 int 返回更友好
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result

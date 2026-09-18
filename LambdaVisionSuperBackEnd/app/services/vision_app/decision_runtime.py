from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
}
_ALLOWED_CMPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
}
_ALLOWED_CALLS = {"abs": abs, "min": min, "max": max, "len": len, "round": round}


class DecisionScriptError(ValueError):
    pass


class _Evaluator:
    def __init__(self, context: dict[str, Any]) -> None:
        self.env = dict(context)

    def expr(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            if node.id in {"True", "False", "None"}:
                return {"True": True, "False": False, "None": None}[node.id]
            raise DecisionScriptError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Dict):
            return {self.expr(k): self.expr(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.List):
            return [self.expr(v) for v in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.expr(v) for v in node.elts)
        if isinstance(node, ast.Subscript):
            return self.expr(node.value)[self.expr(node.slice)]
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand)
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            raise DecisionScriptError("Unary operator is not allowed")
        if isinstance(node, ast.BoolOp):
            values = [self.expr(v) for v in node.values]
            if isinstance(node.op, ast.And):
                result = True
                for value in values:
                    result = result and value
                    if not result:
                        break
                return result
            if isinstance(node.op, ast.Or):
                result = False
                for value in values:
                    result = result or value
                    if result:
                        break
                return result
            raise DecisionScriptError("Boolean operator is not allowed")
        if isinstance(node, ast.BinOp):
            fn = _ALLOWED_BINOPS.get(type(node.op))
            if fn is None:
                raise DecisionScriptError("Arithmetic operator is not allowed")
            return fn(self.expr(node.left), self.expr(node.right))
        if isinstance(node, ast.Compare):
            left = self.expr(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self.expr(comparator)
                fn = _ALLOWED_CMPS.get(type(op))
                if fn is None:
                    raise DecisionScriptError("Comparison operator is not allowed")
                if not fn(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self.expr(node.body if self.expr(node.test) else node.orelse)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_CALLS:
                raise DecisionScriptError("Only abs/min/max/len/round calls are allowed")
            return _ALLOWED_CALLS[node.func.id](*[self.expr(arg) for arg in node.args])
        raise DecisionScriptError(f"Expression is not allowed: {type(node).__name__}")

    def stmt(self, node: ast.stmt) -> None:
        if isinstance(node, ast.If):
            branch = node.body if self.expr(node.test) else node.orelse
            for child in branch:
                self.stmt(child)
            return
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                raise DecisionScriptError("Assignments may only target simple names")
            name = node.targets[0].id
            if name != "result":
                raise DecisionScriptError("Only the 'result' variable may be assigned")
            self.env[name] = self.expr(node.value)
            return
        if isinstance(node, ast.Pass):
            return
        raise DecisionScriptError(f"Statement is not allowed: {type(node).__name__}")

    def run(self, script: str) -> Any:
        try:
            tree = ast.parse(script or "", mode="exec")
        except SyntaxError as exc:
            raise DecisionScriptError(f"Decision script syntax error: {exc.msg} (line {exc.lineno})") from exc
        for node in tree.body:
            self.stmt(node)
        if "result" not in self.env:
            raise DecisionScriptError("Decision script must assign result = 'OK'/'NG' or a boolean")
        return self.env["result"]


def run_decision_script(script: str, context: dict[str, Any]) -> tuple[bool, str]:
    value = _Evaluator(context).run(script)
    if isinstance(value, bool):
        return value, "OK" if value else "NG"
    normalized = str(value).strip().upper()
    if normalized not in {"OK", "NG"}:
        raise DecisionScriptError("Decision result must be OK, NG, True or False")
    return normalized == "OK", normalized

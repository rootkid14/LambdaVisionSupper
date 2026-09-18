from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Callable

from app.services.vision_app.automation_models import (
    AutomationExecutionResult,
    AutomationServiceDefinition,
    AutomationTraceEntry,
    AutomationValidationIssue,
    VisionRunSnapshot,
)
from app.services.vision_app.models import VisionProgramDefinition

_ALLOWED_CONST_NAMES = {"ON": True, "OFF": False, "OK": "OK", "NG": "NG", "NONE": None, "True": True, "False": False, "None": None}
_ALLOWED_BUILTINS = {"abs": abs, "min": min, "max": max, "len": len, "round": round}
_ALLOWED_NODE_TYPES = (
    ast.Module, ast.If, ast.Expr, ast.Assign, ast.Name, ast.Load, ast.Store, ast.Constant,
    ast.Attribute, ast.Call, ast.keyword, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.BinOp,
    ast.And, ast.Or, ast.Not, ast.USub, ast.UAdd, ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.Mod, ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Pass,
)


def attribute_path(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def validate_script(script: str) -> list[AutomationValidationIssue]:
    try:
        tree = ast.parse(script or "pass", mode="exec")
    except SyntaxError as exc:
        return [AutomationValidationIssue(line=exc.lineno or 1, column=exc.offset or 0, message=exc.msg)]
    issues: list[AutomationValidationIssue] = []
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            issues.append(AutomationValidationIssue(line=getattr(node, "lineno", 1), column=getattr(node, "col_offset", 0), message=f"Unsupported syntax: {type(node).__name__}"))
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            issues.append(AutomationValidationIssue(line=node.lineno, column=node.col_offset, message="Private/dunder names are not allowed"))
        if isinstance(node, ast.keyword) and node.arg is None:
            issues.append(AutomationValidationIssue(line=getattr(node, "lineno", 1), column=getattr(node, "col_offset", 0), message="Keyword splat (**kwargs) is not allowed"))
    return issues


@dataclass
class AutomationExecutionContext:
    program: VisionProgramDefinition
    snapshot: VisionRunSnapshot | None
    event: dict[str, Any]
    read_endpoint: Callable[[str], Any]
    write_endpoint: Callable[[str, Any, bool], Any]
    call_action: Callable[[str, list[Any], dict[str, Any], bool], Any]
    trace: Callable[[AutomationTraceEntry], None]
    dry_run: bool = False


class SafeAutomationInterpreter:
    def __init__(self, context: AutomationExecutionContext, service: AutomationServiceDefinition) -> None:
        self.ctx = context
        self.service = service
        self.local_trace: list[AutomationTraceEntry] = []

    def _trace(self, message: str, *, endpoint: str = "", value: Any = None, level: str = "info") -> None:
        entry = AutomationTraceEntry(service_id=self.service.service_id, service_name=self.service.name, phase="dry_run" if self.ctx.dry_run else "runtime", level=level, message=message, endpoint=endpoint, value=value, dry_run=self.ctx.dry_run)
        self.local_trace.append(entry)
        self.ctx.trace(entry)

    def execute(self, script: str) -> AutomationExecutionResult:
        issues = validate_script(script)
        if issues:
            return AutomationExecutionResult(ok=False, service_id=self.service.service_id, dry_run=self.ctx.dry_run, issues=issues, trace=self.local_trace)
        tree = ast.parse(script or "pass", mode="exec")
        try:
            for stmt in tree.body:
                self._stmt(stmt)
            return AutomationExecutionResult(ok=True, service_id=self.service.service_id, dry_run=self.ctx.dry_run, trace=self.local_trace)
        except Exception as exc:
            self._trace(str(exc), level="error")
            return AutomationExecutionResult(ok=False, service_id=self.service.service_id, dry_run=self.ctx.dry_run, issues=[AutomationValidationIssue(message=str(exc))], trace=self.local_trace)

    def _stmt(self, node: ast.stmt) -> None:
        if isinstance(node, ast.Pass):
            return
        if isinstance(node, ast.If):
            branch = node.body if bool(self._expr(node.test)) else node.orelse
            for stmt in branch:
                self._stmt(stmt)
            return
        if isinstance(node, ast.Expr):
            self._expr(node.value)
            return
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                raise ValueError("Only one assignment target is allowed")
            path = attribute_path(node.targets[0])
            if not path:
                raise ValueError("Assignments are only allowed to writable endpoints such as device.modbus_1.Y1")
            value = self._expr(node.value)
            self.ctx.write_endpoint(path, value, self.ctx.dry_run)
            self._trace("Write endpoint", endpoint=path, value=value)
            return
        raise ValueError(f"Unsupported statement: {type(node).__name__}")

    def _expr(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_CONST_NAMES:
                return _ALLOWED_CONST_NAMES[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Attribute):
            path = attribute_path(node)
            if not path:
                raise ValueError("Unsupported attribute expression")
            return self.ctx.read_endpoint(path)
        if isinstance(node, ast.Call):
            path = attribute_path(node.func)
            args = [self._expr(item) for item in node.args]
            kwargs = {item.arg: self._expr(item.value) for item in node.keywords if item.arg}
            if path:
                value = self.ctx.call_action(path, args, kwargs, self.ctx.dry_run)
                self._trace("Call action", endpoint=path, value={"args": args, "kwargs": kwargs})
                return value
            if isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_BUILTINS:
                if kwargs:
                    raise ValueError("Safe helper functions do not accept named arguments")
                return _ALLOWED_BUILTINS[node.func.id](*args)
            raise ValueError("Only registered endpoint actions and safe helper functions may be called")
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value = True
                for item in node.values:
                    value = self._expr(item)
                    if not value:
                        return value
                return value
            for item in node.values:
                value = self._expr(item)
                if value:
                    return value
            return value if node.values else False
        if isinstance(node, ast.UnaryOp):
            value = self._expr(node.operand)
            if isinstance(node.op, ast.Not): return not value
            if isinstance(node.op, ast.USub): return -value
            if isinstance(node.op, ast.UAdd): return +value
        if isinstance(node, ast.BinOp):
            left, right = self._expr(node.left), self._expr(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.Mod): return left % right
        if isinstance(node, ast.Compare):
            left = self._expr(node.left)
            for op, comp in zip(node.ops, node.comparators):
                right = self._expr(comp)
                ok = (
                    left == right if isinstance(op, ast.Eq) else
                    left != right if isinstance(op, ast.NotEq) else
                    left > right if isinstance(op, ast.Gt) else
                    left >= right if isinstance(op, ast.GtE) else
                    left < right if isinstance(op, ast.Lt) else
                    left <= right if isinstance(op, ast.LtE) else False
                )
                if not ok: return False
                left = right
            return True
        raise ValueError(f"Unsupported expression: {type(node).__name__}")

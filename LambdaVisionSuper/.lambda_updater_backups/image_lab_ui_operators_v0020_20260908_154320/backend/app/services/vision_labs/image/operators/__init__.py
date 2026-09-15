_LOADED = False


def load_builtin_operators() -> None:
    global _LOADED
    if _LOADED:
        return
    from . import builtins  # noqa: F401
    _LOADED = True


__all__ = ["load_builtin_operators"]

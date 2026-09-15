_LOADED = False


def load_builtin_operators() -> None:
    global _LOADED
    if _LOADED:
        return
    from . import builtins  # noqa: F401
    from . import basic_families  # noqa: F401
    from . import advanced_families  # noqa: F401
    from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY

    # Image Processing LAB is intentionally single-raster processing only.
    # Legacy/multi-image IDs stay registered for saved-pipeline compatibility.
    IMAGE_OPERATOR_REGISTRY.hide_from_catalog(
        "image.arithmetic.absdiff",
        "image.arithmetic.weighted_blend",
        "image.arithmetic.bitwise_and",
    )
    _LOADED = True


__all__ = ["load_builtin_operators"]

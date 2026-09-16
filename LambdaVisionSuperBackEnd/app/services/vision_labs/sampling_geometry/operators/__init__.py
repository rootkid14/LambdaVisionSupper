_LOADED = False


def load_sampling_geometry_operators() -> None:
    global _LOADED
    if _LOADED:
        return
    from . import geometry  # noqa: F401
    from . import spatial  # noqa: F401
    from . import spectral  # noqa: F401
    _LOADED = True


__all__ = ["load_sampling_geometry_operators"]

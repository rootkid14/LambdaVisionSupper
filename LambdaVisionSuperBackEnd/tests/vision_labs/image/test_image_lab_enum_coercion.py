from app.services.vision_labs.core import EnumParam
from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY


def test_numeric_enum_coerces_string_to_declared_choice_type():
    spec = EnumParam((1, 3, 5, 7), default=3)
    value = spec.validate("5")
    assert value == 5
    assert isinstance(value, int)


def test_edge_operator_accepts_numeric_enum_from_html_select():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.edge.sobel_x")
    resolved = definition.operator_class.resolve_parameters({"kernel_size": "5"})
    assert resolved["kernel_size"] == 5
    assert isinstance(resolved["kernel_size"], int)


def test_canny_aperture_accepts_numeric_enum_from_html_select():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.edge.canny")
    resolved = definition.operator_class.resolve_parameters({"aperture": "7"})
    assert resolved["aperture"] == 7

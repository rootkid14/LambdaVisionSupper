from typing import Any, Dict
from pydantic import BaseModel, Field, ConfigDict
import cv2
import numpy as np

from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import (
    NodeType,
    UIDataType,
    UIConfigField,
    UIConfigType,
)
from app.services.utils.image_utils import bytes_to_cv2, cv2_to_base64


class GenerateCharucoBoardInput(BaseModel):
    """Node không cần dữ liệu hình ảnh đầu vào; execute_in chỉ điều khiển luồng chạy."""
    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )


class GenerateCharucoBoardOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    board_image_base64: str = Field(
        ...,
        title="Board Image Base64",
        description=UIDataType.BASE64.value,
    )
    board_info_json: Dict[str, Any] = Field(
        ...,
        title="Board Info JSON",
        description=UIDataType.JSON.value,
    )
    execute_out: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )


@registry_node
class GenerateCharucoBoardNode(
    BaseNode[GenerateCharucoBoardInput, GenerateCharucoBoardOutput]
):
    """
    Sinh ảnh ChArUco board dạng uint8 grayscale.

    Lưu ý:
    - square_length_mm và marker_length_mm mô tả kích thước vật lý.
    - dpi chỉ quyết định số pixel dùng để render ảnh.
    - Khi in phải chọn 100% / Actual Size, không dùng Fit to Page.
    """

    INPUT_SCHEMA = GenerateCharucoBoardInput
    OUTPUT_SCHEMA = GenerateCharucoBoardOutput
    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "Generate ChArUco Board"
    UI_DESCRIPTION = "Generate a printable ChArUco calibration board"
    UI_COLOR = "bg-cyan-600"

    # Render board ở 600 DPI có thể mất hơn timeout mặc định 1 giây.
    NODE_TIMEOUT = 5.0

    CONFIG_FIELDS = [
        UIConfigField(
            id="squares_x",
            label="Squares X",
            type=UIConfigType.NUMBER.value,
            default=7,
        ),
        UIConfigField(
            id="squares_y",
            label="Squares Y",
            type=UIConfigType.NUMBER.value,
            default=5,
        ),
        UIConfigField(
            id="square_length_mm",
            label="Square Length (mm)",
            type=UIConfigType.NUMBER.value,
            default=28.0,
        ),
        UIConfigField(
            id="marker_length_mm",
            label="Marker Length (mm)",
            type=UIConfigType.NUMBER.value,
            default=20.0,
        ),
        UIConfigField(
            id="dictionary",
            label="ArUco Dictionary",
            type=UIConfigType.SELECT.value,
            default="DICT_5X5_100",
            options=[
                "DICT_4X4_50",
                "DICT_4X4_100",
                "DICT_5X5_50",
                "DICT_5X5_100",
                "DICT_5X5_250",
                "DICT_6X6_100",
                "DICT_6X6_250",
                "DICT_7X7_250",
                "DICT_ARUCO_ORIGINAL",
            ],
        ),
        UIConfigField(
            id="dpi",
            label="Render DPI",
            type=UIConfigType.NUMBER.value,
            default=600,
        ),
        UIConfigField(
            id="margin_mm",
            label="White Margin (mm)",
            type=UIConfigType.NUMBER.value,
            default=5.0,
        ),
        UIConfigField(
            id="border_bits",
            label="Marker Border Bits",
            type=UIConfigType.NUMBER.value,
            default=1,
        ),
        UIConfigField(
            id="legacy_pattern",
            label="Use Legacy Pattern",
            type=UIConfigType.CHECKBOX.value,
            default=False,
        ),
    ]

    @staticmethod
    def _mm_to_px(length_mm: float, dpi: int) -> int:
        return max(1, round(length_mm / 25.4 * dpi))

    @staticmethod
    def _resolve_dictionary(dictionary_name: str) -> int:
        dictionary_id = getattr(cv2.aruco, dictionary_name, None)
        if dictionary_id is None:
            raise ValueError(
                f"ArUco dictionary không hợp lệ hoặc OpenCV không hỗ trợ: "
                f"{dictionary_name}"
            )
        return int(dictionary_id)

    async def execute(self) -> None:
        squares_x = int(self.get_config_field_value("squares_x", 7))
        squares_y = int(self.get_config_field_value("squares_y", 5))
        square_length_mm = float(
            self.get_config_field_value("square_length_mm", 28.0)
        )
        marker_length_mm = float(
            self.get_config_field_value("marker_length_mm", 20.0)
        )
        dictionary_name = str(
            self.get_config_field_value("dictionary", "DICT_5X5_100")
        )
        dpi = int(self.get_config_field_value("dpi", 600))
        margin_mm = float(self.get_config_field_value("margin_mm", 5.0))
        border_bits = int(self.get_config_field_value("border_bits", 1))
        legacy_pattern = bool(
            self.get_config_field_value("legacy_pattern", False)
        )

        # ---------- Validate configuration ----------
        if squares_x < 2 or squares_y < 2:
            raise ValueError("squares_x và squares_y phải >= 2.")

        if square_length_mm <= 0:
            raise ValueError("square_length_mm phải > 0.")

        if not 0 < marker_length_mm < square_length_mm:
            raise ValueError(
                "marker_length_mm phải > 0 và nhỏ hơn square_length_mm."
            )

        if dpi <= 0:
            raise ValueError("dpi phải > 0.")

        if margin_mm < 0:
            raise ValueError("margin_mm không được âm.")

        if border_bits < 1:
            raise ValueError("border_bits phải >= 1.")

        dictionary_id = self._resolve_dictionary(dictionary_name)
        dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)

        # ---------- Create board ----------
        board = cv2.aruco.CharucoBoard(
            (squares_x, squares_y),
            square_length_mm,
            marker_length_mm,
            dictionary,
        )

        # Chỉ bật để tương thích với board vật lý được tạo bởi quy ước OpenCV cũ.
        if hasattr(board, "setLegacyPattern"):
            board.setLegacyPattern(legacy_pattern)
        elif legacy_pattern:
            raise RuntimeError(
                "Phiên bản OpenCV hiện tại không hỗ trợ setLegacyPattern()."
            )

        board_width_mm = squares_x * square_length_mm
        board_height_mm = squares_y * square_length_mm
        image_width_mm = board_width_mm + 2.0 * margin_mm
        image_height_mm = board_height_mm + 2.0 * margin_mm

        # Render riêng phần board với đúng aspect ratio vật lý.
        # Không truyền margin trực tiếp vào generateImage vì ở một số kích thước,
        # OpenCV 4.13 có thể làm tròn ROI nội bộ và vượt khỏi ảnh đích.
        board_width_px = self._mm_to_px(board_width_mm, dpi)
        board_height_px = self._mm_to_px(board_height_mm, dpi)
        margin_px = self._mm_to_px(margin_mm, dpi) if margin_mm > 0 else 0

        board_core = board.generateImage(
            outSize=(board_width_px, board_height_px),
            marginSize=0,
            borderBits=border_bits,
        )

        # Thêm viền trắng bằng copyMakeBorder để tránh lỗi ROI của generateImage.
        if margin_px > 0:
            board_image = cv2.copyMakeBorder(
                board_core,
                top=margin_px,
                bottom=margin_px,
                left=margin_px,
                right=margin_px,
                borderType=cv2.BORDER_CONSTANT,
                value=255,
            )
        else:
            board_image = board_core

        image_height_px, image_width_px = board_image.shape[:2]

        # Đảm bảo ảnh liên tục trong bộ nhớ
        board_image = np.ascontiguousarray(board_image, dtype=np.uint8)

        board_image_base64 = cv2_to_base64(board_image)

        if not board_image_base64:
            raise RuntimeError("Không thể chuyển ChArUco board sang Base64.")

        marker_ids = board.getIds()
        marker_count = 0 if marker_ids is None else int(len(marker_ids))

        board_info = {
            "board_type": "charuco",
            "opencv_version": cv2.__version__,
            "squares_x": squares_x,
            "squares_y": squares_y,
            "charuco_corner_count": (squares_x - 1) * (squares_y - 1),
            "marker_count": marker_count,
            "square_length_mm": square_length_mm,
            "marker_length_mm": marker_length_mm,
            "marker_to_square_ratio": marker_length_mm / square_length_mm,
            "dictionary": dictionary_name,
            "dictionary_id": dictionary_id,
            "board_width_mm": board_width_mm,
            "board_height_mm": board_height_mm,
            "margin_mm": margin_mm,
            "print_width_mm": image_width_mm,
            "print_height_mm": image_height_mm,
            "dpi": dpi,
            "image_width_px": image_width_px,
            "image_height_px": image_height_px,
            "border_bits": border_bits,
            "legacy_pattern": legacy_pattern,
            "print_instruction": (
                "Print at 100% / Actual Size; disable Fit to Page."
            ),
        }

        self.local_output = self.OUTPUT_SCHEMA(
            board_image_base64=board_image_base64,
            board_info_json=board_info,
            execute_out="GO",
        )

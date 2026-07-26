from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import json
import math

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import (
    NodeType,
    UIConfigField,
    UIConfigType,
    UIDataType,
)


# =============================================================================
# INPUT / OUTPUT
# =============================================================================

class CalibrateCharucoIntrinsicsInput(BaseModel):
    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )

    calib_folder_path: str = Field(
        ...,
        title="Calibration Dataset Folder",
        description=UIDataType.STRING.value,
    )

    val_folder_path: str = Field(
        ...,
        title="Validation Dataset Folder",
        description=UIDataType.STRING.value,
    )

    board_info_json: Dict[str, Any] = Field(
        ...,
        title="ChArUco Board Config",
        description=UIDataType.JSON.value,
    )


class CalibrateCharucoIntrinsicsOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    calibration_success: bool = Field(
        ...,
        title="Calibration Success",
        description=UIDataType.BOOLEAN.value,
    )

    validation_passed: bool = Field(
        ...,
        title="Validation Passed",
        description=UIDataType.BOOLEAN.value,
    )

    overall_success: bool = Field(
        ...,
        title="Overall Success",
        description=UIDataType.BOOLEAN.value,
    )

    report_file_path: str = Field(
        ...,
        title="Calibration Report TXT",
        description=UIDataType.STRING.value,
    )

    debug_folder_path: str = Field(
        default="",
        title="Calibration Debug Image Folder",
        description=UIDataType.STRING.value,
    )

    calibration_result_json: Dict[str, Any] = Field(
        ...,
        title="Calibration Result JSON",
        description=UIDataType.JSON.value,
    )

    execute_success: Any = Field(
        default="GO",
        title="success",
        description=UIDataType.EXECUTE.value,
    )

    execute_failed: Any = Field(
        default="GO",
        title="failed",
        description=UIDataType.EXECUTE.value,
    )


# =============================================================================
# NODE
# =============================================================================

@registry_node
class CalibrateCharucoIntrinsicsFromDatasetNode(
    BaseNode[
        CalibrateCharucoIntrinsicsInput,
        CalibrateCharucoIntrinsicsOutput,
    ]
):
    """
    Intrinsic calibration từ hai dataset:

    calib_folder_path:
        Ảnh dùng để tìm camera matrix K và distortion D.

    val_folder_path:
        Ảnh độc lập dùng để kiểm tra reprojection error sau calibration.

    board_info_json:
        JSON do GenerateCharucoBoardNode sinh ra.

    Auto Error Fix:
        Loại calibration view có reprojection error bất thường, calibration
        lại và giữ candidate có validation error tốt nhất.
    """

    INPUT_SCHEMA = CalibrateCharucoIntrinsicsInput
    OUTPUT_SCHEMA = CalibrateCharucoIntrinsicsOutput

    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "Calibrate ChArUco Intrinsics"
    UI_DESCRIPTION = (
        "Calibrate K and D from ChArUco calibration and validation datasets"
    )
    UI_COLOR = "bg-emerald-600"

    # Dataset ảnh lớn có thể cần nhiều thời gian.
    NODE_TIMEOUT = 300.0

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    CONFIG_FIELDS = [
        UIConfigField(
            id="output_folder",
            label="Output Folder (empty = automatic)",
            type=UIConfigType.TEXT.value,
            default="",
        ),

        # ---------------------------------------------------------------------
        # Printed-board dimensions
        # ---------------------------------------------------------------------

        UIConfigField(
            id="physical_size_mode",
            label="Printed Board Size Source",
            type=UIConfigType.SELECT.value,
            default="FROM_BOARD_CONFIG",
            options=[
                "FROM_BOARD_CONFIG",
                "MEASURED_BOARD_SIZE",
                "MANUAL_LENGTHS",
            ],
        ),
        UIConfigField(
            id="measured_board_width_mm",
            label="Measured Chessboard Width (mm)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
        UIConfigField(
            id="measured_board_height_mm",
            label="Measured Chessboard Height (mm)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
        UIConfigField(
            id="manual_square_length_mm",
            label="Manual Square Length (mm)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
        UIConfigField(
            id="manual_marker_length_mm",
            label="Manual Marker Length (mm)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
        UIConfigField(
            id="max_print_anisotropy_percent",
            label="Maximum X/Y Print Difference (%)",
            type=UIConfigType.NUMBER.value,
            default=0.5,
        ),

        # ---------------------------------------------------------------------
        # Image acceptance
        # ---------------------------------------------------------------------

        UIConfigField(
            id="min_valid_calib_images",
            label="Minimum Valid Calibration Images",
            type=UIConfigType.NUMBER.value,
            default=10,
        ),
        UIConfigField(
            id="min_valid_val_images",
            label="Minimum Valid Validation Images",
            type=UIConfigType.NUMBER.value,
            default=3,
        ),
        UIConfigField(
            id="min_marker_count",
            label="Minimum Detected Markers",
            type=UIConfigType.NUMBER.value,
            default=4,
        ),
        UIConfigField(
            id="min_charuco_corners",
            label="Minimum ChArUco Corners",
            type=UIConfigType.NUMBER.value,
            default=12,
        ),
        UIConfigField(
            id="min_corner_ratio",
            label="Minimum Corner Ratio",
            type=UIConfigType.NUMBER.value,
            default=0.30,
        ),
        UIConfigField(
            id="min_sharpness",
            label="Minimum Sharpness",
            type=UIConfigType.NUMBER.value,
            default=80.0,
        ),
        UIConfigField(
            id="min_coverage_ratio",
            label="Minimum Board Coverage",
            type=UIConfigType.NUMBER.value,
            default=0.03,
        ),

        # ---------------------------------------------------------------------
        # Calibration model
        # ---------------------------------------------------------------------

        UIConfigField(
            id="distortion_model",
            label="Distortion Model",
            type=UIConfigType.SELECT.value,
            default="STANDARD_5",
            options=[
                "STANDARD_5",
                "RATIONAL_8",
            ],
        ),
        UIConfigField(
            id="zero_tangent_distortion",
            label="Force Tangential Distortion to Zero",
            type=UIConfigType.SELECT.value,
            default="False",
            options=[
                "True",
                "False",
            ],
        ),

        # ---------------------------------------------------------------------
        # Validation
        # ---------------------------------------------------------------------

        UIConfigField(
            id="max_validation_mean_error_px",
            label="Maximum Validation Mean Error (px)",
            type=UIConfigType.NUMBER.value,
            default=0.8,
        ),
        UIConfigField(
            id="max_validation_view_error_px",
            label="Maximum Validation Image Error (px)",
            type=UIConfigType.NUMBER.value,
            default=1.5,
        ),

        # ---------------------------------------------------------------------
        # Automatic outlier correction
        # ---------------------------------------------------------------------

        UIConfigField(
            id="enable_error_fix",
            label="Enable Automatic Error Fix",
            type=UIConfigType.SELECT.value,
            default="True",
            options=[
                "True",
                "False",
            ],
        ),
        UIConfigField(
            id="max_fix_iterations",
            label="Maximum Error Fix Iterations",
            type=UIConfigType.NUMBER.value,
            default=3,
        ),
        UIConfigField(
            id="outlier_robust_factor",
            label="Outlier Robust Factor (Median / MAD)",
            type=UIConfigType.NUMBER.value,
            default=2.5,
        ),
        UIConfigField(
            id="absolute_outlier_error_px",
            label="Minimum Absolute Outlier Error (px)",
            type=UIConfigType.NUMBER.value,
            default=1.0,
        ),
        UIConfigField(
            id="max_outliers_per_iteration",
            label="Maximum Removed Images per Iteration",
            type=UIConfigType.NUMBER.value,
            default=2,
        ),
        UIConfigField(
            id="max_total_removal_fraction",
            label="Maximum Total Removal Fraction",
            type=UIConfigType.NUMBER.value,
            default=0.25,
        ),

        # ---------------------------------------------------------------------
        # Debug-image export
        # ---------------------------------------------------------------------

        UIConfigField(
            id="enable_debug_images",
            label="Save Calibration Debug Images",
            type=UIConfigType.SELECT.value,
            default="True",
            options=[
                "True",
                "False",
            ],
        ),
        UIConfigField(
            id="debug_save_rejected_images",
            label="Save Rejected Dataset Images",
            type=UIConfigType.SELECT.value,
            default="True",
            options=[
                "True",
                "False",
            ],
        ),
        UIConfigField(
            id="debug_image_format",
            label="Debug Image Format",
            type=UIConfigType.SELECT.value,
            default="PNG",
            options=[
                "PNG",
                "JPG",
            ],
        ),
        UIConfigField(
            id="debug_axis_length_mm",
            label="Debug Board Axis Length (mm, 0 = automatic)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
    ]

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _as_bool(value: Any) -> bool:
        """
        Convert Boolean-compatible values to bool.

        UI Boolean configuration fields are represented by SELECT controls and
        therefore normally arrive as the strings "True" or "False".
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return bool(value)

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {
                "1",
                "true",
                "yes",
                "on",
                "enabled",
            }:
                return True

            if normalized in {
                "",
                "0",
                "false",
                "no",
                "off",
                "disabled",
            }:
                return False

            raise ValueError(
                f"Invalid Boolean string: {value!r}. "
                "Expected 'True' or 'False'."
            )

        return bool(value)

    @staticmethod
    def _as_float(value: Any, name: str) -> float:
        result = float(value)

        if not math.isfinite(result):
            raise ValueError(f"{name} must be a finite number.")

        return result

    @classmethod
    def _json_safe(cls, value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return value.tolist()

        if isinstance(value, np.floating):
            return float(value)

        if isinstance(value, np.integer):
            return int(value)

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, dict):
            return {
                str(key): cls._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [cls._json_safe(item) for item in value]

        return value

    @classmethod
    def _list_images(cls, folder: Path) -> List[Path]:
        return sorted(
            [
                path
                for path in folder.iterdir()
                if path.is_file()
                and path.suffix.lower() in cls.IMAGE_EXTENSIONS
            ],
            key=lambda path: path.name.lower(),
        )

    # =========================================================================
    # Board creation and print-size override
    # =========================================================================

    def _create_board(
        self,
        board_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        required = [
            "squares_x",
            "squares_y",
            "square_length_mm",
            "marker_length_mm",
            "dictionary",
        ]

        missing = [key for key in required if key not in board_info]

        if missing:
            raise ValueError(
                "board_info_json is missing: " + ", ".join(missing)
            )

        squares_x = int(board_info["squares_x"])
        squares_y = int(board_info["squares_y"])

        design_square = self._as_float(
            board_info["square_length_mm"],
            "square_length_mm",
        )
        design_marker = self._as_float(
            board_info["marker_length_mm"],
            "marker_length_mm",
        )

        dictionary_name = str(board_info["dictionary"])
        legacy_pattern = self._as_bool(
            board_info.get("legacy_pattern", False)
        )

        if squares_x < 2 or squares_y < 2:
            raise ValueError("Board must contain at least 2 x 2 squares.")

        if design_square <= 0:
            raise ValueError("square_length_mm must be greater than zero.")

        if not 0 < design_marker < design_square:
            raise ValueError(
                "marker_length_mm must be smaller than square_length_mm."
            )

        physical_size_mode = str(
            self.get_config_field_value(
                "physical_size_mode",
                "FROM_BOARD_CONFIG",
            )
        ).strip().upper()

        square_length = design_square
        marker_length = design_marker

        scale_x = 1.0
        scale_y = 1.0
        anisotropy_percent = 0.0

        if physical_size_mode == "MEASURED_BOARD_SIZE":
            measured_width = self._as_float(
                self.get_config_field_value(
                    "measured_board_width_mm",
                    0.0,
                ),
                "measured_board_width_mm",
            )
            measured_height = self._as_float(
                self.get_config_field_value(
                    "measured_board_height_mm",
                    0.0,
                ),
                "measured_board_height_mm",
            )

            if measured_width <= 0 or measured_height <= 0:
                raise ValueError(
                    "Measured board width and height must be greater than zero."
                )

            design_width = squares_x * design_square
            design_height = squares_y * design_square

            scale_x = measured_width / design_width
            scale_y = measured_height / design_height

            uniform_scale = (scale_x + scale_y) / 2.0

            anisotropy_percent = (
                abs(scale_x - scale_y)
                / uniform_scale
                * 100.0
            )

            allowed_anisotropy = self._as_float(
                self.get_config_field_value(
                    "max_print_anisotropy_percent",
                    0.5,
                ),
                "max_print_anisotropy_percent",
            )

            if anisotropy_percent > allowed_anisotropy:
                raise ValueError(
                    "NON_UNIFORM_PRINT_SCALE: "
                    f"X/Y difference is {anisotropy_percent:.6f}%, "
                    f"allowed maximum is {allowed_anisotropy:.6f}%. "
                    "The board should be printed again."
                )

            square_length = design_square * uniform_scale
            marker_length = design_marker * uniform_scale

        elif physical_size_mode == "MANUAL_LENGTHS":
            square_length = self._as_float(
                self.get_config_field_value(
                    "manual_square_length_mm",
                    0.0,
                ),
                "manual_square_length_mm",
            )
            marker_length = self._as_float(
                self.get_config_field_value(
                    "manual_marker_length_mm",
                    0.0,
                ),
                "manual_marker_length_mm",
            )

            if square_length <= 0:
                raise ValueError(
                    "manual_square_length_mm must be greater than zero."
                )

            if not 0 < marker_length < square_length:
                raise ValueError(
                    "manual_marker_length_mm must be smaller than "
                    "manual_square_length_mm."
                )

        elif physical_size_mode != "FROM_BOARD_CONFIG":
            raise ValueError(
                f"Unknown physical_size_mode: {physical_size_mode}"
            )

        dictionary_id = getattr(
            cv2.aruco,
            dictionary_name,
            None,
        )

        if dictionary_id is None:
            raise ValueError(
                f"Unsupported ArUco dictionary: {dictionary_name}"
            )

        dictionary = cv2.aruco.getPredefinedDictionary(
            int(dictionary_id)
        )

        board = cv2.aruco.CharucoBoard(
            (squares_x, squares_y),
            float(square_length),
            float(marker_length),
            dictionary,
        )

        if hasattr(board, "setLegacyPattern"):
            board.setLegacyPattern(legacy_pattern)
        elif legacy_pattern:
            raise RuntimeError(
                "Current OpenCV version does not support legacy patterns."
            )

        object_corner_table = np.asarray(
            board.getChessboardCorners(),
            dtype=np.float32,
        ).reshape(-1, 3)

        return {
            "board": board,
            "dictionary": dictionary,
            "dictionary_name": dictionary_name,
            "dictionary_id": int(dictionary_id),
            "squares_x": squares_x,
            "squares_y": squares_y,
            "expected_corner_count": (
                squares_x - 1
            ) * (
                squares_y - 1
            ),
            "square_length_mm": square_length,
            "marker_length_mm": marker_length,
            "legacy_pattern": legacy_pattern,
            "object_corner_table": object_corner_table,
            "print_geometry": {
                "physical_size_mode": physical_size_mode,
                "design_square_length_mm": design_square,
                "design_marker_length_mm": design_marker,
                "effective_square_length_mm": square_length,
                "effective_marker_length_mm": marker_length,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "anisotropy_percent": anisotropy_percent,
            },
        }

    # =========================================================================
    # Detection
    # =========================================================================

    @staticmethod
    def _create_detector(board: Any) -> Any:
        detector_parameters = cv2.aruco.DetectorParameters()

        if hasattr(detector_parameters, "cornerRefinementMethod"):
            detector_parameters.cornerRefinementMethod = (
                cv2.aruco.CORNER_REFINE_SUBPIX
            )

        charuco_parameters = cv2.aruco.CharucoParameters()

        if hasattr(charuco_parameters, "minMarkers"):
            charuco_parameters.minMarkers = 2

        if hasattr(charuco_parameters, "tryRefineMarkers"):
            charuco_parameters.tryRefineMarkers = True

        return cv2.aruco.CharucoDetector(
            board,
            charuco_parameters,
            detector_parameters,
        )

    def _detect_image(
        self,
        path: Path,
        role: str,
        board_data: Dict[str, Any],
        detector: Any,
        required_size: Tuple[int, int],
    ) -> Dict[str, Any]:
        record: Dict[str, Any] = {
            "path": str(path.resolve()),
            "filename": path.name,
            "role": role,
            "accepted": False,
            "reasons": [],
            "warnings": [],
            "marker_count": 0,
            "charuco_corner_count": 0,
            "corner_ratio": 0.0,
            "sharpness": 0.0,
            "coverage_ratio": 0.0,
            "image_size": None,
            "image_points": None,
            "object_points": None,
            "charuco_ids": None,
            "marker_corners": None,
            "marker_ids": None,
        }

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None or image.size == 0:
            record["reasons"].append("IMAGE_UNREADABLE")
            return record

        height, width = image.shape[:2]
        image_size = (int(width), int(height))

        record["image_size"] = image_size

        if image_size != required_size:
            record["reasons"].append(
                f"IMAGE_SIZE_MISMATCH: {image_size} != {required_size}"
            )
            return record

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        record["sharpness"] = float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

        (
            charuco_corners,
            charuco_ids,
            marker_corners,
            marker_ids,
        ) = detector.detectBoard(gray)

        record["marker_count"] = (
            0 if marker_ids is None else int(len(marker_ids))
        )

        record["marker_corners"] = (
            None
            if marker_corners is None
            else [
                np.asarray(
                    corners,
                    dtype=np.float32,
                ).reshape(1, 4, 2)
                for corners in marker_corners
            ]
        )

        record["marker_ids"] = (
            None
            if marker_ids is None
            else np.asarray(
                marker_ids,
                dtype=np.int32,
            ).reshape(-1, 1)
        )

        if charuco_corners is None or charuco_ids is None:
            record["reasons"].append("CHARUCO_CORNERS_NOT_FOUND")

            if record["marker_count"] == 0:
                record["reasons"].append("ARUCO_MARKERS_NOT_FOUND")

            return record

        image_points = np.asarray(
            charuco_corners,
            dtype=np.float32,
        ).reshape(-1, 1, 2)

        ids = np.asarray(
            charuco_ids,
            dtype=np.int32,
        ).reshape(-1, 1)

        valid_ids = (
            (ids.reshape(-1) >= 0)
            & (
                ids.reshape(-1)
                < len(board_data["object_corner_table"])
            )
        )

        if not np.all(valid_ids):
            image_points = image_points[valid_ids]
            ids = ids[valid_ids]
            record["warnings"].append(
                "INVALID_CHARUCO_IDS_REMOVED"
            )

        corner_count = int(len(ids))
        expected_count = int(
            board_data["expected_corner_count"]
        )

        record["charuco_corner_count"] = corner_count
        record["corner_ratio"] = (
            corner_count / expected_count
            if expected_count > 0
            else 0.0
        )

        if corner_count >= 3:
            hull = cv2.convexHull(
                image_points.reshape(-1, 2)
            )

            record["coverage_ratio"] = float(
                cv2.contourArea(hull)
                / float(width * height)
            )

        try:
            collinear = bool(
                board_data["board"].checkCharucoCornersCollinear(
                    ids
                )
            )
        except Exception:
            collinear = False
            record["warnings"].append(
                "COLLINEARITY_CHECK_UNAVAILABLE"
            )

        object_points = board_data["object_corner_table"][
            ids.reshape(-1)
        ].reshape(-1, 1, 3).astype(np.float32)

        record["image_points"] = image_points
        record["object_points"] = object_points
        record["charuco_ids"] = ids

        min_markers = int(
            self.get_config_field_value(
                "min_marker_count",
                4,
            )
        )
        min_corners = int(
            self.get_config_field_value(
                "min_charuco_corners",
                12,
            )
        )
        min_corner_ratio = self._as_float(
            self.get_config_field_value(
                "min_corner_ratio",
                0.30,
            ),
            "min_corner_ratio",
        )
        min_sharpness = self._as_float(
            self.get_config_field_value(
                "min_sharpness",
                80.0,
            ),
            "min_sharpness",
        )
        min_coverage = self._as_float(
            self.get_config_field_value(
                "min_coverage_ratio",
                0.03,
            ),
            "min_coverage_ratio",
        )

        if record["marker_count"] < min_markers:
            record["reasons"].append(
                f"INSUFFICIENT_MARKERS: "
                f"{record['marker_count']} < {min_markers}"
            )

        if corner_count < min_corners:
            record["reasons"].append(
                f"INSUFFICIENT_CHARUCO_CORNERS: "
                f"{corner_count} < {min_corners}"
            )

        if record["corner_ratio"] < min_corner_ratio:
            record["reasons"].append(
                f"LOW_CORNER_RATIO: "
                f"{record['corner_ratio']:.6f} < "
                f"{min_corner_ratio:.6f}"
            )

        if record["sharpness"] < min_sharpness:
            record["reasons"].append(
                f"IMAGE_BLURRED: "
                f"{record['sharpness']:.6f} < "
                f"{min_sharpness:.6f}"
            )

        if record["coverage_ratio"] < min_coverage:
            record["reasons"].append(
                f"BOARD_TOO_SMALL: "
                f"{record['coverage_ratio']:.6f} < "
                f"{min_coverage:.6f}"
            )

        if collinear:
            record["reasons"].append(
                "CHARUCO_CORNERS_COLLINEAR"
            )

        record["accepted"] = len(record["reasons"]) == 0

        return record

    # =========================================================================
    # Calibration
    # =========================================================================

    def _calibration_flags(self) -> int:
        flags = 0

        model = str(
            self.get_config_field_value(
                "distortion_model",
                "STANDARD_5",
            )
        ).strip().upper()

        if model == "RATIONAL_8":
            flags |= cv2.CALIB_RATIONAL_MODEL
        elif model != "STANDARD_5":
            raise ValueError(
                f"Unknown distortion model: {model}"
            )

        if self._as_bool(
            self.get_config_field_value(
                "zero_tangent_distortion",
                "False",
            )
        ):
            flags |= cv2.CALIB_ZERO_TANGENT_DIST

        return flags

    @staticmethod
    def _calculate_per_view_errors(
        object_points: Sequence[np.ndarray],
        image_points: Sequence[np.ndarray],
        rvecs: Sequence[np.ndarray],
        tvecs: Sequence[np.ndarray],
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
    ) -> List[float]:
        errors: List[float] = []

        for obj, img, rvec, tvec in zip(
            object_points,
            image_points,
            rvecs,
            tvecs,
        ):
            projected, _ = cv2.projectPoints(
                obj,
                rvec,
                tvec,
                camera_matrix,
                dist_coeffs,
            )

            residual = (
                img.reshape(-1, 2).astype(np.float64)
                - projected.reshape(-1, 2).astype(np.float64)
            )

            rmse = np.sqrt(
                np.mean(
                    np.sum(
                        residual * residual,
                        axis=1,
                    )
                )
            )

            errors.append(float(rmse))

        return errors

    def _calibrate(
        self,
        records: Sequence[Dict[str, Any]],
        used_indices: Sequence[int],
        image_size: Tuple[int, int],
    ) -> Dict[str, Any]:
        object_points = [
            records[index]["object_points"]
            for index in used_indices
        ]

        image_points = [
            records[index]["image_points"]
            for index in used_indices
        ]

        criteria = (
            cv2.TERM_CRITERIA_EPS
            + cv2.TERM_CRITERIA_COUNT,
            100,
            1e-9,
        )

        (
            rms,
            camera_matrix,
            dist_coeffs,
            rvecs,
            tvecs,
            std_intrinsics,
            std_extrinsics,
            _,
        ) = cv2.calibrateCameraExtended(
            object_points,
            image_points,
            image_size,
            None,
            None,
            flags=self._calibration_flags(),
            criteria=criteria,
        )

        camera_matrix = np.asarray(
            camera_matrix,
            dtype=np.float64,
        )

        dist_coeffs = np.asarray(
            dist_coeffs,
            dtype=np.float64,
        )

        if (
            camera_matrix.shape != (3, 3)
            or not np.all(np.isfinite(camera_matrix))
            or not np.all(np.isfinite(dist_coeffs))
        ):
            raise RuntimeError(
                "OpenCV returned invalid calibration parameters."
            )

        per_view_errors = self._calculate_per_view_errors(
            object_points,
            image_points,
            rvecs,
            tvecs,
            camera_matrix,
            dist_coeffs,
        )

        return {
            "rms": float(rms),
            "camera_matrix": camera_matrix,
            "dist_coeffs": dist_coeffs,
            "rvecs": rvecs,
            "tvecs": tvecs,
            "std_intrinsics": std_intrinsics,
            "std_extrinsics": std_extrinsics,
            "per_view_errors": per_view_errors,
        }

    # =========================================================================
    # Independent validation
    # =========================================================================

    @staticmethod
    def _solve_pose(
        object_points: np.ndarray,
        image_points: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
    ) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        flags = []

        if hasattr(cv2, "SOLVEPNP_IPPE"):
            flags.append(cv2.SOLVEPNP_IPPE)

        flags.append(cv2.SOLVEPNP_ITERATIVE)

        for flag in flags:
            try:
                success, rvec, tvec = cv2.solvePnP(
                    object_points,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    flags=flag,
                )

                if success:
                    return True, rvec, tvec

            except cv2.error:
                continue

        return False, None, None

    def _validate(
        self,
        records: Sequence[Dict[str, Any]],
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        errors: List[float] = []
        undistorted_errors: List[float] = []

        for record in records:
            if not record["accepted"]:
                results.append(
                    {
                        "filename": record["filename"],
                        "status": "DETECTION_FAILED",
                        "reasons": record["reasons"],
                        "error_px": None,
                    }
                )
                continue

            success, rvec, tvec = self._solve_pose(
                record["object_points"],
                record["image_points"],
                camera_matrix,
                dist_coeffs,
            )

            if not success:
                results.append(
                    {
                        "filename": record["filename"],
                        "status": "POSE_ESTIMATION_FAILED",
                        "reasons": [],
                        "error_px": None,
                    }
                )
                continue

            projected, _ = cv2.projectPoints(
                record["object_points"],
                rvec,
                tvec,
                camera_matrix,
                dist_coeffs,
            )

            residual = (
                record["image_points"]
                .reshape(-1, 2)
                .astype(np.float64)
                - projected
                .reshape(-1, 2)
                .astype(np.float64)
            )

            error = float(
                np.sqrt(
                    np.mean(
                        np.sum(
                            residual * residual,
                            axis=1,
                        )
                    )
                )
            )

            # Kiểm tra trong mặt phẳng pixel sau khi loại distortion.
            undistorted_points = cv2.undistortPoints(
                record["image_points"],
                camera_matrix,
                dist_coeffs,
                P=camera_matrix,
            ).astype(np.float32)

            zero_dist = np.zeros_like(dist_coeffs)

            und_success, und_rvec, und_tvec = self._solve_pose(
                record["object_points"],
                undistorted_points,
                camera_matrix,
                zero_dist,
            )

            und_error = None

            if und_success:
                und_projected, _ = cv2.projectPoints(
                    record["object_points"],
                    und_rvec,
                    und_tvec,
                    camera_matrix,
                    zero_dist,
                )

                und_residual = (
                    undistorted_points
                    .reshape(-1, 2)
                    .astype(np.float64)
                    - und_projected
                    .reshape(-1, 2)
                    .astype(np.float64)
                )

                und_error = float(
                    np.sqrt(
                        np.mean(
                            np.sum(
                                und_residual * und_residual,
                                axis=1,
                            )
                        )
                    )
                )

                undistorted_errors.append(und_error)

            errors.append(error)

            results.append(
                {
                    "filename": record["filename"],
                    "status": "VALIDATED",
                    "error_px": error,
                    "undistorted_error_px": und_error,
                    "corner_count": record["charuco_corner_count"],
                }
            )

        min_valid_images = int(
            self.get_config_field_value(
                "min_valid_val_images",
                3,
            )
        )

        max_mean_error = self._as_float(
            self.get_config_field_value(
                "max_validation_mean_error_px",
                0.8,
            ),
            "max_validation_mean_error_px",
        )

        max_view_error = self._as_float(
            self.get_config_field_value(
                "max_validation_view_error_px",
                1.5,
            ),
            "max_validation_view_error_px",
        )

        mean_error = (
            float(np.mean(errors))
            if errors
            else None
        )

        max_error = (
            float(np.max(errors))
            if errors
            else None
        )

        mean_undistorted_error = (
            float(np.mean(undistorted_errors))
            if undistorted_errors
            else None
        )

        passed = bool(
            len(errors) >= min_valid_images
            and mean_error is not None
            and max_error is not None
            and mean_error <= max_mean_error
            and max_error <= max_view_error
        )

        return {
            "summary": {
                "total_images": len(records),
                "valid_images": len(errors),
                "minimum_valid_images": min_valid_images,
                "mean_error_px": mean_error,
                "maximum_error_px": max_error,
                "mean_undistorted_error_px": (
                    mean_undistorted_error
                ),
                "allowed_mean_error_px": max_mean_error,
                "allowed_view_error_px": max_view_error,
                "passed": passed,
            },
            "images": results,
        }

    # =========================================================================
    # Error-fix loop
    # =========================================================================

    def _run_error_fix(
        self,
        calib_records: Sequence[Dict[str, Any]],
        val_records: Sequence[Dict[str, Any]],
        image_size: Tuple[int, int],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        minimum_images = int(
            self.get_config_field_value(
                "min_valid_calib_images",
                10,
            )
        )

        if len(calib_records) < minimum_images:
            raise ValueError(
                f"INSUFFICIENT_CALIBRATION_IMAGES: "
                f"{len(calib_records)} < {minimum_images}"
            )

        enabled = self._as_bool(
            self.get_config_field_value(
                "enable_error_fix",
                "True",
            )
        )

        maximum_iterations = max(
            0,
            int(
                self.get_config_field_value(
                    "max_fix_iterations",
                    3,
                )
            ),
        )

        # Factor used by the Median/MAD robust outlier detector.
        #
        # The legacy field is used only as a migration fallback for previously
        # serialized nodes that still contain "outlier_sigma_factor".
        robust_factor_value = self.get_config_field_value(
            "outlier_robust_factor",
            None,
        )

        if robust_factor_value is None:
            robust_factor_value = self.get_config_field_value(
                "outlier_sigma_factor",
                2.5,
            )

        robust_factor = self._as_float(
            robust_factor_value,
            "outlier_robust_factor",
        )

        if robust_factor <= 0:
            raise ValueError(
                "outlier_robust_factor must be greater than zero."
            )

        absolute_threshold = self._as_float(
            self.get_config_field_value(
                "absolute_outlier_error_px",
                1.0,
            ),
            "absolute_outlier_error_px",
        )

        maximum_per_iteration = max(
            1,
            int(
                self.get_config_field_value(
                    "max_outliers_per_iteration",
                    2,
                )
            ),
        )

        maximum_fraction = self._as_float(
            self.get_config_field_value(
                "max_total_removal_fraction",
                0.25,
            ),
            "max_total_removal_fraction",
        )

        if not 0 <= maximum_fraction < 1:
            raise ValueError(
                "max_total_removal_fraction must be in [0, 1)."
            )

        maximum_total_removed = min(
            len(calib_records) - minimum_images,
            int(
                math.floor(
                    len(calib_records)
                    * maximum_fraction
                )
            ),
        )

        maximum_total_removed = max(
            0,
            maximum_total_removed,
        )

        current_indices = list(
            range(len(calib_records))
        )

        removed_indices: List[int] = []
        candidates: List[Dict[str, Any]] = []
        history: List[Dict[str, Any]] = []

        round_count = (
            maximum_iterations + 1
            if enabled
            else 1
        )

        for iteration in range(round_count):
            calibration = self._calibrate(
                calib_records,
                current_indices,
                image_size,
            )

            validation = self._validate(
                val_records,
                calibration["camera_matrix"],
                calibration["dist_coeffs"],
            )

            valid_val_count = int(
                validation["summary"]["valid_images"]
            )

            minimum_val_count = int(
                self.get_config_field_value(
                    "min_valid_val_images",
                    3,
                )
            )

            if valid_val_count >= minimum_val_count:
                score = float(
                    validation["summary"]["mean_error_px"]
                )
                score_source = "VALIDATION_MEAN_ERROR"
            else:
                score = float(calibration["rms"])
                score_source = "CALIBRATION_RMS_FALLBACK"

            candidate = {
                "iteration": iteration,
                "used_indices": list(current_indices),
                "removed_indices": list(removed_indices),
                "calibration": calibration,
                "validation": validation,
                "selection_score": score,
                "selection_score_source": score_source,
            }

            candidates.append(candidate)

            step = {
                "iteration": iteration,
                "used_image_count": len(current_indices),
                "calibration_rms_px": calibration["rms"],
                "validation_mean_error_px": (
                    validation["summary"]["mean_error_px"]
                ),
                "selection_score": score,
                "selection_score_source": score_source,
                "removed_this_iteration": [],
                "stop_reason": None,
            }

            if not enabled:
                step["stop_reason"] = "AUTO_FIX_DISABLED"
                history.append(step)
                break

            if iteration >= maximum_iterations:
                step["stop_reason"] = "MAX_ITERATIONS_REACHED"
                history.append(step)
                break

            if len(removed_indices) >= maximum_total_removed:
                step["stop_reason"] = (
                    "MAX_TOTAL_REMOVAL_REACHED"
                )
                history.append(step)
                break

            errors = np.asarray(
                calibration["per_view_errors"],
                dtype=np.float64,
            )

            # Robust center of the per-view reprojection errors.
            median_error = float(
                np.median(errors)
            )

            # Median Absolute Deviation:
            #
            # MAD = median(|error_i - median_error|)
            mad = float(
                np.median(
                    np.abs(
                        errors - median_error
                    )
                )
            )

            # Multiplication by 1.4826 puts MAD on approximately the same scale
            # as standard deviation for normally distributed data. The
            # calculation remains robust because both its center and spread
            # are obtained from medians; np.mean() and np.std() are not used.
            scaled_mad = 1.4826 * mad

            robust_threshold = (
                median_error
                + robust_factor * scaled_mad
            )

            # Requiring the error to exceed this maximum protects against an
            # unrealistically low threshold when the dataset is extremely
            # uniform or MAD is zero.
            threshold = max(
                absolute_threshold,
                robust_threshold,
            )

            step["outlier_method"] = "MEDIAN_MAD"
            step["outlier_threshold_px"] = threshold
            step["robust_threshold_px"] = robust_threshold
            step["absolute_threshold_px"] = absolute_threshold
            step["median_error_px"] = median_error
            step["mad_px"] = mad
            step["scaled_mad_px"] = scaled_mad
            step["outlier_robust_factor"] = robust_factor

            local_outliers = [
                position
                for position, error in enumerate(errors)
                if error > threshold
            ]

            if not local_outliers:
                step["stop_reason"] = "NO_OUTLIERS_FOUND"
                history.append(step)
                break

            local_outliers.sort(
                key=lambda position: errors[position],
                reverse=True,
            )

            remaining_total_capacity = (
                maximum_total_removed
                - len(removed_indices)
            )

            remaining_minimum_capacity = (
                len(current_indices)
                - minimum_images
            )

            remove_count = min(
                maximum_per_iteration,
                len(local_outliers),
                remaining_total_capacity,
                remaining_minimum_capacity,
            )

            if remove_count <= 0:
                step["stop_reason"] = (
                    "MINIMUM_IMAGE_COUNT_PROTECTED"
                )
                history.append(step)
                break

            selected_positions = local_outliers[
                :remove_count
            ]

            selected_indices = [
                current_indices[position]
                for position in selected_positions
            ]

            step["removed_this_iteration"] = [
                {
                    "filename": (
                        calib_records[index]["filename"]
                    ),
                    "error_px": float(
                        errors[position]
                    ),
                }
                for position, index in zip(
                    selected_positions,
                    selected_indices,
                )
            ]

            selected_set = set(selected_indices)

            removed_indices.extend(selected_indices)

            current_indices = [
                index
                for index in current_indices
                if index not in selected_set
            ]

            history.append(step)

        best_candidate = min(
            candidates,
            key=lambda candidate: (
                candidate["selection_score"]
            ),
        )

        initial_score = float(
            candidates[0]["selection_score"]
        )

        final_score = float(
            best_candidate["selection_score"]
        )

        improvement = initial_score - final_score

        improvement_percent = (
            improvement / initial_score * 100.0
            if initial_score > 0
            else 0.0
        )

        fix_summary = {
            "requested": enabled,
            "outlier_method": "MEDIAN_MAD",
            "outlier_robust_factor": robust_factor,
            "absolute_outlier_error_px": absolute_threshold,
            "selected_iteration": (
                best_candidate["iteration"]
            ),
            "fix_applied": (
                best_candidate["iteration"] > 0
            ),
            "initial_score": initial_score,
            "final_score": final_score,
            "improvement": improvement,
            "improvement_percent": improvement_percent,
            "selection_score_source": (
                best_candidate[
                    "selection_score_source"
                ]
            ),
            "removed_images": [
                calib_records[index]["filename"]
                for index in best_candidate[
                    "removed_indices"
                ]
            ],
            "history": history,
        }

        return best_candidate, fix_summary

    # =========================================================================
    # TXT report
    # =========================================================================

    def _resolve_output_folder(
        self,
        calib_folder: Path,
    ) -> Path:
        configured = str(
            self.get_config_field_value(
                "output_folder",
                "",
            )
            or ""
        ).strip()

        if configured:
            output_folder = Path(
                configured
            ).expanduser()
        else:
            output_folder = (
                calib_folder.parent
                / (
                    calib_folder.name
                    + "_charuco_calibration_result"
                )
            )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_folder.resolve()

    @staticmethod
    def _public_detection_record(
        record: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            key: value
            for key, value in record.items()
            if key not in {
                "image_points",
                "object_points",
                "charuco_ids",
                "marker_corners",
                "marker_ids",
            }
        }

    # =========================================================================
    # Debug-image export
    # =========================================================================

    @staticmethod
    def _safe_debug_stem(filename: str) -> str:
        stem = Path(filename).stem

        safe = "".join(
            character
            if character.isalnum() or character in "-_."
            else "_"
            for character in stem
        ).strip("._")

        return safe or "image"

    @staticmethod
    def _draw_debug_cross(
        image: np.ndarray,
        point: Tuple[int, int],
        color: Tuple[int, int, int],
        size: int = 6,
        thickness: int = 1,
    ) -> None:
        x, y = point

        cv2.line(
            image,
            (x - size, y - size),
            (x + size, y + size),
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.line(
            image,
            (x - size, y + size),
            (x + size, y - size),
            color,
            thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def _draw_debug_text_panel(
        image: np.ndarray,
        lines: Sequence[str],
    ) -> None:
        if not lines:
            return

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.52
        thickness = 1
        line_height = 22
        padding = 8

        text_widths = [
            cv2.getTextSize(
                str(line),
                font,
                font_scale,
                thickness,
            )[0][0]
            for line in lines
        ]

        panel_width = min(
            image.shape[1],
            max(text_widths, default=300) + 2 * padding,
        )

        panel_height = min(
            image.shape[0],
            len(lines) * line_height + 2 * padding,
        )

        overlay = image.copy()

        cv2.rectangle(
            overlay,
            (0, 0),
            (panel_width, panel_height),
            (0, 0, 0),
            -1,
        )

        cv2.addWeighted(
            overlay,
            0.68,
            image,
            0.32,
            0.0,
            image,
        )

        for index, line in enumerate(lines):
            y = padding + 16 + index * line_height

            if y >= panel_height:
                break

            cv2.putText(
                image,
                str(line),
                (padding, y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

    @staticmethod
    def _encode_debug_image(
        path: Path,
        image: np.ndarray,
        image_format: str,
    ) -> None:
        normalized_format = image_format.strip().upper()

        if normalized_format == "PNG":
            suffix = ".png"
            parameters = [
                cv2.IMWRITE_PNG_COMPRESSION,
                3,
            ]
        elif normalized_format == "JPG":
            suffix = ".jpg"
            parameters = [
                cv2.IMWRITE_JPEG_QUALITY,
                95,
            ]
        else:
            raise ValueError(
                f"Unsupported debug image format: {image_format}"
            )

        if path.suffix.lower() != suffix:
            path = path.with_suffix(suffix)

        success, encoded = cv2.imencode(
            suffix,
            image,
            parameters,
        )

        if not success:
            raise RuntimeError(
                f"OpenCV failed to encode debug image: {path}"
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(
            encoded.tobytes()
        )

    def _annotate_debug_image(
        self,
        record: Dict[str, Any],
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        status: str,
        axis_length_mm: float,
        supplied_error_px: Optional[float] = None,
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        metadata: Dict[str, Any] = {
            "source_path": record.get("path"),
            "filename": record.get("filename"),
            "role": record.get("role"),
            "status": status,
            "accepted": bool(record.get("accepted")),
            "reasons": list(record.get("reasons", [])),
            "warnings": list(record.get("warnings", [])),
            "marker_count": int(
                record.get("marker_count", 0)
            ),
            "charuco_corner_count": int(
                record.get("charuco_corner_count", 0)
            ),
            "pose_found": False,
            "error_px": supplied_error_px,
        }

        image = cv2.imread(
            str(record["path"]),
            cv2.IMREAD_COLOR,
        )

        if image is None or image.size == 0:
            metadata["debug_error"] = "IMAGE_UNREADABLE"
            return None, metadata

        annotated = image.copy()

        marker_corners = record.get("marker_corners")
        marker_ids = record.get("marker_ids")

        if marker_corners:
            try:
                cv2.aruco.drawDetectedMarkers(
                    annotated,
                    marker_corners,
                    marker_ids,
                    borderColor=(255, 255, 0),
                )
            except cv2.error as error:
                metadata["warnings"].append(
                    "DRAW_MARKERS_FAILED: "
                    + str(error)
                )

        image_points = record.get("image_points")
        object_points = record.get("object_points")
        charuco_ids = record.get("charuco_ids")

        if image_points is not None and charuco_ids is not None:
            try:
                cv2.aruco.drawDetectedCornersCharuco(
                    annotated,
                    np.asarray(
                        image_points,
                        dtype=np.float32,
                    ),
                    np.asarray(
                        charuco_ids,
                        dtype=np.int32,
                    ),
                    cornerColor=(0, 255, 0),
                )
            except cv2.error as error:
                metadata["warnings"].append(
                    "DRAW_CHARUCO_CORNERS_FAILED: "
                    + str(error)
                )

        pose_success = False
        rvec = None
        tvec = None
        computed_error_px = None

        if (
            image_points is not None
            and object_points is not None
            and len(image_points) >= 4
            and len(object_points) >= 4
        ):
            pose_success, rvec, tvec = self._solve_pose(
                np.asarray(
                    object_points,
                    dtype=np.float32,
                ),
                np.asarray(
                    image_points,
                    dtype=np.float32,
                ),
                camera_matrix,
                dist_coeffs,
            )

        metadata["pose_found"] = bool(pose_success)

        if pose_success and rvec is not None and tvec is not None:
            projected_points, _ = cv2.projectPoints(
                np.asarray(
                    object_points,
                    dtype=np.float32,
                ),
                rvec,
                tvec,
                camera_matrix,
                dist_coeffs,
            )

            observed = np.asarray(
                image_points,
                dtype=np.float64,
            ).reshape(-1, 2)

            projected = np.asarray(
                projected_points,
                dtype=np.float64,
            ).reshape(-1, 2)

            residual = observed - projected

            computed_error_px = float(
                np.sqrt(
                    np.mean(
                        np.sum(
                            residual * residual,
                            axis=1,
                        )
                    )
                )
            )

            metadata["error_px"] = computed_error_px

            for observed_point, projected_point in zip(
                observed,
                projected,
            ):
                observed_xy = tuple(
                    np.rint(
                        observed_point
                    ).astype(int)
                )

                projected_xy = tuple(
                    np.rint(
                        projected_point
                    ).astype(int)
                )

                # Detected image point.
                cv2.circle(
                    annotated,
                    observed_xy,
                    3,
                    (0, 255, 0),
                    -1,
                    cv2.LINE_AA,
                )

                # Reprojected 3-D object point.
                self._draw_debug_cross(
                    annotated,
                    projected_xy,
                    (0, 0, 255),
                    size=5,
                    thickness=1,
                )

                # Residual vector.
                cv2.line(
                    annotated,
                    observed_xy,
                    projected_xy,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

            try:
                cv2.drawFrameAxes(
                    annotated,
                    camera_matrix,
                    dist_coeffs,
                    rvec,
                    tvec,
                    float(axis_length_mm),
                    2,
                )
            except cv2.error as error:
                metadata["warnings"].append(
                    "DRAW_BOARD_AXES_FAILED: "
                    + str(error)
                )

        displayed_error = (
            computed_error_px
            if computed_error_px is not None
            else supplied_error_px
        )

        info_lines = [
            f"File: {record.get('filename')}",
            f"Role: {record.get('role')}",
            f"Status: {status}",
            (
                f"Markers: {record.get('marker_count', 0)} | "
                f"ChArUco corners: "
                f"{record.get('charuco_corner_count', 0)}"
            ),
            (
                f"Sharpness: "
                f"{float(record.get('sharpness', 0.0)):.3f} | "
                f"Coverage: "
                f"{float(record.get('coverage_ratio', 0.0)):.4f}"
            ),
            (
                "Reprojection RMSE: "
                + (
                    f"{float(displayed_error):.6f} px"
                    if displayed_error is not None
                    else "N/A"
                )
            ),
            (
                "Pose / board frame: "
                + (
                    "FOUND"
                    if pose_success
                    else "NOT AVAILABLE"
                )
            ),
            (
                "Legend: cyan=markers, green=detected corners, "
                "red=reprojected object points"
            ),
            "Yellow lines = reprojection residual vectors",
        ]

        reasons = list(record.get("reasons", []))

        for reason in reasons[:3]:
            info_lines.append(
                "Reject reason: " + str(reason)
            )

        if len(reasons) > 3:
            info_lines.append(
                f"... and {len(reasons) - 3} more reasons"
            )

        self._draw_debug_text_panel(
            annotated,
            info_lines,
        )

        return annotated, metadata

    def _save_debug_images(
        self,
        output_folder: Path,
        calib_all: Sequence[Dict[str, Any]],
        calib_valid: Sequence[Dict[str, Any]],
        val_all: Sequence[Dict[str, Any]],
        best_candidate: Dict[str, Any],
        board_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        enabled = self._as_bool(
            self.get_config_field_value(
                "enable_debug_images",
                "True",
            )
        )

        if not enabled:
            return {
                "enabled": False,
                "success": True,
                "root_folder": "",
                "manifest_file": "",
                "saved_image_count": 0,
                "errors": [],
            }

        save_rejected = self._as_bool(
            self.get_config_field_value(
                "debug_save_rejected_images",
                "True",
            )
        )

        image_format = str(
            self.get_config_field_value(
                "debug_image_format",
                "PNG",
            )
        ).strip().upper()

        if image_format not in {
            "PNG",
            "JPG",
        }:
            raise ValueError(
                "debug_image_format must be PNG or JPG."
            )

        configured_axis_length = self._as_float(
            self.get_config_field_value(
                "debug_axis_length_mm",
                0.0,
            ),
            "debug_axis_length_mm",
        )

        if configured_axis_length < 0:
            raise ValueError(
                "debug_axis_length_mm cannot be negative."
            )

        axis_length_mm = (
            configured_axis_length
            if configured_axis_length > 0
            else max(
                float(
                    board_data["square_length_mm"]
                ) * 3.0,
                float(
                    board_data["marker_length_mm"]
                ) * 2.0,
            )
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        debug_root = (
            output_folder
            / f"debug_images_{timestamp}"
        ).resolve()

        folders = {
            "calibration_used": (
                debug_root
                / "calibration"
                / "used"
            ),
            "calibration_removed": (
                debug_root
                / "calibration"
                / "removed_outliers"
            ),
            "calibration_not_selected": (
                debug_root
                / "calibration"
                / "not_selected"
            ),
            "calibration_rejected": (
                debug_root
                / "calibration"
                / "rejected"
            ),
            "validation_validated": (
                debug_root
                / "validation"
                / "validated"
            ),
            "validation_rejected": (
                debug_root
                / "validation"
                / "rejected"
            ),
        }

        for folder in folders.values():
            folder.mkdir(
                parents=True,
                exist_ok=True,
            )

        calibration = best_candidate["calibration"]
        validation = best_candidate["validation"]

        camera_matrix = np.asarray(
            calibration["camera_matrix"],
            dtype=np.float64,
        )

        dist_coeffs = np.asarray(
            calibration["dist_coeffs"],
            dtype=np.float64,
        )

        used_indices = list(
            best_candidate["used_indices"]
        )

        used_index_set = set(
            used_indices
        )

        removed_index_set = set(
            best_candidate["removed_indices"]
        )

        calibration_error_by_index = {
            int(record_index): float(error)
            for record_index, error in zip(
                used_indices,
                calibration["per_view_errors"],
            )
        }

        valid_index_by_path = {
            str(record["path"]): index
            for index, record in enumerate(
                calib_valid
            )
        }

        validation_results = list(
            validation.get("images", [])
        )

        manifest_images: List[Dict[str, Any]] = []
        debug_errors: List[Dict[str, Any]] = []
        category_counts: Dict[str, int] = {}

        extension = (
            ".png"
            if image_format == "PNG"
            else ".jpg"
        )

        def export_record(
            record: Dict[str, Any],
            sequence_number: int,
            category: str,
            status: str,
            error_px: Optional[float],
        ) -> None:
            category_counts[category] = (
                category_counts.get(category, 0)
                + 1
            )

            safe_stem = self._safe_debug_stem(
                str(record.get("filename", "image"))
            )

            destination = (
                folders[category]
                / (
                    f"{sequence_number:04d}_"
                    f"{safe_stem}"
                    f"{extension}"
                )
            )

            try:
                annotated, metadata = (
                    self._annotate_debug_image(
                        record,
                        camera_matrix,
                        dist_coeffs,
                        status,
                        axis_length_mm,
                        supplied_error_px=error_px,
                    )
                )

                if annotated is None:
                    raise RuntimeError(
                        str(
                            metadata.get(
                                "debug_error",
                                "ANNOTATION_FAILED",
                            )
                        )
                    )

                self._encode_debug_image(
                    destination,
                    annotated,
                    image_format,
                )

                metadata["category"] = category
                metadata["debug_image_path"] = str(
                    destination.resolve()
                )

                manifest_images.append(
                    metadata
                )

            except Exception as error:
                debug_errors.append(
                    {
                        "filename": record.get(
                            "filename"
                        ),
                        "category": category,
                        "error": (
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                    }
                )

        # ---------------------------------------------------------------------
        # Calibration images
        # ---------------------------------------------------------------------

        for sequence_number, record in enumerate(
            calib_all,
            start=1,
        ):
            if not record["accepted"]:
                if save_rejected:
                    export_record(
                        record,
                        sequence_number,
                        "calibration_rejected",
                        "DETECTION_REJECTED",
                        None,
                    )

                continue

            valid_index = valid_index_by_path.get(
                str(record["path"])
            )

            if valid_index is None:
                if save_rejected:
                    export_record(
                        record,
                        sequence_number,
                        "calibration_not_selected",
                        "VALID_INDEX_NOT_FOUND",
                        None,
                    )

                continue

            if valid_index in used_index_set:
                export_record(
                    record,
                    sequence_number,
                    "calibration_used",
                    "USED_FOR_FINAL_CALIBRATION",
                    calibration_error_by_index.get(
                        valid_index
                    ),
                )

            elif valid_index in removed_index_set:
                export_record(
                    record,
                    sequence_number,
                    "calibration_removed",
                    "REMOVED_AS_OUTLIER",
                    None,
                )

            else:
                export_record(
                    record,
                    sequence_number,
                    "calibration_not_selected",
                    "NOT_USED_BY_SELECTED_ITERATION",
                    None,
                )

        # ---------------------------------------------------------------------
        # Validation images
        # ---------------------------------------------------------------------

        for sequence_number, record in enumerate(
            val_all,
            start=1,
        ):
            validation_result = (
                validation_results[
                    sequence_number - 1
                ]
                if sequence_number - 1
                < len(validation_results)
                else {}
            )

            validation_status = str(
                validation_result.get(
                    "status",
                    "VALIDATION_RESULT_MISSING",
                )
            )

            validation_error = validation_result.get(
                "error_px"
            )

            if validation_status == "VALIDATED":
                export_record(
                    record,
                    sequence_number,
                    "validation_validated",
                    "VALIDATED",
                    (
                        float(validation_error)
                        if validation_error is not None
                        else None
                    ),
                )

            elif save_rejected:
                export_record(
                    record,
                    sequence_number,
                    "validation_rejected",
                    validation_status,
                    None,
                )

        manifest_path = (
            debug_root
            / "manifest.json"
        )

        manifest_payload = {
            "created_at": (
                datetime.now()
                .astimezone()
                .isoformat()
            ),
            "root_folder": str(debug_root),
            "image_format": image_format,
            "axis_length_mm": axis_length_mm,
            "save_rejected_images": save_rejected,
            "selected_calibration_iteration": (
                best_candidate.get("iteration")
            ),
            "camera_matrix": camera_matrix,
            "distortion_coefficients": dist_coeffs,
            "category_counts": category_counts,
            "saved_image_count": len(
                manifest_images
            ),
            "images": manifest_images,
            "errors": debug_errors,
        }

        manifest_path.write_text(
            json.dumps(
                self._json_safe(
                    manifest_payload
                ),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return {
            "enabled": True,
            "success": len(debug_errors) == 0,
            "root_folder": str(debug_root),
            "manifest_file": str(
                manifest_path.resolve()
            ),
            "image_format": image_format,
            "axis_length_mm": axis_length_mm,
            "save_rejected_images": save_rejected,
            "saved_image_count": len(
                manifest_images
            ),
            "category_counts": category_counts,
            "errors": debug_errors,
        }

    def _write_report(
        self,
        output_folder: Path,
        result: Dict[str, Any],
    ) -> str:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        report_path = output_folder / (
            f"charuco_intrinsic_calibration_{timestamp}.txt"
        )

        lines: List[str] = []

        def add(value: str = "") -> None:
            lines.append(value)

        add("=" * 88)
        add("CHARUCO CAMERA INTRINSIC CALIBRATION REPORT")
        add("=" * 88)
        add(f"Created at: {result.get('created_at')}")
        add(f"OpenCV version: {result.get('opencv_version')}")
        add(f"Calibration folder: {result.get('calib_folder')}")
        add(f"Validation folder: {result.get('val_folder')}")
        add()

        add("1. FINAL STATUS")
        add("-" * 88)
        add(
            f"Calibration success : "
            f"{result.get('calibration_success')}"
        )
        add(
            f"Validation passed   : "
            f"{result.get('validation_passed')}"
        )
        add(
            f"Overall success      : "
            f"{result.get('overall_success')}"
        )
        add(
            f"Failure message      : "
            f"{result.get('failure_message') or 'None'}"
        )
        add()

        add("2. BOARD CONFIGURATION")
        add("-" * 88)
        add(
            json.dumps(
                result.get("board", {}),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("3. DATASET SUMMARY")
        add("-" * 88)
        add(
            json.dumps(
                result.get("dataset_summary", {}),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("Calibration detection failures:")
        failures = result.get(
            "calib_detection_failures",
            [],
        )

        if not failures:
            add("  None")

        for failure in failures:
            add(
                f"  - {failure['filename']}: "
                + "; ".join(
                    failure.get("reasons", [])
                )
            )

        add()
        add("Validation detection failures:")

        failures = result.get(
            "val_detection_failures",
            [],
        )

        if not failures:
            add("  None")

        for failure in failures:
            add(
                f"  - {failure['filename']}: "
                + "; ".join(
                    failure.get("reasons", [])
                )
            )

        add()
        add("4. AUTOMATIC ERROR FIX")
        add("-" * 88)
        add(
            json.dumps(
                result.get("auto_fix", {}),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("5. CAMERA MATRIX K")
        add("-" * 88)

        camera_matrix = result.get(
            "camera_matrix"
        )

        if camera_matrix is None:
            add("N/A")
        else:
            for row in camera_matrix:
                add(
                    "  ["
                    + ", ".join(
                        f"{float(value):.12g}"
                        for value in row
                    )
                    + "]"
                )

        add()
        add("6. DISTORTION COEFFICIENTS D")
        add("-" * 88)
        add(
            json.dumps(
                result.get(
                    "distortion_coefficients"
                ),
                ensure_ascii=False,
            )
        )
        add()

        add("7. CALIBRATION ERROR")
        add("-" * 88)
        add(
            f"Initial RMS: "
            f"{result.get('initial_calibration_rms_px')}"
        )
        add(
            f"Final RMS: "
            f"{result.get('final_calibration_rms_px')}"
        )
        add(
            json.dumps(
                result.get(
                    "calibration_per_view_errors",
                    [],
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("8. INDEPENDENT VALIDATION")
        add("-" * 88)
        add(
            json.dumps(
                result.get("validation", {}),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("9. DEBUG IMAGES")
        add("-" * 88)
        add(
            json.dumps(
                result.get("debug_images", {}),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("10. OPERATOR ACTION")
        add("-" * 88)

        actions = result.get(
            "operator_actions",
            [],
        )

        if not actions:
            add("  No action required.")

        for action in actions:
            add(f"  - {action}")

        add()
        add("=" * 88)

        report_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        return str(report_path.resolve())

    # =========================================================================
    # Execute
    # =========================================================================

    async def execute(self) -> Optional[str]:
        calib_folder = Path(
            self.local_input.calib_folder_path
        ).expanduser()

        val_folder = Path(
            self.local_input.val_folder_path
        ).expanduser()

        fallback_output_folder = (
            Path.cwd()
            / "charuco_calibration_failed_result"
        )

        fallback_output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        result: Dict[str, Any] = {
            "created_at": (
                datetime.now()
                .astimezone()
                .isoformat()
            ),
            "opencv_version": cv2.__version__,
            "calib_folder": str(
                calib_folder.resolve()
            ),
            "val_folder": str(
                val_folder.resolve()
            ),
            "calibration_success": False,
            "validation_passed": False,
            "overall_success": False,
            "failure_message": None,
            "board": {},
            "dataset_summary": {},
            "calib_detection_failures": [],
            "val_detection_failures": [],
            "auto_fix": {},
            "camera_matrix": None,
            "distortion_coefficients": None,
            "initial_calibration_rms_px": None,
            "final_calibration_rms_px": None,
            "calibration_per_view_errors": [],
            "validation": {},
            "debug_images": {
                "enabled": False,
                "success": True,
                "root_folder": "",
                "manifest_file": "",
                "saved_image_count": 0,
                "errors": [],
            },
            "operator_actions": [],
        }

        output_folder = fallback_output_folder

        try:
            if not calib_folder.is_dir():
                raise ValueError(
                    f"Invalid calibration folder: {calib_folder}"
                )

            if not val_folder.is_dir():
                raise ValueError(
                    f"Invalid validation folder: {val_folder}"
                )

            output_folder = self._resolve_output_folder(
                calib_folder
            )

            board_data = self._create_board(
                dict(
                    self.local_input.board_info_json
                )
            )

            result["board"] = {
                "squares_x": board_data["squares_x"],
                "squares_y": board_data["squares_y"],
                "dictionary": (
                    board_data["dictionary_name"]
                ),
                "dictionary_id": (
                    board_data["dictionary_id"]
                ),
                "legacy_pattern": (
                    board_data["legacy_pattern"]
                ),
                "expected_corner_count": (
                    board_data[
                        "expected_corner_count"
                    ]
                ),
                "square_length_mm": (
                    board_data["square_length_mm"]
                ),
                "marker_length_mm": (
                    board_data["marker_length_mm"]
                ),
                "print_geometry": (
                    board_data["print_geometry"]
                ),
            }

            detector = self._create_detector(
                board_data["board"]
            )

            calib_paths = self._list_images(
                calib_folder
            )

            val_paths = self._list_images(
                val_folder
            )

            if not calib_paths:
                raise ValueError(
                    "Calibration folder contains no supported images."
                )

            if not val_paths:
                raise ValueError(
                    "Validation folder contains no supported images."
                )

            first_image_size = None

            for path in calib_paths:
                image = cv2.imread(
                    str(path),
                    cv2.IMREAD_COLOR,
                )

                if image is not None:
                    height, width = image.shape[:2]
                    first_image_size = (
                        int(width),
                        int(height),
                    )
                    break

            if first_image_size is None:
                raise ValueError(
                    "No calibration image can be read."
                )

            calib_all = [
                self._detect_image(
                    path,
                    "CALIBRATION",
                    board_data,
                    detector,
                    first_image_size,
                )
                for path in calib_paths
            ]

            val_all = [
                self._detect_image(
                    path,
                    "VALIDATION",
                    board_data,
                    detector,
                    first_image_size,
                )
                for path in val_paths
            ]

            calib_valid = [
                record
                for record in calib_all
                if record["accepted"]
            ]

            val_valid = [
                record
                for record in val_all
                if record["accepted"]
            ]

            result["dataset_summary"] = {
                "image_size": list(
                    first_image_size
                ),
                "calib_total": len(calib_all),
                "calib_accepted": len(
                    calib_valid
                ),
                "calib_rejected": (
                    len(calib_all)
                    - len(calib_valid)
                ),
                "val_total": len(val_all),
                "val_accepted": len(
                    val_valid
                ),
                "val_rejected": (
                    len(val_all)
                    - len(val_valid)
                ),
            }

            result["calib_detection_failures"] = [
                self._public_detection_record(
                    record
                )
                for record in calib_all
                if not record["accepted"]
            ]

            result["val_detection_failures"] = [
                self._public_detection_record(
                    record
                )
                for record in val_all
                if not record["accepted"]
            ]

            best, fix_summary = self._run_error_fix(
                calib_valid,
                val_all,
                first_image_size,
            )

            calibration = best["calibration"]
            validation = best["validation"]

            result["calibration_success"] = True
            result["validation_passed"] = bool(
                validation["summary"]["passed"]
            )
            result["overall_success"] = bool(
                result["calibration_success"]
                and result["validation_passed"]
            )

            result["auto_fix"] = fix_summary

            result["camera_matrix"] = (
                calibration[
                    "camera_matrix"
                ].tolist()
            )

            result["distortion_coefficients"] = (
                calibration[
                    "dist_coeffs"
                ]
                .reshape(-1)
                .tolist()
            )

            initial_candidate = (
                fix_summary["history"][0]
                if fix_summary.get("history")
                else {}
            )

            result["initial_calibration_rms_px"] = (
                initial_candidate.get(
                    "calibration_rms_px"
                )
            )

            result["final_calibration_rms_px"] = (
                calibration["rms"]
            )

            result["calibration_per_view_errors"] = [
                {
                    "filename": (
                        calib_valid[index][
                            "filename"
                        ]
                    ),
                    "error_px": float(error),
                }
                for index, error in zip(
                    best["used_indices"],
                    calibration[
                        "per_view_errors"
                    ],
                )
            ]

            result["validation"] = validation

            try:
                result["debug_images"] = (
                    self._save_debug_images(
                        output_folder,
                        calib_all,
                        calib_valid,
                        val_all,
                        best,
                        board_data,
                    )
                )
            except Exception as debug_error:
                result["debug_images"] = {
                    "enabled": True,
                    "success": False,
                    "root_folder": "",
                    "manifest_file": "",
                    "saved_image_count": 0,
                    "errors": [
                        {
                            "error": (
                                f"{type(debug_error).__name__}: "
                                f"{debug_error}"
                            )
                        }
                    ],
                }

                result["operator_actions"].append(
                    "Calibration succeeded, but debug-image export "
                    "failed: "
                    f"{type(debug_error).__name__}: {debug_error}"
                )

            for failed in result[
                "calib_detection_failures"
            ]:
                result["operator_actions"].append(
                    "Recapture calibration image "
                    f"{failed['filename']}: "
                    + "; ".join(
                        failed["reasons"]
                    )
                )

            for filename in fix_summary.get(
                "removed_images",
                [],
            ):
                result["operator_actions"].append(
                    "Review or recapture calibration outlier: "
                    + filename
                )

            for image_result in validation[
                "images"
            ]:
                if image_result["status"] != "VALIDATED":
                    result["operator_actions"].append(
                        "Recapture validation image "
                        f"{image_result['filename']}: "
                        f"{image_result['status']}"
                    )

            if not result["validation_passed"]:
                result["operator_actions"].insert(
                    0,
                    "Validation did not pass. Do not approve this "
                    "camera profile for production.",
                )

            result["operator_actions"] = list(
                dict.fromkeys(
                    result["operator_actions"]
                )
            )

        except Exception as error:
            result["failure_message"] = (
                f"{type(error).__name__}: {error}"
            )

            result["operator_actions"].append(
                "Fix the configuration or failed dataset images "
                "and run calibration again."
            )

        safe_result = self._json_safe(
            result
        )

        report_path = self._write_report(
            output_folder,
            safe_result,
        )

        self.local_output = self.OUTPUT_SCHEMA(
            calibration_success=bool(
                safe_result[
                    "calibration_success"
                ]
            ),
            validation_passed=bool(
                safe_result[
                    "validation_passed"
                ]
            ),
            overall_success=bool(
                safe_result[
                    "overall_success"
                ]
            ),
            report_file_path=report_path,
            debug_folder_path=str(
                safe_result.get(
                    "debug_images",
                    {},
                ).get(
                    "root_folder",
                    "",
                )
                or ""
            ),
            calibration_result_json=safe_result,
            execute_success="GO",
            execute_failed="GO",
        )

        return (
            "execute_success"
            if self.local_output.overall_success
            else "execute_failed"
        )
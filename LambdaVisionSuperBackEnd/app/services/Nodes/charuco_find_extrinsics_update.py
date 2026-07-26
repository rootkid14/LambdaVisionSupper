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


class FindCharucoExtrinsicsInput(BaseModel):
    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )

    image_path: str = Field(
        ...,
        title="ChArUco Reference Image Path",
        description=UIDataType.STRING.value,
    )

    camera_matrix_json: List[List[float]] = Field(
        ...,
        title="Camera Matrix K",
        description=UIDataType.JSON.value,
    )

    distortion_coefficients_json: List[float] = Field(
        ...,
        title="Distortion Coefficients D",
        description=UIDataType.JSON.value,
    )

    board_config_file_path: str = Field(
        ...,
        title="ChArUco Board Config File Path",
        description=UIDataType.STRING.value,
    )


class FindCharucoExtrinsicsOutput(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    pose_success: bool = Field(
        ...,
        title="Pose Estimation Success",
        description=UIDataType.BOOLEAN.value,
    )

    quality_passed: bool = Field(
        ...,
        title="Pose Quality Passed",
        description=UIDataType.BOOLEAN.value,
    )

    overall_success: bool = Field(
        ...,
        title="Overall Success",
        description=UIDataType.BOOLEAN.value,
    )

    world_to_camera_transform_json: Dict[str, Any] = Field(
        ...,
        title="World to Camera Transform",
        description=UIDataType.JSON.value,
    )

    camera_to_world_transform_json: Dict[str, Any] = Field(
        ...,
        title="Camera to World Transform",
        description=UIDataType.JSON.value,
    )

    extrinsics_profile_json: Dict[str, Any] = Field(
        ...,
        title="Extrinsics Profile",
        description=UIDataType.JSON.value,
    )

    profile_file_path: str = Field(
        ...,
        title="Extrinsics Profile JSON",
        description=UIDataType.STRING.value,
    )

    report_file_path: str = Field(
        ...,
        title="Extrinsics Report TXT",
        description=UIDataType.STRING.value,
    )

    debug_image_path: str = Field(
        ...,
        title="Extrinsics Debug Image",
        description=UIDataType.STRING.value,
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
class FindCharucoExtrinsicsNode(
    BaseNode[
        FindCharucoExtrinsicsInput,
        FindCharucoExtrinsicsOutput,
    ]
):
    """
    Estimate camera extrinsics from one ChArUco reference image.

    Coordinate convention
    ---------------------
    World frame:
        ChArUco board frame.

    World-coordinate convention:
        ChArUco chessboard corner ID 0 is always [0, 0, 0].
        Axis directions remain the native ChArUco X/Y/Z directions.

    OpenCV solvePnP output:
        P_camera = R_camera_from_world * P_world
                   + t_camera_from_world

    Main transform exported by this node:
        P_world = T_world_from_camera * P_camera

    Important:
        A single image pixel cannot define an arbitrary 3-D point without
        additional depth information.

        For points lying on the world plane Z_world = 0, use the inverse
        homography exported in extrinsics_profile_json after first
        undistorting the image pixel.
    """

    INPUT_SCHEMA = FindCharucoExtrinsicsInput
    OUTPUT_SCHEMA = FindCharucoExtrinsicsOutput

    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "Find ChArUco Extrinsics"
    UI_DESCRIPTION = (
        "Estimate world-to-camera and camera-to-world transforms "
        "from a ChArUco reference image"
    )
    UI_COLOR = "bg-sky-600"

    NODE_TIMEOUT = 120.0

    CONFIG_FIELDS = [
        UIConfigField(
            id="output_folder",
            label="Output Folder (empty = automatic)",
            type=UIConfigType.TEXT.value,
            default="",
        ),

        # ---------------------------------------------------------------------
        # World coordinate definition
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # Image and detection validation
        # ---------------------------------------------------------------------

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
            default=15,
        ),
        UIConfigField(
            id="min_corner_ratio",
            label="Minimum ChArUco Corner Ratio",
            type=UIConfigType.NUMBER.value,
            default=0.50,
        ),
        UIConfigField(
            id="min_sharpness",
            label="Minimum Image Sharpness",
            type=UIConfigType.NUMBER.value,
            default=80.0,
        ),

        # ---------------------------------------------------------------------
        # Pose solver
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # Quality validation
        # ---------------------------------------------------------------------

        UIConfigField(
            id="max_reprojection_rmse_px",
            label="Maximum Extrinsics RMSE (px)",
            type=UIConfigType.NUMBER.value,
            default=0.8,
        ),
        UIConfigField(
            id="max_reprojection_point_error_px",
            label="Maximum Corner Error (px)",
            type=UIConfigType.NUMBER.value,
            default=3.0,
        ),

        # ---------------------------------------------------------------------
        # Debug output
        # ---------------------------------------------------------------------

        UIConfigField(
            id="save_debug_image",
            label="Save Extrinsics Debug Image",
            type=UIConfigType.SELECT.value,
            default="True",
            options=[
                "True",
                "False",
            ],
        ),
        UIConfigField(
            id="debug_axis_length_mm",
            label="Debug Axis Length (mm, 0 = automatic)",
            type=UIConfigType.NUMBER.value,
            default=0.0,
        ),
    ]

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _as_bool(value: Any) -> bool:
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
    def _as_float(
        value: Any,
        name: str,
    ) -> float:
        result = float(value)

        if not math.isfinite(result):
            raise ValueError(
                f"{name} must be a finite number."
            )

        return result

    @classmethod
    def _json_safe(
        cls,
        value: Any,
    ) -> Any:
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
            return [
                cls._json_safe(item)
                for item in value
            ]

        return value

    @staticmethod
    def _unwrap_array_value(
        value: Any,
    ) -> Any:
        if not isinstance(value, dict):
            return value

        for key in (
            "matrix",
            "matrix_3x3",
            "matrix_4x4",
            "values",
            "data",
            "coefficients",
        ):
            if key in value:
                return value[key]

        return value

    @staticmethod
    def _collect_nested_dicts(
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        queue: List[Dict[str, Any]] = [payload]
        visited: set[int] = set()

        nested_keys = {
            "calibration_result_json",
            "camera_profile",
            "intrinsics",
            "result",
            "profile",
            "board",
        }

        while queue:
            candidate = queue.pop(0)
            identity = id(candidate)

            if identity in visited:
                continue

            visited.add(identity)
            candidates.append(candidate)

            for key, value in candidate.items():
                if (
                    key in nested_keys
                    and isinstance(value, dict)
                ):
                    queue.append(value)

        return candidates

    # =========================================================================
    # Intrinsic profile
    # =========================================================================

    def _extract_camera_profile(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates = self._collect_nested_dicts(
            payload
        )

        camera_matrix_value = None
        dist_coeffs_value = None
        image_size_value = None
        distortion_model = None

        for candidate in candidates:
            if camera_matrix_value is None:
                for key in (
                    "camera_matrix",
                    "K",
                    "intrinsic_matrix",
                ):
                    if key in candidate:
                        camera_matrix_value = (
                            self._unwrap_array_value(
                                candidate[key]
                            )
                        )
                        break

            if dist_coeffs_value is None:
                for key in (
                    "distortion_coefficients",
                    "dist_coeffs",
                    "D",
                ):
                    if key in candidate:
                        dist_coeffs_value = (
                            self._unwrap_array_value(
                                candidate[key]
                            )
                        )
                        break

            if image_size_value is None:
                if "image_size" in candidate:
                    image_size_value = candidate[
                        "image_size"
                    ]

                dataset_summary = candidate.get(
                    "dataset_summary"
                )

                if (
                    image_size_value is None
                    and isinstance(
                        dataset_summary,
                        dict,
                    )
                ):
                    image_size_value = (
                        dataset_summary.get(
                            "image_size"
                        )
                    )

            if distortion_model is None:
                distortion_model = candidate.get(
                    "distortion_model"
                )

        if camera_matrix_value is None:
            raise ValueError(
                "camera_profile_json does not contain "
                "camera_matrix or K."
            )

        if dist_coeffs_value is None:
            raise ValueError(
                "camera_profile_json does not contain "
                "distortion_coefficients or D."
            )

        camera_matrix = np.asarray(
            camera_matrix_value,
            dtype=np.float64,
        )

        dist_coeffs = np.asarray(
            dist_coeffs_value,
            dtype=np.float64,
        ).reshape(-1, 1)

        if camera_matrix.shape != (3, 3):
            raise ValueError(
                "Camera matrix must have shape 3 x 3. "
                f"Received {camera_matrix.shape}."
            )

        if not np.all(
            np.isfinite(camera_matrix)
        ):
            raise ValueError(
                "Camera matrix contains non-finite values."
            )

        if not np.all(
            np.isfinite(dist_coeffs)
        ):
            raise ValueError(
                "Distortion coefficients contain "
                "non-finite values."
            )

        if (
            camera_matrix[0, 0] <= 0
            or camera_matrix[1, 1] <= 0
        ):
            raise ValueError(
                "Camera focal lengths must be positive."
            )

        image_size = None

        if image_size_value is not None:
            size_array = np.asarray(
                image_size_value
            ).reshape(-1)

            if len(size_array) >= 2:
                image_size = (
                    int(size_array[0]),
                    int(size_array[1]),
                )

        return {
            "camera_matrix": camera_matrix,
            "dist_coeffs": dist_coeffs,
            "image_size": image_size,
            "distortion_model": distortion_model,
        }

    # =========================================================================
    # Board creation
    # =========================================================================

    def _create_board(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates = self._collect_nested_dicts(
            payload
        )

        board_info = None

        for candidate in candidates:
            required = {
                "squares_x",
                "squares_y",
                "square_length_mm",
                "marker_length_mm",
                "dictionary",
            }

            if required.issubset(
                candidate.keys()
            ):
                board_info = candidate
                break

        if board_info is None:
            raise ValueError(
                "board_info_json does not contain a "
                "valid ChArUco board definition."
            )

        squares_x = int(
            board_info["squares_x"]
        )
        squares_y = int(
            board_info["squares_y"]
        )

        square_length = self._as_float(
            board_info["square_length_mm"],
            "square_length_mm",
        )

        marker_length = self._as_float(
            board_info["marker_length_mm"],
            "marker_length_mm",
        )

        print_geometry = board_info.get(
            "print_geometry"
        )

        if isinstance(print_geometry, dict):
            effective_square = (
                print_geometry.get(
                    "effective_square_length_mm"
                )
            )

            effective_marker = (
                print_geometry.get(
                    "effective_marker_length_mm"
                )
            )

            if effective_square is not None:
                square_length = self._as_float(
                    effective_square,
                    "effective_square_length_mm",
                )

            if effective_marker is not None:
                marker_length = self._as_float(
                    effective_marker,
                    "effective_marker_length_mm",
                )

        if squares_x < 2 or squares_y < 2:
            raise ValueError(
                "Board must contain at least 2 x 2 squares."
            )

        if square_length <= 0:
            raise ValueError(
                "square_length_mm must be greater than zero."
            )

        if not 0 < marker_length < square_length:
            raise ValueError(
                "marker_length_mm must be greater than zero "
                "and smaller than square_length_mm."
            )

        dictionary_name = str(
            board_info["dictionary"]
        )

        dictionary_id = getattr(
            cv2.aruco,
            dictionary_name,
            None,
        )

        if dictionary_id is None:
            raise ValueError(
                "Unsupported ArUco dictionary: "
                + dictionary_name
            )

        dictionary = (
            cv2.aruco.getPredefinedDictionary(
                int(dictionary_id)
            )
        )

        board = cv2.aruco.CharucoBoard(
            (
                squares_x,
                squares_y,
            ),
            float(square_length),
            float(marker_length),
            dictionary,
        )

        legacy_pattern = self._as_bool(
            board_info.get(
                "legacy_pattern",
                False,
            )
        )

        if hasattr(
            board,
            "setLegacyPattern",
        ):
            board.setLegacyPattern(
                legacy_pattern
            )
        elif legacy_pattern:
            raise RuntimeError(
                "Current OpenCV version does not support "
                "legacy ChArUco patterns."
            )

        native_corner_table = np.asarray(
            board.getChessboardCorners(),
            dtype=np.float32,
        ).reshape(-1, 3)

        if len(native_corner_table) == 0:
            raise RuntimeError(
                "ChArUco board contains no chessboard corners."
            )

        # The world-coordinate convention is fixed:
        #
        #   origin = ChArUco chessboard corner ID 0
        #   axes   = native ChArUco X/Y/Z directions
        #   plane  = Z_world = 0
        #
        # Only the object-point origin is translated. The board-axis
        # directions are never flipped or reconfigured.
        world_origin_mode = "CHARUCO_CORNER_0"

        origin_offset = (
            native_corner_table[0]
            .copy()
        )

        # Rebase all ChArUco corner coordinates so that ChArUco corner
        # ID 0 becomes exactly [0, 0, 0] when requested.
        world_corner_table = (
            native_corner_table
            - origin_offset.reshape(1, 3)
        ).astype(np.float32)

        return {
            "board": board,
            "dictionary": dictionary,
            "dictionary_name": dictionary_name,
            "dictionary_id": int(dictionary_id),
            "squares_x": squares_x,
            "squares_y": squares_y,
            "square_length_mm": square_length,
            "marker_length_mm": marker_length,
            "legacy_pattern": legacy_pattern,
            "expected_corner_count": int(
                len(world_corner_table)
            ),
            "native_corner_table": (
                native_corner_table
            ),
            "world_corner_table": (
                world_corner_table
            ),
            "world_origin_mode": (
                world_origin_mode
            ),
            "origin_offset_native_mm": (
                origin_offset
            ),
        }

    # =========================================================================
    # Detection
    # =========================================================================

    @staticmethod
    def _create_detector(
        board: Any,
    ) -> Any:
        detector_parameters = (
            cv2.aruco.DetectorParameters()
        )

        if hasattr(
            detector_parameters,
            "cornerRefinementMethod",
        ):
            detector_parameters.cornerRefinementMethod = (
                cv2.aruco.CORNER_REFINE_SUBPIX
            )

        charuco_parameters = (
            cv2.aruco.CharucoParameters()
        )

        if hasattr(
            charuco_parameters,
            "minMarkers",
        ):
            charuco_parameters.minMarkers = 2

        if hasattr(
            charuco_parameters,
            "tryRefineMarkers",
        ):
            charuco_parameters.tryRefineMarkers = True

        return cv2.aruco.CharucoDetector(
            board,
            charuco_parameters,
            detector_parameters,
        )

    def _detect_reference_image(
        self,
        image_path: Path,
        board_data: Dict[str, Any],
        intrinsic_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None or image.size == 0:
            raise ValueError(
                f"IMAGE_UNREADABLE: {image_path}"
            )

        height, width = image.shape[:2]
        image_size = (
            int(width),
            int(height),
        )

        # No hard image-size comparison is performed.
        #
        # K and D are copied manually into this node. The engineer is
        # responsible for ensuring that they belong to the same camera,
        # lens, focus, ROI, crop, and image resolution as this image.

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        sharpness = float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

        detector = self._create_detector(
            board_data["board"]
        )

        (
            charuco_corners,
            charuco_ids,
            marker_corners,
            marker_ids,
        ) = detector.detectBoard(
            gray
        )

        marker_count = (
            0
            if marker_ids is None
            else int(len(marker_ids))
        )

        reasons: List[str] = []
        warnings: List[str] = []

        if (
            charuco_corners is None
            or charuco_ids is None
        ):
            reasons.append(
                "CHARUCO_CORNERS_NOT_FOUND"
            )

            if marker_count == 0:
                reasons.append(
                    "ARUCO_MARKERS_NOT_FOUND"
                )

            raise ValueError(
                "; ".join(reasons)
            )

        image_points = np.asarray(
            charuco_corners,
            dtype=np.float32,
        ).reshape(-1, 1, 2)

        ids = np.asarray(
            charuco_ids,
            dtype=np.int32,
        ).reshape(-1, 1)

        id_values = ids.reshape(-1)

        valid_id_mask = (
            (id_values >= 0)
            & (
                id_values
                < len(
                    board_data[
                        "world_corner_table"
                    ]
                )
            )
        )

        if not np.all(valid_id_mask):
            image_points = image_points[
                valid_id_mask
            ]

            ids = ids[
                valid_id_mask
            ]

            warnings.append(
                "INVALID_CHARUCO_IDS_REMOVED"
            )

        corner_count = int(
            len(ids)
        )

        expected_corner_count = int(
            board_data[
                "expected_corner_count"
            ]
        )

        corner_ratio = (
            corner_count
            / expected_corner_count
            if expected_corner_count > 0
            else 0.0
        )

        object_points = (
            board_data[
                "world_corner_table"
            ][
                ids.reshape(-1)
            ]
            .reshape(-1, 1, 3)
            .astype(np.float32)
        )

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

        if marker_count < min_markers:
            reasons.append(
                "INSUFFICIENT_MARKERS: "
                f"{marker_count} < {min_markers}"
            )

        if corner_count < min_corners:
            reasons.append(
                "INSUFFICIENT_CHARUCO_CORNERS: "
                f"{corner_count} < {min_corners}"
            )

        if corner_ratio < min_corner_ratio:
            reasons.append(
                "LOW_CORNER_RATIO: "
                f"{corner_ratio:.6f} "
                f"< {min_corner_ratio:.6f}"
            )

        if sharpness < min_sharpness:
            reasons.append(
                "IMAGE_BLURRED: "
                f"{sharpness:.6f} "
                f"< {min_sharpness:.6f}"
            )

        try:
            collinear = bool(
                board_data[
                    "board"
                ].checkCharucoCornersCollinear(
                    ids
                )
            )
        except Exception:
            collinear = False
            warnings.append(
                "COLLINEARITY_CHECK_UNAVAILABLE"
            )

        if collinear:
            reasons.append(
                "CHARUCO_CORNERS_COLLINEAR"
            )

        if reasons:
            raise ValueError(
                "; ".join(reasons)
            )

        normalized_marker_corners = (
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

        normalized_marker_ids = (
            None
            if marker_ids is None
            else np.asarray(
                marker_ids,
                dtype=np.int32,
            ).reshape(-1, 1)
        )

        return {
            "image": image,
            "gray": gray,
            "image_size": image_size,
            "sharpness": sharpness,
            "marker_count": marker_count,
            "marker_corners": (
                normalized_marker_corners
            ),
            "marker_ids": (
                normalized_marker_ids
            ),
            "charuco_corner_count": (
                corner_count
            ),
            "corner_ratio": corner_ratio,
            "charuco_ids": ids,
            "image_points": image_points,
            "object_points": object_points,
            "warnings": warnings,
        }

    # =========================================================================
    # Pose estimation
    # =========================================================================

    @staticmethod
    def _calculate_pose_statistics(
        object_points: np.ndarray,
        image_points: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        rvec: np.ndarray,
        tvec: np.ndarray,
    ) -> Dict[str, Any]:
        projected_points, _ = (
            cv2.projectPoints(
                object_points,
                rvec,
                tvec,
                camera_matrix,
                dist_coeffs,
            )
        )

        observed = np.asarray(
            image_points,
            dtype=np.float64,
        ).reshape(-1, 2)

        projected = np.asarray(
            projected_points,
            dtype=np.float64,
        ).reshape(-1, 2)

        residual_vectors = (
            observed - projected
        )

        point_errors = np.linalg.norm(
            residual_vectors,
            axis=1,
        )

        rmse = float(
            np.sqrt(
                np.mean(
                    point_errors
                    * point_errors
                )
            )
        )

        rotation_matrix, _ = cv2.Rodrigues(
            rvec
        )

        world_points = np.asarray(
            object_points,
            dtype=np.float64,
        ).reshape(-1, 3)

        camera_points = (
            rotation_matrix
            @ world_points.T
            + np.asarray(
                tvec,
                dtype=np.float64,
            ).reshape(3, 1)
        ).T

        positive_depth_ratio = float(
            np.mean(
                camera_points[:, 2] > 0
            )
        )

        return {
            "rmse_px": rmse,
            "mean_error_px": float(
                np.mean(point_errors)
            ),
            "median_error_px": float(
                np.median(point_errors)
            ),
            "maximum_error_px": float(
                np.max(point_errors)
            ),
            "p95_error_px": float(
                np.percentile(
                    point_errors,
                    95,
                )
            ),
            "positive_depth_ratio": (
                positive_depth_ratio
            ),
            "point_errors_px": point_errors,
            "residual_vectors_px": (
                residual_vectors
            ),
            "projected_points": (
                projected_points
            ),
            "camera_points": camera_points,
        }

    @staticmethod
    def _refine_pose(
        object_points: np.ndarray,
        image_points: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        rvec: np.ndarray,
        tvec: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if not hasattr(
            cv2,
            "solvePnPRefineLM",
        ):
            return rvec, tvec

        try:
            refined_rvec, refined_tvec = (
                cv2.solvePnPRefineLM(
                    np.ascontiguousarray(
                        object_points,
                        dtype=np.float32,
                    ),
                    np.ascontiguousarray(
                        image_points,
                        dtype=np.float32,
                    ),
                    camera_matrix,
                    dist_coeffs,
                    np.asarray(
                        rvec,
                        dtype=np.float64,
                    ).copy(),
                    np.asarray(
                        tvec,
                        dtype=np.float64,
                    ).copy(),
                )
            )

            return (
                np.asarray(
                    refined_rvec,
                    dtype=np.float64,
                ),
                np.asarray(
                    refined_tvec,
                    dtype=np.float64,
                ),
            )

        except cv2.error:
            return rvec, tvec

    def _estimate_pose(
        self,
        detection: Dict[str, Any],
        intrinsic_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        object_points = np.ascontiguousarray(
            detection["object_points"],
            dtype=np.float32,
        )

        image_points = np.ascontiguousarray(
            detection["image_points"],
            dtype=np.float32,
        )

        camera_matrix = intrinsic_data[
            "camera_matrix"
        ]

        dist_coeffs = intrinsic_data[
            "dist_coeffs"
        ]

        # Solver strategy is internal and deliberately hidden from
        # the engineer-facing UI.
        solver = "IPPE_THEN_ITERATIVE"

        # This is a fixed physical rule rather than a tunable
        # quality parameter.
        minimum_positive_depth_ratio = 1.0

        candidates: List[
            Dict[str, Any]
        ] = []

        def add_candidate(
            method_name: str,
            rvec: np.ndarray,
            tvec: np.ndarray,
            inlier_indices: Optional[
                np.ndarray
            ] = None,
        ) -> None:
            refinement_object_points = (
                object_points
            )

            refinement_image_points = (
                image_points
            )

            if (
                inlier_indices is not None
                and len(inlier_indices) >= 4
            ):
                indices = np.asarray(
                    inlier_indices,
                    dtype=np.int32,
                ).reshape(-1)

                refinement_object_points = (
                    object_points[indices]
                )

                refinement_image_points = (
                    image_points[indices]
                )

            refined_rvec, refined_tvec = (
                self._refine_pose(
                    refinement_object_points,
                    refinement_image_points,
                    camera_matrix,
                    dist_coeffs,
                    rvec,
                    tvec,
                )
            )

            statistics = (
                self._calculate_pose_statistics(
                    object_points,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    refined_rvec,
                    refined_tvec,
                )
            )

            candidates.append(
                {
                    "method": method_name,
                    "rvec": refined_rvec,
                    "tvec": refined_tvec,
                    "inlier_indices": (
                        None
                        if inlier_indices is None
                        else np.asarray(
                            inlier_indices,
                            dtype=np.int32,
                        ).reshape(-1)
                    ),
                    "inlier_count": (
                        len(object_points)
                        if inlier_indices is None
                        else int(
                            len(inlier_indices)
                        )
                    ),
                    "statistics": statistics,
                    "physically_valid": bool(
                        statistics[
                            "positive_depth_ratio"
                        ]
                        >= minimum_positive_depth_ratio
                    ),
                }
            )

        if solver == "RANSAC_ITERATIVE":
            iterations = max(
                1,
                int(
                    self.get_config_field_value(
                        "ransac_iterations",
                        200,
                    )
                ),
            )

            ransac_error = self._as_float(
                self.get_config_field_value(
                    "ransac_reprojection_error_px",
                    2.0,
                ),
                "ransac_reprojection_error_px",
            )

            confidence = self._as_float(
                self.get_config_field_value(
                    "ransac_confidence",
                    0.999,
                ),
                "ransac_confidence",
            )

            if not 0 < confidence < 1:
                raise ValueError(
                    "ransac_confidence must be "
                    "between 0 and 1."
                )

            (
                success,
                rvec,
                tvec,
                inliers,
            ) = cv2.solvePnPRansac(
                object_points,
                image_points,
                camera_matrix,
                dist_coeffs,
                iterationsCount=iterations,
                reprojectionError=ransac_error,
                confidence=confidence,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )

            if success:
                add_candidate(
                    "RANSAC_ITERATIVE",
                    rvec,
                    tvec,
                    inliers,
                )

        elif solver in {
            "IPPE_THEN_ITERATIVE",
            "ITERATIVE",
        }:
            # ChArUco object points are planar. solvePnPGeneric with IPPE
            # can return both possible planar-pose candidates.
            if (
                solver == "IPPE_THEN_ITERATIVE"
                and hasattr(
                    cv2,
                    "solvePnPGeneric",
                )
                and hasattr(
                    cv2,
                    "SOLVEPNP_IPPE",
                )
            ):
                try:
                    generic_result = (
                        cv2.solvePnPGeneric(
                            object_points,
                            image_points,
                            camera_matrix,
                            dist_coeffs,
                            flags=cv2.SOLVEPNP_IPPE,
                        )
                    )

                    generic_success = bool(
                        generic_result[0]
                    )

                    if generic_success:
                        generic_rvecs = (
                            generic_result[1]
                        )
                        generic_tvecs = (
                            generic_result[2]
                        )

                        for solution_index, (
                            rvec,
                            tvec,
                        ) in enumerate(
                            zip(
                                generic_rvecs,
                                generic_tvecs,
                            )
                        ):
                            add_candidate(
                                (
                                    "IPPE_SOLUTION_"
                                    f"{solution_index}"
                                ),
                                rvec,
                                tvec,
                            )

                except cv2.error:
                    pass

            # ITERATIVE is always retained as a fallback candidate.
            try:
                success, rvec, tvec = (
                    cv2.solvePnP(
                        object_points,
                        image_points,
                        camera_matrix,
                        dist_coeffs,
                        flags=cv2.SOLVEPNP_ITERATIVE,
                    )
                )

                if success:
                    add_candidate(
                        "ITERATIVE_FALLBACK",
                        rvec,
                        tvec,
                    )

            except cv2.error:
                pass

        else:
            raise ValueError(
                "Unknown pose_solver: "
                + solver
            )

        if not candidates:
            raise RuntimeError(
                "POSE_ESTIMATION_FAILED: no PnP "
                "solver returned a solution."
            )

        physically_valid_candidates = [
            candidate
            for candidate in candidates
            if candidate["physically_valid"]
        ]

        if not physically_valid_candidates:
            summary = [
                {
                    "method": candidate[
                        "method"
                    ],
                    "rmse_px": candidate[
                        "statistics"
                    ]["rmse_px"],
                    "positive_depth_ratio": (
                        candidate[
                            "statistics"
                        ][
                            "positive_depth_ratio"
                        ]
                    ),
                }
                for candidate in candidates
            ]

            raise RuntimeError(
                "POSE_ESTIMATION_FAILED: all PnP "
                "solutions place too many board points "
                "behind the camera. Candidates: "
                + json.dumps(summary)
            )

        best_candidate = min(
            physically_valid_candidates,
            key=lambda candidate: (
                candidate[
                    "statistics"
                ]["rmse_px"]
            ),
        )

        best_candidate["all_candidates"] = [
            {
                "method": candidate[
                    "method"
                ],
                "rmse_px": candidate[
                    "statistics"
                ]["rmse_px"],
                "maximum_error_px": (
                    candidate[
                        "statistics"
                    ]["maximum_error_px"]
                ),
                "positive_depth_ratio": (
                    candidate[
                        "statistics"
                    ][
                        "positive_depth_ratio"
                    ]
                ),
                "inlier_count": candidate[
                    "inlier_count"
                ],
                "physically_valid": candidate[
                    "physically_valid"
                ],
            }
            for candidate in candidates
        ]

        return best_candidate

    # =========================================================================
    # Transform construction
    # =========================================================================

    @staticmethod
    def _build_transforms(
        rvec: np.ndarray,
        tvec: np.ndarray,
    ) -> Dict[str, Any]:
        rotation_camera_from_world, _ = (
            cv2.Rodrigues(
                np.asarray(
                    rvec,
                    dtype=np.float64,
                )
            )
        )

        translation_camera_from_world = (
            np.asarray(
                tvec,
                dtype=np.float64,
            ).reshape(3, 1)
        )

        transform_camera_from_world = (
            np.eye(
                4,
                dtype=np.float64,
            )
        )

        transform_camera_from_world[
            :3,
            :3,
        ] = rotation_camera_from_world

        transform_camera_from_world[
            :3,
            3,
        ] = (
            translation_camera_from_world
            .reshape(3)
        )

        rotation_world_from_camera = (
            rotation_camera_from_world.T
        )

        translation_world_from_camera = (
            -rotation_world_from_camera
            @ translation_camera_from_world
        )

        transform_world_from_camera = (
            np.eye(
                4,
                dtype=np.float64,
            )
        )

        transform_world_from_camera[
            :3,
            :3,
        ] = rotation_world_from_camera

        transform_world_from_camera[
            :3,
            3,
        ] = (
            translation_world_from_camera
            .reshape(3)
        )

        return {
            "rotation_camera_from_world": (
                rotation_camera_from_world
            ),
            "translation_camera_from_world": (
                translation_camera_from_world
            ),
            "transform_camera_from_world": (
                transform_camera_from_world
            ),
            "rotation_world_from_camera": (
                rotation_world_from_camera
            ),
            "translation_world_from_camera": (
                translation_world_from_camera
            ),
            "transform_world_from_camera": (
                transform_world_from_camera
            ),
            "camera_position_world": (
                translation_world_from_camera
                .reshape(3)
            ),
        }

    @staticmethod
    def _build_world_plane_mapping(
        camera_matrix: np.ndarray,
        transform_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        rotation = transform_data[
            "rotation_camera_from_world"
        ]

        translation = transform_data[
            "translation_camera_from_world"
        ]

        # For Z_world = 0:
        #
        # s [u_ideal, v_ideal, 1]^T
        #     = K [r1 r2 t] [X_world, Y_world, 1]^T
        #
        # This homography is only valid in the ideal undistorted
        # image plane.
        plane_pose = np.column_stack(
            (
                rotation[:, 0],
                rotation[:, 1],
                translation.reshape(3),
            )
        )

        world_plane_to_ideal_image = (
            camera_matrix
            @ plane_pose
        )

        determinant = float(
            np.linalg.det(
                world_plane_to_ideal_image
            )
        )

        if abs(determinant) < 1e-12:
            raise RuntimeError(
                "WORLD_PLANE_HOMOGRAPHY_SINGULAR"
            )

        ideal_image_to_world_plane = (
            np.linalg.inv(
                world_plane_to_ideal_image
            )
        )

        plane_normal_camera = (
            rotation[:, 2]
            .reshape(3)
        )

        plane_offset_camera = float(
            -plane_normal_camera
            @ translation.reshape(3)
        )

        return {
            "world_plane_to_undistorted_image_homography": (
                world_plane_to_ideal_image
            ),
            "undistorted_image_to_world_plane_homography": (
                ideal_image_to_world_plane
            ),
            "world_plane_equation": {
                "frame": "WORLD",
                "equation": "Z_world = 0",
            },
            "plane_in_camera_frame": {
                "normal": (
                    plane_normal_camera
                ),
                "offset": (
                    plane_offset_camera
                ),
                "equation": (
                    "normal^T * P_camera "
                    "+ offset = 0"
                ),
            },
            "usage": {
                "input_pixel_requirement": (
                    "Pixel must first be undistorted "
                    "with cv2.undistortPoints(..., P=K)."
                ),
                "equation": (
                    "[X_world, Y_world, 1]^T "
                    "~ H_image_to_world "
                    "* [u_undistorted, "
                    "v_undistorted, 1]^T"
                ),
                "valid_only_for": (
                    "Points on Z_world = 0."
                ),
            },
        }

    # =========================================================================
    # Debug image
    # =========================================================================

    @staticmethod
    def _draw_cross(
        image: np.ndarray,
        point: Tuple[int, int],
        color: Tuple[int, int, int],
        size: int = 5,
    ) -> None:
        x, y = point

        cv2.line(
            image,
            (
                x - size,
                y - size,
            ),
            (
                x + size,
                y + size,
            ),
            color,
            1,
            cv2.LINE_AA,
        )

        cv2.line(
            image,
            (
                x - size,
                y + size,
            ),
            (
                x + size,
                y - size,
            ),
            color,
            1,
            cv2.LINE_AA,
        )

    @staticmethod
    def _draw_text_panel(
        image: np.ndarray,
        lines: Sequence[str],
    ) -> None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.52
        thickness = 1
        line_height = 22
        padding = 8

        widths = [
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
            max(widths, default=300)
            + 2 * padding,
        )

        panel_height = min(
            image.shape[0],
            len(lines) * line_height
            + 2 * padding,
        )

        overlay = image.copy()

        cv2.rectangle(
            overlay,
            (0, 0),
            (
                panel_width,
                panel_height,
            ),
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

        for index, line in enumerate(
            lines
        ):
            y = (
                padding
                + 16
                + index * line_height
            )

            if y >= panel_height:
                break

            cv2.putText(
                image,
                str(line),
                (
                    padding,
                    y,
                ),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

    @staticmethod
    def _write_image(
        path: Path,
        image: np.ndarray,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        success, encoded = cv2.imencode(
            ".png",
            image,
            [
                cv2.IMWRITE_PNG_COMPRESSION,
                3,
            ],
        )

        if not success:
            raise RuntimeError(
                "Failed to encode debug image."
            )

        path.write_bytes(
            encoded.tobytes()
        )

    def _save_debug_image(
        self,
        output_folder: Path,
        detection: Dict[str, Any],
        intrinsic_data: Dict[str, Any],
        pose_data: Dict[str, Any],
        transform_data: Dict[str, Any],
        board_data: Dict[str, Any],
        quality_passed: bool,
    ) -> str:
        enabled = self._as_bool(
            self.get_config_field_value(
                "save_debug_image",
                "True",
            )
        )

        if not enabled:
            return ""

        annotated = detection[
            "image"
        ].copy()

        marker_corners = detection.get(
            "marker_corners"
        )

        marker_ids = detection.get(
            "marker_ids"
        )

        if marker_corners:
            cv2.aruco.drawDetectedMarkers(
                annotated,
                marker_corners,
                marker_ids,
                borderColor=(
                    255,
                    255,
                    0,
                ),
            )

        cv2.aruco.drawDetectedCornersCharuco(
            annotated,
            detection[
                "image_points"
            ],
            detection[
                "charuco_ids"
            ],
            cornerColor=(
                0,
                255,
                0,
            ),
        )

        statistics = pose_data[
            "statistics"
        ]

        observed_points = np.asarray(
            detection[
                "image_points"
            ],
            dtype=np.float64,
        ).reshape(-1, 2)

        projected_points = np.asarray(
            statistics[
                "projected_points"
            ],
            dtype=np.float64,
        ).reshape(-1, 2)

        for observed, projected in zip(
            observed_points,
            projected_points,
        ):
            observed_xy = tuple(
                np.rint(
                    observed
                ).astype(int)
            )

            projected_xy = tuple(
                np.rint(
                    projected
                ).astype(int)
            )

            # Green circle: detected ChArUco corner.
            cv2.circle(
                annotated,
                observed_xy,
                3,
                (0, 255, 0),
                -1,
                cv2.LINE_AA,
            )

            # Red cross: reprojected world/object point.
            self._draw_cross(
                annotated,
                projected_xy,
                (0, 0, 255),
            )

            # Yellow line: reprojection residual.
            cv2.line(
                annotated,
                observed_xy,
                projected_xy,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )

        configured_axis_length = (
            self._as_float(
                self.get_config_field_value(
                    "debug_axis_length_mm",
                    0.0,
                ),
                "debug_axis_length_mm",
            )
        )

        if configured_axis_length < 0:
            raise ValueError(
                "debug_axis_length_mm cannot be negative."
            )

        axis_length = (
            configured_axis_length
            if configured_axis_length > 0
            else max(
                float(
                    board_data[
                        "square_length_mm"
                    ]
                )
                * 3.0,
                float(
                    board_data[
                        "marker_length_mm"
                    ]
                )
                * 2.0,
            )
        )

        cv2.drawFrameAxes(
            annotated,
            intrinsic_data[
                "camera_matrix"
            ],
            intrinsic_data[
                "dist_coeffs"
            ],
            pose_data["rvec"],
            pose_data["tvec"],
            float(axis_length),
            2,
        )

        # Explicitly project world origin [0, 0, 0].
        #
        # Because all board object points were translated relative to
        # ChArUco corner ID 0, this is the exact pixel location at which
        # the world-coordinate frame begins.
        origin_object_point = np.zeros(
            (1, 1, 3),
            dtype=np.float32,
        )

        origin_projected, _ = cv2.projectPoints(
            origin_object_point,
            pose_data["rvec"],
            pose_data["tvec"],
            intrinsic_data[
                "camera_matrix"
            ],
            intrinsic_data[
                "dist_coeffs"
            ],
        )

        origin_pixel_float = (
            origin_projected
            .reshape(-1, 2)[0]
        )

        origin_pixel = tuple(
            np.rint(
                origin_pixel_float
            ).astype(int)
        )

        cv2.circle(
            annotated,
            origin_pixel,
            12,
            (255, 0, 255),
            3,
            cv2.LINE_AA,
        )

        cv2.circle(
            annotated,
            origin_pixel,
            3,
            (255, 0, 255),
            -1,
            cv2.LINE_AA,
        )

        cv2.putText(
            annotated,
            "WORLD ORIGIN - CHARUCO ID 0",
            (
                origin_pixel[0] + 15,
                origin_pixel[1] - 15,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 0, 255),
            2,
            cv2.LINE_AA,
        )

        camera_position = transform_data[
            "camera_position_world"
        ]

        lines = [
            "CHARUCO EXTRINSICS",
            (
                "Status: "
                + (
                    "PASS"
                    if quality_passed
                    else "QUALITY FAILED"
                )
            ),
            (
                f"Solver: "
                f"{pose_data['method']}"
            ),
            (
                f"Markers: "
                f"{detection['marker_count']} | "
                f"Corners: "
                f"{detection['charuco_corner_count']}"
            ),
            (
                f"Corner ratio: "
                f"{detection['corner_ratio']:.4f} | "
                f"Sharpness: "
                f"{detection['sharpness']:.3f}"
            ),
            (
                f"RMSE: "
                f"{statistics['rmse_px']:.6f} px"
            ),
            (
                f"Maximum error: "
                f"{statistics['maximum_error_px']:.6f} px"
            ),
            (
                "All board points in front: "
                f"{statistics['positive_depth_ratio'] >= 1.0}"
            ),
            (
                "Camera position in world: "
                f"[{camera_position[0]:.3f}, "
                f"{camera_position[1]:.3f}, "
                f"{camera_position[2]:.3f}] mm"
            ),
            (
                "World origin: ChArUco ID 0 at pixel "
                f"({origin_pixel[0]}, {origin_pixel[1]})"
            ),
            (
                "Axis convention: native ChArUco X/Y/Z"
            ),
            (
                "Green=detected | Red=reprojected | "
                "Yellow=residual | Magenta=origin"
            ),
            "Axes show the world frame.",
        ]

        self._draw_text_panel(
            annotated,
            lines,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        debug_path = (
            output_folder
            / (
                "charuco_extrinsics_debug_"
                f"{timestamp}.png"
            )
        )

        self._write_image(
            debug_path,
            annotated,
        )

        return str(
            debug_path.resolve()
        )

    # =========================================================================
    # Output files
    # =========================================================================

    def _resolve_output_folder(
        self,
        image_path: Path,
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
                image_path.parent
                / (
                    image_path.stem
                    + "_extrinsics_result"
                )
            )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_folder.resolve()

    def _write_result_files(
        self,
        output_folder: Path,
        result: Dict[str, Any],
    ) -> Tuple[str, str]:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        profile_path = (
            output_folder
            / (
                "charuco_extrinsics_profile_"
                f"{timestamp}.json"
            )
        )

        report_path = (
            output_folder
            / (
                "charuco_extrinsics_report_"
                f"{timestamp}.txt"
            )
        )

        safe_result = self._json_safe(
            result
        )

        profile_path.write_text(
            json.dumps(
                safe_result,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        lines: List[str] = []

        def add(
            value: str = "",
        ) -> None:
            lines.append(value)

        add("=" * 88)
        add("CHARUCO CAMERA EXTRINSICS REPORT")
        add("=" * 88)
        add(
            f"Created at: "
            f"{safe_result.get('created_at')}"
        )
        add(
            f"OpenCV version: "
            f"{safe_result.get('opencv_version')}"
        )
        add(
            f"Reference image: "
            f"{safe_result.get('reference_image')}"
        )
        add()

        add("1. FINAL STATUS")
        add("-" * 88)
        add(
            "Pose success   : "
            f"{safe_result.get('pose_success')}"
        )
        add(
            "Quality passed : "
            f"{safe_result.get('quality_passed')}"
        )
        add(
            "Overall success: "
            f"{safe_result.get('overall_success')}"
        )
        add(
            "Failure message: "
            f"{safe_result.get('failure_message') or 'None'}"
        )
        add()

        add("2. COORDINATE CONVENTION")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "coordinate_convention",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("3. DETECTION")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "detection",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("4. POSE QUALITY")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "pose_quality",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("5. WORLD TO CAMERA")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "world_to_camera",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("6. CAMERA TO WORLD")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "camera_to_world",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("7. WORLD PLANE Z=0")
        add("-" * 88)
        add(
            json.dumps(
                safe_result.get(
                    "world_plane_mapping",
                    {},
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        add()

        add("8. DEBUG IMAGE")
        add("-" * 88)
        add(
            str(
                safe_result.get(
                    "debug_image_path",
                    "",
                )
            )
        )
        add()
        add("=" * 88)

        report_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        return (
            str(profile_path.resolve()),
            str(report_path.resolve()),
        )

    # =========================================================================
    # Execute
    # =========================================================================

    async def execute(
        self,
    ) -> Optional[str]:
        image_path = Path(
            self.local_input.image_path
        ).expanduser()

        board_config_path = Path(
            self.local_input
            .board_config_file_path
        ).expanduser()

        fallback_output_folder = (
            Path.cwd()
            / "charuco_extrinsics_failed_result"
        )

        fallback_output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_folder = (
            fallback_output_folder
        )

        result: Dict[str, Any] = {
            "schema_version": 1,
            "created_at": (
                datetime.now()
                .astimezone()
                .isoformat()
            ),
            "opencv_version": cv2.__version__,
            "reference_image": str(
                image_path.resolve()
            ),
            "board_config_file": str(
                board_config_path.resolve()
            ),
            "pose_success": False,
            "quality_passed": False,
            "overall_success": False,
            "failure_message": None,
            "coordinate_convention": {},
            "intrinsics": {},
            "board": {},
            "detection": {},
            "pose_quality": {},
            "world_to_camera": {},
            "camera_to_world": {},
            "world_plane_mapping": {},
            "debug_image_path": "",
            "profile_file_path": "",
            "report_file_path": "",
        }

        try:
            if not image_path.is_file():
                raise ValueError(
                    "Invalid reference image path: "
                    + str(image_path)
                )

            output_folder = (
                self._resolve_output_folder(
                    image_path
                )
            )

            intrinsic_data = (
                self._extract_camera_profile(
                    {
                        "camera_matrix": (
                            self.local_input
                            .camera_matrix_json
                        ),
                        "distortion_coefficients": (
                            self.local_input
                            .distortion_coefficients_json
                        ),
                    }
                )
            )

            if not board_config_path.is_file():
                raise ValueError(
                    "Invalid ChArUco board config file path: "
                    + str(board_config_path)
                )

            try:
                board_payload = json.loads(
                    board_config_path.read_text(
                        encoding="utf-8",
                    )
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Invalid ChArUco board config JSON: "
                    f"{error}"
                ) from error

            if not isinstance(
                board_payload,
                dict,
            ):
                raise ValueError(
                    "ChArUco board config file must "
                    "contain a JSON object."
                )

            board_data = self._create_board(
                board_payload
            )

            detection = (
                self._detect_reference_image(
                    image_path,
                    board_data,
                    intrinsic_data,
                )
            )

            pose_data = self._estimate_pose(
                detection,
                intrinsic_data,
            )

            transform_data = (
                self._build_transforms(
                    pose_data["rvec"],
                    pose_data["tvec"],
                )
            )

            world_plane_mapping = (
                self._build_world_plane_mapping(
                    intrinsic_data[
                        "camera_matrix"
                    ],
                    transform_data,
                )
            )

            statistics = pose_data[
                "statistics"
            ]

            maximum_rmse = self._as_float(
                self.get_config_field_value(
                    "max_reprojection_rmse_px",
                    1.0,
                ),
                "max_reprojection_rmse_px",
            )

            maximum_point_error = (
                self._as_float(
                    self.get_config_field_value(
                        "max_reprojection_point_error_px",
                        3.0,
                    ),
                    "max_reprojection_point_error_px",
                )
            )

            quality_passed = bool(
                statistics["rmse_px"]
                <= maximum_rmse
                and statistics[
                    "maximum_error_px"
                ]
                <= maximum_point_error
            )

            result["pose_success"] = True
            result["quality_passed"] = (
                quality_passed
            )
            result["overall_success"] = (
                quality_passed
            )

            result[
                "coordinate_convention"
            ] = {
                "units": "millimetres",
                "world_frame": (
                    "CHARUCO_BOARD"
                ),
                "world_origin": (
                    board_data[
                        "world_origin_mode"
                    ]
                ),
                "world_origin_description": (
                    "ChArUco chessboard corner ID 0"
                    if board_data[
                        "world_origin_mode"
                    ]
                    == "CHARUCO_CORNER_0"
                    else "OpenCV native board origin"
                ),
                "world_axes": {
                    "x": (
                        "Positive X direction of "
                        "the ChArUco board"
                    ),
                    "y": (
                        "Positive Y direction of "
                        "the ChArUco board"
                    ),
                    "z": (
                        "Right-handed board normal"
                    ),
                },
                "camera_axes_opencv": {
                    "x": "right",
                    "y": "down",
                    "z": "forward",
                },
            }

            result["intrinsics"] = {
                "camera_matrix": (
                    intrinsic_data[
                        "camera_matrix"
                    ]
                ),
                "distortion_coefficients": (
                    intrinsic_data[
                        "dist_coeffs"
                    ].reshape(-1)
                ),
                "reference_image_size": (
                    detection[
                        "image_size"
                    ]
                ),
                "image_size_match_check": (
                    "NOT_ENFORCED"
                ),
                "engineer_responsibility": (
                    "K and D must belong to the same camera, "
                    "lens, focus, ROI, crop, and resolution "
                    "as the reference image."
                ),
            }

            result["board"] = {
                "squares_x": (
                    board_data[
                        "squares_x"
                    ]
                ),
                "squares_y": (
                    board_data[
                        "squares_y"
                    ]
                ),
                "square_length_mm": (
                    board_data[
                        "square_length_mm"
                    ]
                ),
                "marker_length_mm": (
                    board_data[
                        "marker_length_mm"
                    ]
                ),
                "dictionary": (
                    board_data[
                        "dictionary_name"
                    ]
                ),
                "legacy_pattern": (
                    board_data[
                        "legacy_pattern"
                    ]
                ),
                "world_origin_mode": (
                    board_data[
                        "world_origin_mode"
                    ]
                ),
                "origin_offset_native_mm": (
                    board_data[
                        "origin_offset_native_mm"
                    ]
                ),
            }

            result["detection"] = {
                "image_size": (
                    detection[
                        "image_size"
                    ]
                ),
                "marker_count": (
                    detection[
                        "marker_count"
                    ]
                ),
                "charuco_corner_count": (
                    detection[
                        "charuco_corner_count"
                    ]
                ),
                "corner_ratio": (
                    detection[
                        "corner_ratio"
                    ]
                ),
                "sharpness": (
                    detection[
                        "sharpness"
                    ]
                ),
                "detected_charuco_ids": (
                    detection[
                        "charuco_ids"
                    ].reshape(-1)
                ),
                "warnings": (
                    detection[
                        "warnings"
                    ]
                ),
            }

            result["pose_quality"] = {
                "solver": (
                    pose_data[
                        "method"
                    ]
                ),
                "candidate_solutions": (
                    pose_data[
                        "all_candidates"
                    ]
                ),
                "inlier_count": (
                    pose_data[
                        "inlier_count"
                    ]
                ),
                "total_corner_count": (
                    detection[
                        "charuco_corner_count"
                    ]
                ),
                "reprojection_rmse_px": (
                    statistics[
                        "rmse_px"
                    ]
                ),
                "mean_error_px": (
                    statistics[
                        "mean_error_px"
                    ]
                ),
                "median_error_px": (
                    statistics[
                        "median_error_px"
                    ]
                ),
                "maximum_error_px": (
                    statistics[
                        "maximum_error_px"
                    ]
                ),
                "p95_error_px": (
                    statistics[
                        "p95_error_px"
                    ]
                ),
                "positive_depth_ratio": (
                    statistics[
                        "positive_depth_ratio"
                    ]
                ),
                "allowed_rmse_px": (
                    maximum_rmse
                ),
                "allowed_maximum_error_px": (
                    maximum_point_error
                ),
                "passed": quality_passed,
            }

            result["world_to_camera"] = {
                "transform_name": (
                    "T_camera_from_world"
                ),
                "equation": (
                    "P_camera = "
                    "R_camera_from_world "
                    "* P_world "
                    "+ t_camera_from_world"
                ),
                "rotation_3x3": (
                    transform_data[
                        "rotation_camera_from_world"
                    ]
                ),
                "translation_mm": (
                    transform_data[
                        "translation_camera_from_world"
                    ].reshape(3)
                ),
                "matrix_4x4": (
                    transform_data[
                        "transform_camera_from_world"
                    ]
                ),
                "opencv_rvec": (
                    pose_data[
                        "rvec"
                    ].reshape(3)
                ),
                "opencv_tvec_mm": (
                    pose_data[
                        "tvec"
                    ].reshape(3)
                ),
            }

            result["camera_to_world"] = {
                "transform_name": (
                    "T_world_from_camera"
                ),
                "equation": (
                    "P_world = "
                    "R_world_from_camera "
                    "* P_camera "
                    "+ t_world_from_camera"
                ),
                "rotation_3x3": (
                    transform_data[
                        "rotation_world_from_camera"
                    ]
                ),
                "translation_mm": (
                    transform_data[
                        "translation_world_from_camera"
                    ].reshape(3)
                ),
                "matrix_4x4": (
                    transform_data[
                        "transform_world_from_camera"
                    ]
                ),
                "camera_position_world_mm": (
                    transform_data[
                        "camera_position_world"
                    ]
                ),
            }

            result[
                "world_plane_mapping"
            ] = world_plane_mapping

            result["debug_image_path"] = (
                self._save_debug_image(
                    output_folder,
                    detection,
                    intrinsic_data,
                    pose_data,
                    transform_data,
                    board_data,
                    quality_passed,
                )
            )

        except Exception as error:
            result["failure_message"] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

        safe_result = self._json_safe(
            result
        )

        profile_path, report_path = (
            self._write_result_files(
                output_folder,
                safe_result,
            )
        )

        safe_result[
            "profile_file_path"
        ] = profile_path

        safe_result[
            "report_file_path"
        ] = report_path

        # Rewrite the profile once so it also contains its final output paths.
        Path(profile_path).write_text(
            json.dumps(
                safe_result,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        self.local_output = (
            self.OUTPUT_SCHEMA(
                pose_success=bool(
                    safe_result[
                        "pose_success"
                    ]
                ),
                quality_passed=bool(
                    safe_result[
                        "quality_passed"
                    ]
                ),
                overall_success=bool(
                    safe_result[
                        "overall_success"
                    ]
                ),
                world_to_camera_transform_json=(
                    safe_result.get(
                        "world_to_camera",
                        {},
                    )
                ),
                camera_to_world_transform_json=(
                    safe_result.get(
                        "camera_to_world",
                        {},
                    )
                ),
                extrinsics_profile_json=(
                    safe_result
                ),
                profile_file_path=(
                    profile_path
                ),
                report_file_path=(
                    report_path
                ),
                debug_image_path=str(
                    safe_result.get(
                        "debug_image_path",
                        "",
                    )
                    or ""
                ),
                execute_success="GO",
                execute_failed="GO",
            )
        )

        return (
            "execute_success"
            if self.local_output.overall_success
            else "execute_failed"
        )
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json
import math

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.services.node_registry import (
    BaseNode,
    registry_node,
)
from app.services.LVSTypes import (
    NodeType,
    UIDataType,
)


# =============================================================================
# INPUT / OUTPUT
# =============================================================================


class PixelToWorldFrameInput(BaseModel):
    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )

    pixel_u: float = Field(
        ...,
        title="Pixel U / X",
        description=UIDataType.NUMBER.value,
    )

    pixel_v: float = Field(
        ...,
        title="Pixel V / Y",
        description=UIDataType.NUMBER.value,
    )

    target_plane_z_mm: float = Field(
        default=0.0,
        title="Target Plane Z (mm)",
        description=UIDataType.NUMBER.value,
    )

    extrinsics_profile_file_path: str = Field(
        ...,
        title="Extrinsics Profile File Path",
        description=UIDataType.STRING.value,
    )


class PixelToWorldFrameOutput(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    conversion_success: bool = Field(
        ...,
        title="Conversion Success",
        description=UIDataType.BOOLEAN.value,
    )

    world_x_mm: float = Field(
        ...,
        title="World X (mm)",
        description=UIDataType.NUMBER.value,
    )

    world_y_mm: float = Field(
        ...,
        title="World Y (mm)",
        description=UIDataType.NUMBER.value,
    )

    world_z_mm: float = Field(
        ...,
        title="World Z (mm)",
        description=UIDataType.NUMBER.value,
    )

    ray_distance_mm: float = Field(
        ...,
        title="Ray Distance (mm)",
        description=UIDataType.NUMBER.value,
    )

    reprojection_error_px: float = Field(
        ...,
        title="Reprojection Error (px)",
        description=UIDataType.NUMBER.value,
    )

    world_point_json: Dict[str, Any] = Field(
        ...,
        title="World Point",
        description=UIDataType.JSON.value,
    )

    calculation_details_json: Dict[str, Any] = Field(
        ...,
        title="Calculation Details",
        description=UIDataType.JSON.value,
    )

    failure_message: str = Field(
        default="",
        title="Failure Message",
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
class PixelToWorldFrameNode(
    BaseNode[
        PixelToWorldFrameInput,
        PixelToWorldFrameOutput,
    ]
):
    """
    Convert one distorted image pixel into a point in the ChArUco world frame.

    The pixel defines a ray, not a unique 3-D point. This node intersects
    that ray with the world plane:

        Z_world = target_plane_z_mm

    Coordinate convention:
        - World origin: ChArUco corner ID 0
        - World axes: native ChArUco X/Y/Z axes
        - Default working plane: Z_world = 0 mm

    Required Extrinsics Profile fields:
        intrinsics.camera_matrix
        intrinsics.distortion_coefficients
        camera_to_world.matrix_4x4

    If camera_to_world is absent, the node can invert:

        world_to_camera.matrix_4x4
    """

    INPUT_SCHEMA = PixelToWorldFrameInput
    OUTPUT_SCHEMA = PixelToWorldFrameOutput

    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "Pixel To World Frame"

    UI_DESCRIPTION = (
        "Convert a distorted image pixel into a physical point "
        "by intersecting its camera ray with a constant-Z world plane"
    )

    UI_COLOR = "bg-emerald-600"

    NODE_TIMEOUT = 10.0

    CONFIG_FIELDS: List[Any] = []

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _as_finite_float(
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
        if isinstance(
            value,
            np.ndarray,
        ):
            return value.tolist()

        if isinstance(
            value,
            np.floating,
        ):
            return float(value)

        if isinstance(
            value,
            np.integer,
        ):
            return int(value)

        if isinstance(
            value,
            Path,
        ):
            return str(value)

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): cls._json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                cls._json_safe(item)
                for item in value
            ]

        return value

    @staticmethod
    def _unwrap_array_value(
        value: Any,
    ) -> Any:
        if not isinstance(
            value,
            dict,
        ):
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
        candidates: List[
            Dict[str, Any]
        ] = []

        queue: List[
            Dict[str, Any]
        ] = [
            payload
        ]

        visited: set[int] = set()

        while queue:
            candidate = queue.pop(0)
            identity = id(candidate)

            if identity in visited:
                continue

            visited.add(identity)
            candidates.append(candidate)

            for value in candidate.values():
                if isinstance(
                    value,
                    dict,
                ):
                    queue.append(value)

        return candidates

    # =========================================================================
    # Profile loading and caching
    # =========================================================================

    def _load_profile_json(
        self,
        profile_path: Path,
    ) -> Dict[str, Any]:
        if not profile_path.is_file():
            raise ValueError(
                "Invalid Extrinsics Profile file path: "
                + str(profile_path)
            )

        stat = profile_path.stat()

        cache_key = (
            str(
                profile_path.resolve()
            ),
            int(
                stat.st_mtime_ns
            ),
            int(
                stat.st_size
            ),
        )

        cached_key = getattr(
            self,
            "_profile_cache_key",
            None,
        )

        cached_payload = getattr(
            self,
            "_profile_cache_payload",
            None,
        )

        if (
            cached_key == cache_key
            and isinstance(
                cached_payload,
                dict,
            )
        ):
            return cached_payload

        try:
            payload = json.loads(
                profile_path.read_text(
                    encoding="utf-8",
                )
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid Extrinsics Profile JSON: "
                f"{error}"
            ) from error

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Extrinsics Profile must contain "
                "a JSON object."
            )

        self._profile_cache_key = (
            cache_key
        )

        self._profile_cache_payload = (
            payload
        )

        return payload

    # =========================================================================
    # Intrinsic extraction
    # =========================================================================

    def _extract_intrinsics(
        self,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates = (
            self._collect_nested_dicts(
                profile
            )
        )

        camera_matrix_value = None
        dist_coeffs_value = None
        reference_image_size = None

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

            if reference_image_size is None:
                for key in (
                    "reference_image_size",
                    "calibration_image_size",
                    "image_size",
                ):
                    if key in candidate:
                        size_value = candidate[key]

                        size_array = np.asarray(
                            size_value
                        ).reshape(-1)

                        if len(size_array) >= 2:
                            reference_image_size = (
                                int(
                                    size_array[0]
                                ),
                                int(
                                    size_array[1]
                                ),
                            )

                        break

        if camera_matrix_value is None:
            raise ValueError(
                "Extrinsics Profile does not contain "
                "intrinsics.camera_matrix."
            )

        if dist_coeffs_value is None:
            raise ValueError(
                "Extrinsics Profile does not contain "
                "intrinsics.distortion_coefficients."
            )

        camera_matrix = np.asarray(
            camera_matrix_value,
            dtype=np.float64,
        )

        dist_coeffs = np.asarray(
            dist_coeffs_value,
            dtype=np.float64,
        ).reshape(-1, 1)

        if camera_matrix.shape != (
            3,
            3,
        ):
            raise ValueError(
                "Camera matrix must have shape 3 x 3. "
                f"Received {camera_matrix.shape}."
            )

        if not np.all(
            np.isfinite(
                camera_matrix
            )
        ):
            raise ValueError(
                "Camera matrix contains "
                "non-finite values."
            )

        if not np.all(
            np.isfinite(
                dist_coeffs
            )
        ):
            raise ValueError(
                "Distortion coefficients contain "
                "non-finite values."
            )

        if len(dist_coeffs) not in {
            4,
            5,
            8,
            12,
            14,
        }:
            raise ValueError(
                "Unsupported distortion coefficient count: "
                f"{len(dist_coeffs)}."
            )

        matrix_scale = float(
            camera_matrix[2, 2]
        )

        if abs(matrix_scale) < 1e-12:
            raise ValueError(
                "Camera matrix K[2,2] cannot be zero."
            )

        camera_matrix = (
            camera_matrix
            / matrix_scale
        )

        if (
            camera_matrix[0, 0] <= 0
            or camera_matrix[1, 1] <= 0
        ):
            raise ValueError(
                "Camera focal lengths fx and fy "
                "must be positive."
            )

        return {
            "camera_matrix": (
                camera_matrix
            ),
            "dist_coeffs": (
                dist_coeffs
            ),
            "reference_image_size": (
                reference_image_size
            ),
        }

    # =========================================================================
    # Transform extraction
    # =========================================================================

    @staticmethod
    def _validate_transform(
        matrix_value: Any,
        matrix_name: str,
    ) -> np.ndarray:
        matrix = np.asarray(
            matrix_value,
            dtype=np.float64,
        )

        if matrix.shape != (
            4,
            4,
        ):
            raise ValueError(
                f"{matrix_name} must have shape 4 x 4. "
                f"Received {matrix.shape}."
            )

        if not np.all(
            np.isfinite(matrix)
        ):
            raise ValueError(
                f"{matrix_name} contains non-finite values."
            )

        homogeneous_scale = float(
            matrix[3, 3]
        )

        if abs(
            homogeneous_scale
        ) < 1e-12:
            raise ValueError(
                f"{matrix_name}[3,3] cannot be zero."
            )

        matrix = (
            matrix
            / homogeneous_scale
        )

        expected_last_row = np.array(
            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            dtype=np.float64,
        )

        last_row_error = float(
            np.linalg.norm(
                matrix[3, :]
                - expected_last_row
            )
        )

        if last_row_error > 1e-6:
            raise ValueError(
                f"{matrix_name} has an invalid "
                "homogeneous last row."
            )

        rotation = matrix[
            :3,
            :3,
        ]

        determinant = float(
            np.linalg.det(
                rotation
            )
        )

        orthogonality_error = float(
            np.linalg.norm(
                rotation.T
                @ rotation
                - np.eye(3)
            )
        )

        if abs(
            determinant - 1.0
        ) > 1e-4:
            raise ValueError(
                f"{matrix_name} contains an invalid "
                "rotation determinant: "
                f"{determinant:.9f}."
            )

        if orthogonality_error > 1e-4:
            raise ValueError(
                f"{matrix_name} rotation is not "
                "sufficiently orthonormal. "
                f"Error={orthogonality_error:.9e}."
            )

        return matrix

    def _extract_transforms(
        self,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        world_from_camera_value = None
        camera_from_world_value = None

        for candidate in (
            self._collect_nested_dicts(
                profile
            )
        ):
            if (
                world_from_camera_value
                is None
                and isinstance(
                    candidate.get(
                        "camera_to_world"
                    ),
                    dict,
                )
            ):
                mapping = candidate[
                    "camera_to_world"
                ]

                for key in (
                    "matrix_4x4",
                    "matrix",
                    "transform",
                ):
                    if key in mapping:
                        world_from_camera_value = (
                            self._unwrap_array_value(
                                mapping[key]
                            )
                        )
                        break

            if (
                camera_from_world_value
                is None
                and isinstance(
                    candidate.get(
                        "world_to_camera"
                    ),
                    dict,
                )
            ):
                mapping = candidate[
                    "world_to_camera"
                ]

                for key in (
                    "matrix_4x4",
                    "matrix",
                    "transform",
                ):
                    if key in mapping:
                        camera_from_world_value = (
                            self._unwrap_array_value(
                                mapping[key]
                            )
                        )
                        break

        if (
            world_from_camera_value
            is None
            and camera_from_world_value
            is None
        ):
            raise ValueError(
                "Extrinsics Profile does not contain "
                "camera_to_world.matrix_4x4 or "
                "world_to_camera.matrix_4x4."
            )

        warnings: List[str] = []

        world_from_camera = None
        camera_from_world = None

        if world_from_camera_value is not None:
            world_from_camera = (
                self._validate_transform(
                    world_from_camera_value,
                    "T_world_from_camera",
                )
            )

        if camera_from_world_value is not None:
            camera_from_world = (
                self._validate_transform(
                    camera_from_world_value,
                    "T_camera_from_world",
                )
            )

        if world_from_camera is None:
            world_from_camera = np.linalg.inv(
                camera_from_world
            )

            world_from_camera = (
                self._validate_transform(
                    world_from_camera,
                    "Inverted T_world_from_camera",
                )
            )

            warnings.append(
                "CAMERA_TO_WORLD_DERIVED_BY_INVERSION"
            )

        if camera_from_world is None:
            camera_from_world = np.linalg.inv(
                world_from_camera
            )

            camera_from_world = (
                self._validate_transform(
                    camera_from_world,
                    "Inverted T_camera_from_world",
                )
            )

            warnings.append(
                "WORLD_TO_CAMERA_DERIVED_BY_INVERSION"
            )

        inverse_consistency_error = float(
            np.linalg.norm(
                world_from_camera
                @ camera_from_world
                - np.eye(4)
            )
        )

        if inverse_consistency_error > 1e-5:
            raise ValueError(
                "camera_to_world and world_to_camera "
                "are inconsistent. "
                f"Error={inverse_consistency_error:.9e}."
            )

        return {
            "world_from_camera": (
                world_from_camera
            ),
            "camera_from_world": (
                camera_from_world
            ),
            "inverse_consistency_error": (
                inverse_consistency_error
            ),
            "warnings": warnings,
        }

    # =========================================================================
    # Profile validation
    # =========================================================================

    @staticmethod
    def _validate_profile_status(
        profile: Dict[str, Any],
    ) -> List[str]:
        warnings: List[str] = []

        if (
            "overall_success" in profile
            and profile[
                "overall_success"
            ]
            is False
        ):
            raise ValueError(
                "The Extrinsics Profile is marked "
                "overall_success = false."
            )

        if (
            "quality_passed" in profile
            and profile[
                "quality_passed"
            ]
            is False
        ):
            raise ValueError(
                "The Extrinsics Profile is marked "
                "quality_passed = false."
            )

        convention = profile.get(
            "coordinate_convention"
        )

        if isinstance(
            convention,
            dict,
        ):
            origin = str(
                convention.get(
                    "world_origin",
                    "",
                )
            ).upper()

            if (
                origin
                and "CHARUCO" not in origin
            ):
                warnings.append(
                    "WORLD_ORIGIN_IS_NOT_DECLARED_AS_CHARUCO"
                )

            if (
                origin
                and "0" not in origin
            ):
                warnings.append(
                    "WORLD_ORIGIN_IS_NOT_DECLARED_AS_ID_0"
                )

        else:
            warnings.append(
                "COORDINATE_CONVENTION_NOT_FOUND"
            )

        return warnings

    # =========================================================================
    # Pixel to world calculation
    # =========================================================================

    @staticmethod
    def _pixel_to_world_plane(
        pixel_u: float,
        pixel_v: float,
        plane_z_mm: float,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        world_from_camera: np.ndarray,
        camera_from_world: np.ndarray,
    ) -> Dict[str, Any]:
        distorted_pixel = np.array(
            [
                [
                    [
                        pixel_u,
                        pixel_v,
                    ]
                ]
            ],
            dtype=np.float64,
        )

        # No P matrix is supplied here. OpenCV therefore returns normalized,
        # undistorted camera coordinates.
        undistorted_normalized = (
            cv2.undistortPoints(
                distorted_pixel,
                camera_matrix,
                dist_coeffs,
            )
        )

        normalized_x = float(
            undistorted_normalized[
                0,
                0,
                0,
            ]
        )

        normalized_y = float(
            undistorted_normalized[
                0,
                0,
                1,
            ]
        )

        ray_camera = np.array(
            [
                normalized_x,
                normalized_y,
                1.0,
            ],
            dtype=np.float64,
        )

        ray_camera_norm = float(
            np.linalg.norm(
                ray_camera
            )
        )

        if ray_camera_norm < 1e-12:
            raise RuntimeError(
                "INVALID_CAMERA_RAY"
            )

        ray_camera = (
            ray_camera
            / ray_camera_norm
        )

        rotation_world_from_camera = (
            world_from_camera[
                :3,
                :3,
            ]
        )

        camera_origin_world = (
            world_from_camera[
                :3,
                3,
            ].copy()
        )

        ray_world = (
            rotation_world_from_camera
            @ ray_camera
        )

        ray_world_norm = float(
            np.linalg.norm(
                ray_world
            )
        )

        if ray_world_norm < 1e-12:
            raise RuntimeError(
                "INVALID_WORLD_RAY"
            )

        ray_world = (
            ray_world
            / ray_world_norm
        )

        denominator = float(
            ray_world[2]
        )

        if abs(
            denominator
        ) < 1e-12:
            raise RuntimeError(
                "RAY_PARALLEL_TO_TARGET_PLANE: "
                "the camera ray does not intersect "
                "a constant-Z world plane."
            )

        ray_distance_mm = float(
            (
                plane_z_mm
                - camera_origin_world[2]
            )
            / denominator
        )

        if ray_distance_mm <= 0.0:
            raise RuntimeError(
                "INTERSECTION_BEHIND_CAMERA: "
                "the selected world plane lies behind "
                "the camera along this pixel ray."
            )

        world_point = (
            camera_origin_world
            + ray_distance_mm
            * ray_world
        )

        # Force the known plane coordinate exactly to avoid retaining a tiny
        # floating-point residue such as 1e-13 instead of zero.
        world_point[2] = (
            plane_z_mm
        )

        world_point_h = np.array(
            [
                world_point[0],
                world_point[1],
                world_point[2],
                1.0,
            ],
            dtype=np.float64,
        )

        camera_point_h = (
            camera_from_world
            @ world_point_h
        )

        camera_point = (
            camera_point_h[:3]
        )

        if camera_point[2] <= 0:
            raise RuntimeError(
                "CALCULATED_POINT_BEHIND_CAMERA"
            )

        rotation_camera_from_world = (
            camera_from_world[
                :3,
                :3,
            ]
        )

        translation_camera_from_world = (
            camera_from_world[
                :3,
                3,
            ].reshape(3, 1)
        )

        rvec_camera_from_world, _ = (
            cv2.Rodrigues(
                rotation_camera_from_world
            )
        )

        reprojected_pixel, _ = (
            cv2.projectPoints(
                world_point.reshape(
                    1,
                    1,
                    3,
                ),
                rvec_camera_from_world,
                translation_camera_from_world,
                camera_matrix,
                dist_coeffs,
            )
        )

        reprojected_pixel = (
            reprojected_pixel
            .reshape(-1, 2)[0]
        )

        reprojection_error_px = float(
            np.linalg.norm(
                reprojected_pixel
                - np.array(
                    [
                        pixel_u,
                        pixel_v,
                    ],
                    dtype=np.float64,
                )
            )
        )

        incidence_cosine = float(
            abs(
                ray_world[2]
            )
        )

        incidence_cosine = float(
            np.clip(
                incidence_cosine,
                0.0,
                1.0,
            )
        )

        ray_angle_to_plane_normal_deg = (
            float(
                math.degrees(
                    math.acos(
                        incidence_cosine
                    )
                )
            )
        )

        return {
            "world_point": world_point,
            "camera_origin_world": (
                camera_origin_world
            ),
            "ray_camera": ray_camera,
            "ray_world": ray_world,
            "normalized_undistorted_pixel": (
                np.array(
                    [
                        normalized_x,
                        normalized_y,
                    ],
                    dtype=np.float64,
                )
            ),
            "ray_plane_denominator": (
                denominator
            ),
            "ray_distance_mm": (
                ray_distance_mm
            ),
            "camera_point": (
                camera_point
            ),
            "camera_depth_mm": float(
                camera_point[2]
            ),
            "reprojected_pixel": (
                reprojected_pixel
            ),
            "reprojection_error_px": (
                reprojection_error_px
            ),
            "ray_angle_to_plane_normal_deg": (
                ray_angle_to_plane_normal_deg
            ),
        }

    # =========================================================================
    # Output helpers
    # =========================================================================

    def _set_failure_output(
        self,
        message: str,
        details: Optional[
            Dict[str, Any]
        ] = None,
    ) -> None:
        self.local_output = (
            self.OUTPUT_SCHEMA(
                conversion_success=False,
                world_x_mm=0.0,
                world_y_mm=0.0,
                world_z_mm=0.0,
                ray_distance_mm=0.0,
                reprojection_error_px=0.0,
                world_point_json={},
                calculation_details_json=(
                    self._json_safe(
                        details or {}
                    )
                ),
                failure_message=message,
                execute_success="GO",
                execute_failed="GO",
            )
        )

    # =========================================================================
    # Execute
    # =========================================================================

    async def execute(
        self,
    ) -> Optional[str]:
        try:
            pixel_u = (
                self._as_finite_float(
                    self.local_input.pixel_u,
                    "pixel_u",
                )
            )

            pixel_v = (
                self._as_finite_float(
                    self.local_input.pixel_v,
                    "pixel_v",
                )
            )

            target_plane_z_mm = (
                self._as_finite_float(
                    self.local_input
                    .target_plane_z_mm,
                    "target_plane_z_mm",
                )
            )

            profile_path = Path(
                self.local_input
                .extrinsics_profile_file_path
            ).expanduser().resolve()

            profile = (
                self._load_profile_json(
                    profile_path
                )
            )

            warnings = (
                self._validate_profile_status(
                    profile
                )
            )

            intrinsic_data = (
                self._extract_intrinsics(
                    profile
                )
            )

            transform_data = (
                self._extract_transforms(
                    profile
                )
            )

            warnings.extend(
                transform_data[
                    "warnings"
                ]
            )

            reference_image_size = (
                intrinsic_data[
                    "reference_image_size"
                ]
            )

            inside_reference_image = None

            if reference_image_size is not None:
                width, height = (
                    reference_image_size
                )

                inside_reference_image = bool(
                    0.0
                    <= pixel_u
                    < float(width)
                    and 0.0
                    <= pixel_v
                    < float(height)
                )

                if not inside_reference_image:
                    warnings.append(
                        "PIXEL_OUTSIDE_REFERENCE_IMAGE"
                    )

            calculation = (
                self._pixel_to_world_plane(
                    pixel_u=pixel_u,
                    pixel_v=pixel_v,
                    plane_z_mm=(
                        target_plane_z_mm
                    ),
                    camera_matrix=(
                        intrinsic_data[
                            "camera_matrix"
                        ]
                    ),
                    dist_coeffs=(
                        intrinsic_data[
                            "dist_coeffs"
                        ]
                    ),
                    world_from_camera=(
                        transform_data[
                            "world_from_camera"
                        ]
                    ),
                    camera_from_world=(
                        transform_data[
                            "camera_from_world"
                        ]
                    ),
                )
            )

            world_point = (
                calculation[
                    "world_point"
                ]
            )

            world_x_mm = float(
                world_point[0]
            )

            world_y_mm = float(
                world_point[1]
            )

            world_z_mm = float(
                world_point[2]
            )

            world_point_json = {
                "frame": "CHARUCO_WORLD",
                "units": "millimetres",
                "x_mm": world_x_mm,
                "y_mm": world_y_mm,
                "z_mm": world_z_mm,
                "source_pixel": {
                    "u": pixel_u,
                    "v": pixel_v,
                },
                "target_plane": {
                    "equation": (
                        "Z_world = constant"
                    ),
                    "z_mm": (
                        target_plane_z_mm
                    ),
                },
            }

            calculation_details = {
                "extrinsics_profile_file": (
                    str(profile_path)
                ),
                "input_pixel_distorted": {
                    "u": pixel_u,
                    "v": pixel_v,
                },
                "reference_image_size": (
                    reference_image_size
                ),
                "pixel_inside_reference_image": (
                    inside_reference_image
                ),
                "normalized_undistorted_pixel": (
                    calculation[
                        "normalized_undistorted_pixel"
                    ]
                ),
                "camera_origin_world_mm": (
                    calculation[
                        "camera_origin_world"
                    ]
                ),
                "camera_ray_unit_vector": (
                    calculation[
                        "ray_camera"
                    ]
                ),
                "world_ray_unit_vector": (
                    calculation[
                        "ray_world"
                    ]
                ),
                "target_plane_z_mm": (
                    target_plane_z_mm
                ),
                "ray_plane_denominator": (
                    calculation[
                        "ray_plane_denominator"
                    ]
                ),
                "ray_distance_mm": (
                    calculation[
                        "ray_distance_mm"
                    ]
                ),
                "camera_point_mm": (
                    calculation[
                        "camera_point"
                    ]
                ),
                "camera_depth_mm": (
                    calculation[
                        "camera_depth_mm"
                    ]
                ),
                "ray_angle_to_plane_normal_deg": (
                    calculation[
                        "ray_angle_to_plane_normal_deg"
                    ]
                ),
                "reprojected_pixel": (
                    calculation[
                        "reprojected_pixel"
                    ]
                ),
                "reprojection_error_px": (
                    calculation[
                        "reprojection_error_px"
                    ]
                ),
                "transform_inverse_consistency_error": (
                    transform_data[
                        "inverse_consistency_error"
                    ]
                ),
                "warnings": warnings,
            }

            self.local_output = (
                self.OUTPUT_SCHEMA(
                    conversion_success=True,
                    world_x_mm=(
                        world_x_mm
                    ),
                    world_y_mm=(
                        world_y_mm
                    ),
                    world_z_mm=(
                        world_z_mm
                    ),
                    ray_distance_mm=float(
                        calculation[
                            "ray_distance_mm"
                        ]
                    ),
                    reprojection_error_px=float(
                        calculation[
                            "reprojection_error_px"
                        ]
                    ),
                    world_point_json=(
                        self._json_safe(
                            world_point_json
                        )
                    ),
                    calculation_details_json=(
                        self._json_safe(
                            calculation_details
                        )
                    ),
                    failure_message="",
                    execute_success="GO",
                    execute_failed="GO",
                )
            )

            return "execute_success"

        except Exception as error:
            failure_message = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            self._set_failure_output(
                failure_message,
                {
                    "input_pixel": {
                        "u": getattr(
                            self.local_input,
                            "pixel_u",
                            None,
                        ),
                        "v": getattr(
                            self.local_input,
                            "pixel_v",
                            None,
                        ),
                    },
                    "target_plane_z_mm": getattr(
                        self.local_input,
                        "target_plane_z_mm",
                        None,
                    ),
                    "extrinsics_profile_file_path": (
                        getattr(
                            self.local_input,
                            "extrinsics_profile_file_path",
                            "",
                        )
                    ),
                },
            )

            return "execute_failed"
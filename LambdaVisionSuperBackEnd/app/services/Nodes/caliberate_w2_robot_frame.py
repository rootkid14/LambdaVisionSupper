from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import csv
import json
import math

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


class CalibrateWorldToRobotFrameInput(BaseModel):
    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
    )

    calibration_pairs_file_path: str = Field(
        ...,
        title="World-Robot Calibration Pairs File Path",
        description=UIDataType.STRING.value,
    )


class CalibrateWorldToRobotFrameOutput(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    calibration_success: bool = Field(
        ...,
        title="Calibration Success",
        description=UIDataType.BOOLEAN.value,
    )

    quality_passed: bool = Field(
        ...,
        title="Calibration Quality Passed",
        description=UIDataType.BOOLEAN.value,
    )

    overall_success: bool = Field(
        ...,
        title="Overall Success",
        description=UIDataType.BOOLEAN.value,
    )

    robot_from_world_transform_json: Dict[str, Any] = Field(
        ...,
        title="World To Robot Transform",
        description=UIDataType.JSON.value,
    )

    world_from_robot_transform_json: Dict[str, Any] = Field(
        ...,
        title="Robot To World Transform",
        description=UIDataType.JSON.value,
    )

    calibration_profile_json: Dict[str, Any] = Field(
        ...,
        title="World-Robot Calibration Profile",
        description=UIDataType.JSON.value,
    )

    profile_file_path: str = Field(
        ...,
        title="Calibration Profile JSON",
        description=UIDataType.STRING.value,
    )

    report_file_path: str = Field(
        ...,
        title="Calibration Report TXT",
        description=UIDataType.STRING.value,
    )

    residual_csv_file_path: str = Field(
        ...,
        title="Calibration Residuals CSV",
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
class CalibrateWorldToRobotFrameNode(
    BaseNode[
        CalibrateWorldToRobotFrameInput,
        CalibrateWorldToRobotFrameOutput,
    ]
):
    """
    Estimate a rigid transform between:

        ChArUco world frame
            and
        Robot base frame

    For every calibration sample, the same physical point must be supplied in
    both coordinate frames:

        world_point_mm
        robot_tcp_point_mm

    The node estimates:

        P_robot = R_robot_from_world * P_world
                  + t_robot_from_world

    Important:
        robot_tcp_point_mm must be the TCP position reported in ROBOT BASE
        coordinates, not in a temporary user frame or work frame.

        Joint positions are not required if the controller already provides
        the Cartesian TCP pose in robot-base coordinates.
    """

    INPUT_SCHEMA = CalibrateWorldToRobotFrameInput
    OUTPUT_SCHEMA = CalibrateWorldToRobotFrameOutput

    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "Calibrate World To Robot Frame"

    UI_DESCRIPTION = (
        "Estimate world-to-robot and robot-to-world rigid transforms "
        "from corresponding ChArUco-world and robot TCP points"
    )

    UI_COLOR = "bg-amber-600"

    NODE_TIMEOUT = 30.0

    CONFIG_FIELDS = [
        UIConfigField(
            id="output_folder",
            label="Output Folder (empty = automatic)",
            type=UIConfigType.TEXT.value,
            default="",
        ),
        UIConfigField(
            id="minimum_point_count",
            label="Minimum Calibration Point Count",
            type=UIConfigType.NUMBER.value,
            default=4,
        ),
        UIConfigField(
            id="robust_outlier_rejection",
            label="Robust Outlier Rejection",
            type=UIConfigType.SELECT.value,
            default="True",
            options=[
                "True",
                "False",
            ],
        ),
        UIConfigField(
            id="outlier_robust_factor",
            label="Outlier Robust Factor (Median/MAD)",
            type=UIConfigType.NUMBER.value,
            default=3.5,
        ),
        UIConfigField(
            id="maximum_outlier_iterations",
            label="Maximum Outlier Iterations",
            type=UIConfigType.NUMBER.value,
            default=10,
        ),
        UIConfigField(
            id="maximum_calibration_rmse_mm",
            label="Maximum Calibration RMSE (mm)",
            type=UIConfigType.NUMBER.value,
            default=1.0,
        ),
        UIConfigField(
            id="maximum_point_error_mm",
            label="Maximum Point Error (mm)",
            type=UIConfigType.NUMBER.value,
            default=2.0,
        ),
    ]

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _as_bool(
        value: Any,
    ) -> bool:
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
                f"Invalid Boolean value: {value!r}."
            )

        return bool(value)

    @staticmethod
    def _as_finite_float(
        value: Any,
        name: str,
    ) -> float:
        result = float(value)

        if not math.isfinite(result):
            raise ValueError(
                f"{name} must be finite."
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

    # =========================================================================
    # Input file
    # =========================================================================

    @staticmethod
    def _read_json_file(
        file_path: Path,
    ) -> Dict[str, Any]:
        if not file_path.is_file():
            raise ValueError(
                "Invalid calibration pairs file path: "
                + str(file_path)
            )

        try:
            payload = json.loads(
                file_path.read_text(
                    encoding="utf-8",
                )
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid calibration pairs JSON: "
                f"{error}"
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                "Calibration pairs file must contain a JSON object."
            )

        return payload

    @classmethod
    def _parse_point(
        cls,
        value: Any,
        field_name: str,
    ) -> np.ndarray:
        """
        Accepted formats:

            [x, y, z]

        or:

            {
                "x_mm": x,
                "y_mm": y,
                "z_mm": z
            }

        or:

            {
                "x": x,
                "y": y,
                "z": z
            }
        """

        if isinstance(value, dict):
            if all(
                key in value
                for key in (
                    "x_mm",
                    "y_mm",
                    "z_mm",
                )
            ):
                value = [
                    value["x_mm"],
                    value["y_mm"],
                    value["z_mm"],
                ]

            elif all(
                key in value
                for key in (
                    "x",
                    "y",
                    "z",
                )
            ):
                value = [
                    value["x"],
                    value["y"],
                    value["z"],
                ]

            elif "position_mm" in value:
                return cls._parse_point(
                    value["position_mm"],
                    field_name,
                )

            elif "position" in value:
                return cls._parse_point(
                    value["position"],
                    field_name,
                )

            elif "translation_mm" in value:
                return cls._parse_point(
                    value["translation_mm"],
                    field_name,
                )

            else:
                raise ValueError(
                    f"{field_name} does not contain x/y/z."
                )

        point = np.asarray(
            value,
            dtype=np.float64,
        ).reshape(-1)

        if len(point) < 3:
            raise ValueError(
                f"{field_name} must contain three values."
            )

        point = point[:3]

        if not np.all(
            np.isfinite(point)
        ):
            raise ValueError(
                f"{field_name} contains non-finite values."
            )

        return point

    @classmethod
    def _extract_pairs(
        cls,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        pairs_value = payload.get(
            "pairs"
        )

        if pairs_value is None:
            pairs_value = payload.get(
                "calibration_pairs"
            )

        if not isinstance(
            pairs_value,
            list,
        ):
            raise ValueError(
                "Calibration file must contain a 'pairs' array."
            )

        result: List[
            Dict[str, Any]
        ] = []

        for index, item in enumerate(
            pairs_value
        ):
            if not isinstance(item, dict):
                raise ValueError(
                    f"pairs[{index}] must be a JSON object."
                )

            if not cls._as_bool(
                item.get(
                    "enabled",
                    True,
                )
            ):
                continue

            if "world_point_mm" not in item:
                raise ValueError(
                    f"pairs[{index}] does not contain "
                    "world_point_mm."
                )

            if "robot_tcp_point_mm" not in item:
                raise ValueError(
                    f"pairs[{index}] does not contain "
                    "robot_tcp_point_mm."
                )

            label = str(
                item.get(
                    "id",
                    item.get(
                        "label",
                        f"P{index + 1:03d}",
                    ),
                )
            )

            result.append(
                {
                    "source_index": index,
                    "label": label,
                    "world_point_mm": (
                        cls._parse_point(
                            item[
                                "world_point_mm"
                            ],
                            (
                                f"pairs[{index}]"
                                ".world_point_mm"
                            ),
                        )
                    ),
                    "robot_tcp_point_mm": (
                        cls._parse_point(
                            item[
                                "robot_tcp_point_mm"
                            ],
                            (
                                f"pairs[{index}]"
                                ".robot_tcp_point_mm"
                            ),
                        )
                    ),
                }
            )

        return result

    # =========================================================================
    # Point-layout validation
    # =========================================================================

    @staticmethod
    def _layout_diagnostics(
        points: np.ndarray,
        frame_name: str,
    ) -> Dict[str, Any]:
        centered = (
            points
            - np.mean(
                points,
                axis=0,
            )
        )

        singular_values = np.linalg.svd(
            centered,
            compute_uv=False,
        )

        primary = float(
            singular_values[0]
        )

        secondary = float(
            singular_values[1]
            if len(singular_values) > 1
            else 0.0
        )

        tertiary = float(
            singular_values[2]
            if len(singular_values) > 2
            else 0.0
        )

        minimum_secondary = max(
            1e-6,
            primary * 1e-4,
        )

        if secondary <= minimum_secondary:
            raise ValueError(
                f"{frame_name} points are collinear or "
                "too close to a line."
            )

        return {
            "singular_values": (
                singular_values
            ),
            "primary_spread": primary,
            "secondary_spread": secondary,
            "tertiary_spread": tertiary,
            "secondary_to_primary_ratio": (
                secondary / primary
                if primary > 0
                else 0.0
            ),
            "tertiary_to_primary_ratio": (
                tertiary / primary
                if primary > 0
                else 0.0
            ),
        }

    # =========================================================================
    # Kabsch rigid registration
    # =========================================================================

    @classmethod
    def _estimate_transform(
        cls,
        world_points: np.ndarray,
        robot_points: np.ndarray,
    ) -> Dict[str, Any]:
        world_points = np.asarray(
            world_points,
            dtype=np.float64,
        )

        robot_points = np.asarray(
            robot_points,
            dtype=np.float64,
        )

        if world_points.shape != robot_points.shape:
            raise ValueError(
                "World and robot point arrays must have identical shapes."
            )

        if (
            world_points.ndim != 2
            or world_points.shape[1] != 3
        ):
            raise ValueError(
                "Point arrays must have shape N x 3."
            )

        if len(world_points) < 3:
            raise ValueError(
                "At least three point pairs are required."
            )

        world_layout = cls._layout_diagnostics(
            world_points,
            "World",
        )

        robot_layout = cls._layout_diagnostics(
            robot_points,
            "Robot",
        )

        world_center = np.mean(
            world_points,
            axis=0,
        )

        robot_center = np.mean(
            robot_points,
            axis=0,
        )

        world_centered = (
            world_points
            - world_center
        )

        robot_centered = (
            robot_points
            - robot_center
        )

        covariance = (
            world_centered.T
            @ robot_centered
        )

        U, singular_values, Vt = (
            np.linalg.svd(
                covariance
            )
        )

        V = Vt.T

        correction = np.eye(
            3,
            dtype=np.float64,
        )

        if np.linalg.det(
            V @ U.T
        ) < 0:
            correction[2, 2] = -1.0

        rotation = (
            V
            @ correction
            @ U.T
        )

        translation = (
            robot_center
            - rotation
            @ world_center
        )

        robot_from_world = np.eye(
            4,
            dtype=np.float64,
        )

        robot_from_world[
            :3,
            :3,
        ] = rotation

        robot_from_world[
            :3,
            3,
        ] = translation

        world_from_robot = np.linalg.inv(
            robot_from_world
        )

        predicted_robot = (
            (
                rotation
                @ world_points.T
            ).T
            + translation
        )

        residual_vectors = (
            robot_points
            - predicted_robot
        )

        point_errors = np.linalg.norm(
            residual_vectors,
            axis=1,
        )

        determinant = float(
            np.linalg.det(rotation)
        )

        orthogonality_error = float(
            np.linalg.norm(
                rotation.T
                @ rotation
                - np.eye(3)
            )
        )

        world_plane_normal_robot = (
            rotation[:, 2].copy()
        )

        world_plane_normal_robot /= (
            np.linalg.norm(
                world_plane_normal_robot
            )
        )

        world_plane_offset_robot = float(
            -world_plane_normal_robot
            @ translation
        )

        table_tilt_deg = float(
            math.degrees(
                math.acos(
                    float(
                        np.clip(
                            abs(
                                world_plane_normal_robot[
                                    2
                                ]
                            ),
                            0.0,
                            1.0,
                        )
                    )
                )
            )
        )

        mapped_world_x = (
            rotation[:, 0]
        )

        world_x_heading_deg = float(
            math.degrees(
                math.atan2(
                    mapped_world_x[1],
                    mapped_world_x[0],
                )
            )
        )

        return {
            "rotation_robot_from_world": (
                rotation
            ),
            "translation_robot_from_world": (
                translation
            ),
            "matrix_robot_from_world": (
                robot_from_world
            ),
            "matrix_world_from_robot": (
                world_from_robot
            ),
            "predicted_robot_points": (
                predicted_robot
            ),
            "residual_vectors_mm": (
                residual_vectors
            ),
            "point_errors_mm": (
                point_errors
            ),
            "rmse_mm": float(
                np.sqrt(
                    np.mean(
                        point_errors ** 2
                    )
                )
            ),
            "mean_error_mm": float(
                np.mean(point_errors)
            ),
            "median_error_mm": float(
                np.median(point_errors)
            ),
            "maximum_error_mm": float(
                np.max(point_errors)
            ),
            "p95_error_mm": float(
                np.percentile(
                    point_errors,
                    95,
                )
            ),
            "rotation_determinant": (
                determinant
            ),
            "rotation_orthogonality_error": (
                orthogonality_error
            ),
            "covariance_singular_values": (
                singular_values
            ),
            "world_layout": world_layout,
            "robot_layout": robot_layout,
            "world_plane_in_robot": {
                "normal": (
                    world_plane_normal_robot
                ),
                "offset": (
                    world_plane_offset_robot
                ),
                "equation": (
                    "normal^T * P_robot + offset = 0"
                ),
                "tilt_from_robot_xy_deg": (
                    table_tilt_deg
                ),
                "world_positive_z_relation": (
                    "SAME_GENERAL_DIRECTION_AS_ROBOT_Z"
                    if world_plane_normal_robot[2] >= 0
                    else "OPPOSITE_GENERAL_DIRECTION_TO_ROBOT_Z"
                ),
            },
            "mapped_world_x_heading_in_robot_xy_deg": (
                world_x_heading_deg
            ),
        }

    # =========================================================================
    # Scale diagnostic
    # =========================================================================

    @staticmethod
    def _calculate_distance_scale_ratio(
        world_points: np.ndarray,
        robot_points: np.ndarray,
    ) -> Dict[str, Any]:
        ratios: List[float] = []

        for first_index in range(
            len(world_points)
        ):
            for second_index in range(
                first_index + 1,
                len(world_points),
            ):
                world_distance = float(
                    np.linalg.norm(
                        world_points[first_index]
                        - world_points[second_index]
                    )
                )

                robot_distance = float(
                    np.linalg.norm(
                        robot_points[first_index]
                        - robot_points[second_index]
                    )
                )

                if world_distance > 1e-9:
                    ratios.append(
                        robot_distance
                        / world_distance
                    )

        if not ratios:
            return {
                "median_ratio": None,
                "minimum_ratio": None,
                "maximum_ratio": None,
            }

        ratio_array = np.asarray(
            ratios,
            dtype=np.float64,
        )

        return {
            "median_ratio": float(
                np.median(ratio_array)
            ),
            "minimum_ratio": float(
                np.min(ratio_array)
            ),
            "maximum_ratio": float(
                np.max(ratio_array)
            ),
            "expected_ratio": 1.0,
            "interpretation": (
                "A ratio far from 1.0 usually indicates "
                "a unit mismatch or incorrect physical dimensions."
            ),
        }

    # =========================================================================
    # Robust outlier rejection
    # =========================================================================

    @classmethod
    def _fit_robust(
        cls,
        world_points: np.ndarray,
        robot_points: np.ndarray,
        minimum_point_count: int,
        enabled: bool,
        robust_factor: float,
        maximum_iterations: int,
    ) -> Dict[str, Any]:
        active_mask = np.ones(
            len(world_points),
            dtype=bool,
        )

        history: List[
            Dict[str, Any]
        ] = []

        if not enabled:
            return {
                "fit": cls._estimate_transform(
                    world_points,
                    robot_points,
                ),
                "active_mask": active_mask,
                "history": history,
            }

        for iteration in range(
            maximum_iterations
        ):
            active_indices = np.where(
                active_mask
            )[0]

            fit = cls._estimate_transform(
                world_points[
                    active_indices
                ],
                robot_points[
                    active_indices
                ],
            )

            errors = fit[
                "point_errors_mm"
            ]

            median_error = float(
                np.median(errors)
            )

            mad = float(
                np.median(
                    np.abs(
                        errors
                        - median_error
                    )
                )
            )

            robust_sigma = (
                1.4826 * mad
            )

            threshold = (
                median_error
                + max(
                    1e-6,
                    robust_factor
                    * robust_sigma,
                )
            )

            local_outliers = np.where(
                errors > threshold
            )[0]

            rejected_global_indices = (
                active_indices[
                    local_outliers
                ]
            )

            history.append(
                {
                    "iteration": (
                        iteration + 1
                    ),
                    "active_point_count": int(
                        len(active_indices)
                    ),
                    "median_error_mm": (
                        median_error
                    ),
                    "mad_mm": mad,
                    "robust_sigma_mm": (
                        robust_sigma
                    ),
                    "threshold_mm": threshold,
                    "rejected_indices": (
                        rejected_global_indices
                    ),
                }
            )

            if len(
                rejected_global_indices
            ) == 0:
                break

            remaining_count = (
                int(
                    np.sum(active_mask)
                )
                - len(
                    rejected_global_indices
                )
            )

            if (
                remaining_count
                < minimum_point_count
            ):
                worst_local_index = int(
                    np.argmax(errors)
                )

                rejected_global_indices = (
                    np.asarray(
                        [
                            active_indices[
                                worst_local_index
                            ]
                        ],
                        dtype=np.int32,
                    )
                )

                if (
                    int(
                        np.sum(active_mask)
                    )
                    - 1
                    < minimum_point_count
                ):
                    break

            active_mask[
                rejected_global_indices
            ] = False

        final_indices = np.where(
            active_mask
        )[0]

        if len(final_indices) < minimum_point_count:
            raise RuntimeError(
                "Outlier rejection left too few calibration points."
            )

        final_fit = cls._estimate_transform(
            world_points[
                final_indices
            ],
            robot_points[
                final_indices
            ],
        )

        return {
            "fit": final_fit,
            "active_mask": active_mask,
            "history": history,
        }

    # =========================================================================
    # Evaluate all original points
    # =========================================================================

    @staticmethod
    def _evaluate_all_points(
        world_points: np.ndarray,
        robot_points: np.ndarray,
        matrix_robot_from_world: np.ndarray,
    ) -> Dict[str, Any]:
        rotation = (
            matrix_robot_from_world[
                :3,
                :3,
            ]
        )

        translation = (
            matrix_robot_from_world[
                :3,
                3,
            ]
        )

        predicted = (
            (
                rotation
                @ world_points.T
            ).T
            + translation
        )

        residuals = (
            robot_points
            - predicted
        )

        errors = np.linalg.norm(
            residuals,
            axis=1,
        )

        return {
            "predicted_robot_points": (
                predicted
            ),
            "residual_vectors_mm": (
                residuals
            ),
            "point_errors_mm": errors,
        }

    # =========================================================================
    # Output files
    # =========================================================================

    def _resolve_output_folder(
        self,
        input_file_path: Path,
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
                input_file_path.parent
                / (
                    input_file_path.stem
                    + "_world_robot_result"
                )
            )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_folder.resolve()

    def _write_files(
        self,
        output_folder: Path,
        result: Dict[str, Any],
        point_rows: Sequence[
            Dict[str, Any]
        ],
    ) -> Tuple[str, str, str]:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        profile_path = (
            output_folder
            / (
                "world_robot_calibration_profile_"
                f"{timestamp}.json"
            )
        )

        report_path = (
            output_folder
            / (
                "world_robot_calibration_report_"
                f"{timestamp}.txt"
            )
        )

        csv_path = (
            output_folder
            / (
                "world_robot_calibration_residuals_"
                f"{timestamp}.csv"
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

        report_lines: List[str] = []

        def add(
            value: str = "",
        ) -> None:
            report_lines.append(value)

        add("=" * 92)
        add("WORLD TO ROBOT FRAME CALIBRATION REPORT")
        add("=" * 92)
        add(
            f"Created at: "
            f"{safe_result.get('created_at')}"
        )
        add(
            "Calibration pairs file: "
            f"{safe_result.get('calibration_pairs_file')}"
        )
        add()

        add("1. FINAL STATUS")
        add("-" * 92)
        add(
            "Calibration success: "
            f"{safe_result.get('calibration_success')}"
        )
        add(
            "Quality passed     : "
            f"{safe_result.get('quality_passed')}"
        )
        add(
            "Overall success    : "
            f"{safe_result.get('overall_success')}"
        )
        add(
            "Failure message    : "
            f"{safe_result.get('failure_message') or 'None'}"
        )
        add()

        for title, key in (
            (
                "2. INPUT SUMMARY",
                "input_summary",
            ),
            (
                "3. CALIBRATION QUALITY",
                "calibration_quality",
            ),
            (
                "4. WORLD TO ROBOT",
                "robot_from_world",
            ),
            (
                "5. ROBOT TO WORLD",
                "world_from_robot",
            ),
            (
                "6. SCARA DIAGNOSTICS",
                "scara_diagnostics",
            ),
        ):
            add(title)
            add("-" * 92)
            add(
                json.dumps(
                    safe_result.get(
                        key,
                        {},
                    ),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            add()

        add("7. POINT RESIDUALS")
        add("-" * 92)

        for row in point_rows:
            add(
                f"{row['label']}: "
                f"inlier={row['inlier']} | "
                f"error={row['error_mm']:.6f} mm | "
                "residual=["
                f"{row['residual_x_mm']:.6f}, "
                f"{row['residual_y_mm']:.6f}, "
                f"{row['residual_z_mm']:.6f}] mm"
            )

        add()
        add("=" * 92)

        report_path.write_text(
            "\n".join(
                report_lines
            )
            + "\n",
            encoding="utf-8",
        )

        csv_fields = [
            "source_index",
            "label",
            "inlier",
            "world_x_mm",
            "world_y_mm",
            "world_z_mm",
            "robot_measured_x_mm",
            "robot_measured_y_mm",
            "robot_measured_z_mm",
            "robot_predicted_x_mm",
            "robot_predicted_y_mm",
            "robot_predicted_z_mm",
            "residual_x_mm",
            "residual_y_mm",
            "residual_z_mm",
            "error_mm",
        ]

        with csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=csv_fields,
            )

            writer.writeheader()

            for row in point_rows:
                writer.writerow(
                    {
                        field: row[field]
                        for field in csv_fields
                    }
                )

        return (
            str(
                profile_path.resolve()
            ),
            str(
                report_path.resolve()
            ),
            str(
                csv_path.resolve()
            ),
        )

    # =========================================================================
    # Execute
    # =========================================================================

    async def execute(
        self,
    ) -> Optional[str]:
        input_file_path = Path(
            self.local_input
            .calibration_pairs_file_path
        ).expanduser()

        fallback_output_folder = (
            Path.cwd()
            / "world_robot_calibration_failed_result"
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
            "calibration_pairs_file": (
                str(
                    input_file_path.resolve()
                )
            ),
            "calibration_success": False,
            "quality_passed": False,
            "overall_success": False,
            "failure_message": None,
            "coordinate_convention": {
                "source_frame": (
                    "CHARUCO_WORLD"
                ),
                "target_frame": (
                    "ROBOT_BASE"
                ),
                "units": "millimetres",
                "equation": (
                    "P_robot = "
                    "T_robot_from_world "
                    "* P_world"
                ),
                "robot_pose_requirement": (
                    "Robot TCP positions must be "
                    "expressed in ROBOT BASE coordinates."
                ),
            },
            "input_summary": {},
            "calibration_quality": {},
            "robot_from_world": {},
            "world_from_robot": {},
            "scara_diagnostics": {},
            "point_results": [],
            "profile_file_path": "",
            "report_file_path": "",
            "residual_csv_file_path": "",
        }

        point_rows: List[
            Dict[str, Any]
        ] = []

        try:
            output_folder = (
                self._resolve_output_folder(
                    input_file_path
                )
            )

            payload = (
                self._read_json_file(
                    input_file_path
                )
            )

            pairs = self._extract_pairs(
                payload
            )

            minimum_point_count = max(
                3,
                int(
                    self.get_config_field_value(
                        "minimum_point_count",
                        4,
                    )
                ),
            )

            if len(pairs) < minimum_point_count:
                raise ValueError(
                    "INSUFFICIENT_CALIBRATION_POINTS: "
                    f"{len(pairs)} "
                    f"< {minimum_point_count}"
                )

            world_points = np.asarray(
                [
                    pair[
                        "world_point_mm"
                    ]
                    for pair in pairs
                ],
                dtype=np.float64,
            )

            robot_points = np.asarray(
                [
                    pair[
                        "robot_tcp_point_mm"
                    ]
                    for pair in pairs
                ],
                dtype=np.float64,
            )

            outlier_enabled = self._as_bool(
                self.get_config_field_value(
                    "robust_outlier_rejection",
                    "True",
                )
            )

            robust_factor = (
                self._as_finite_float(
                    self.get_config_field_value(
                        "outlier_robust_factor",
                        3.5,
                    ),
                    "outlier_robust_factor",
                )
            )

            if robust_factor <= 0:
                raise ValueError(
                    "outlier_robust_factor must "
                    "be greater than zero."
                )

            maximum_iterations = max(
                1,
                int(
                    self.get_config_field_value(
                        "maximum_outlier_iterations",
                        10,
                    )
                ),
            )

            robust_result = (
                self._fit_robust(
                    world_points=(
                        world_points
                    ),
                    robot_points=(
                        robot_points
                    ),
                    minimum_point_count=(
                        minimum_point_count
                    ),
                    enabled=(
                        outlier_enabled
                    ),
                    robust_factor=(
                        robust_factor
                    ),
                    maximum_iterations=(
                        maximum_iterations
                    ),
                )
            )

            fit = robust_result[
                "fit"
            ]

            active_mask = robust_result[
                "active_mask"
            ]

            all_evaluation = (
                self._evaluate_all_points(
                    world_points,
                    robot_points,
                    fit[
                        "matrix_robot_from_world"
                    ],
                )
            )

            maximum_rmse = (
                self._as_finite_float(
                    self.get_config_field_value(
                        "maximum_calibration_rmse_mm",
                        1.0,
                    ),
                    "maximum_calibration_rmse_mm",
                )
            )

            maximum_point_error = (
                self._as_finite_float(
                    self.get_config_field_value(
                        "maximum_point_error_mm",
                        2.0,
                    ),
                    "maximum_point_error_mm",
                )
            )

            if maximum_rmse <= 0:
                raise ValueError(
                    "maximum_calibration_rmse_mm "
                    "must be greater than zero."
                )

            if maximum_point_error <= 0:
                raise ValueError(
                    "maximum_point_error_mm "
                    "must be greater than zero."
                )

            quality_passed = bool(
                fit["rmse_mm"]
                <= maximum_rmse
                and fit[
                    "maximum_error_mm"
                ]
                <= maximum_point_error
                and abs(
                    fit[
                        "rotation_determinant"
                    ]
                    - 1.0
                )
                <= 1e-5
                and fit[
                    "rotation_orthogonality_error"
                ]
                <= 1e-5
            )

            predicted_points = (
                all_evaluation[
                    "predicted_robot_points"
                ]
            )

            residual_vectors = (
                all_evaluation[
                    "residual_vectors_mm"
                ]
            )

            all_errors = (
                all_evaluation[
                    "point_errors_mm"
                ]
            )

            for index, pair in enumerate(
                pairs
            ):
                world = (
                    world_points[index]
                )

                measured = (
                    robot_points[index]
                )

                predicted = (
                    predicted_points[index]
                )

                residual = (
                    residual_vectors[index]
                )

                row = {
                    "source_index": int(
                        pair[
                            "source_index"
                        ]
                    ),
                    "label": pair[
                        "label"
                    ],
                    "inlier": bool(
                        active_mask[index]
                    ),
                    "world_x_mm": float(
                        world[0]
                    ),
                    "world_y_mm": float(
                        world[1]
                    ),
                    "world_z_mm": float(
                        world[2]
                    ),
                    "robot_measured_x_mm": (
                        float(measured[0])
                    ),
                    "robot_measured_y_mm": (
                        float(measured[1])
                    ),
                    "robot_measured_z_mm": (
                        float(measured[2])
                    ),
                    "robot_predicted_x_mm": (
                        float(predicted[0])
                    ),
                    "robot_predicted_y_mm": (
                        float(predicted[1])
                    ),
                    "robot_predicted_z_mm": (
                        float(predicted[2])
                    ),
                    "residual_x_mm": float(
                        residual[0]
                    ),
                    "residual_y_mm": float(
                        residual[1]
                    ),
                    "residual_z_mm": float(
                        residual[2]
                    ),
                    "error_mm": float(
                        all_errors[index]
                    ),
                }

                point_rows.append(row)

            rejected_indices = np.where(
                ~active_mask
            )[0]

            rejected_labels = [
                pairs[int(index)][
                    "label"
                ]
                for index in rejected_indices
            ]

            inlier_world_points = (
                world_points[
                    active_mask
                ]
            )

            inlier_robot_points = (
                robot_points[
                    active_mask
                ]
            )

            scale_diagnostic = (
                self._calculate_distance_scale_ratio(
                    inlier_world_points,
                    inlier_robot_points,
                )
            )

            result[
                "calibration_success"
            ] = True

            result[
                "quality_passed"
            ] = quality_passed

            result[
                "overall_success"
            ] = quality_passed

            result["input_summary"] = {
                "total_enabled_pair_count": int(
                    len(pairs)
                ),
                "inlier_pair_count": int(
                    np.sum(active_mask)
                ),
                "rejected_pair_count": int(
                    len(rejected_indices)
                ),
                "rejected_labels": (
                    rejected_labels
                ),
                "minimum_required_count": (
                    minimum_point_count
                ),
                "robust_outlier_rejection": (
                    outlier_enabled
                ),
                "outlier_robust_factor": (
                    robust_factor
                ),
                "outlier_history": (
                    robust_result[
                        "history"
                    ]
                ),
            }

            result[
                "calibration_quality"
            ] = {
                "fit_uses_inliers_only": True,
                "inlier_rmse_mm": (
                    fit["rmse_mm"]
                ),
                "inlier_mean_error_mm": (
                    fit[
                        "mean_error_mm"
                    ]
                ),
                "inlier_median_error_mm": (
                    fit[
                        "median_error_mm"
                    ]
                ),
                "inlier_maximum_error_mm": (
                    fit[
                        "maximum_error_mm"
                    ]
                ),
                "inlier_p95_error_mm": (
                    fit[
                        "p95_error_mm"
                    ]
                ),
                "all_points_rmse_mm": float(
                    np.sqrt(
                        np.mean(
                            all_errors ** 2
                        )
                    )
                ),
                "all_points_maximum_error_mm": (
                    float(
                        np.max(
                            all_errors
                        )
                    )
                ),
                "allowed_rmse_mm": (
                    maximum_rmse
                ),
                "allowed_maximum_error_mm": (
                    maximum_point_error
                ),
                "rotation_determinant": (
                    fit[
                        "rotation_determinant"
                    ]
                ),
                "rotation_orthogonality_error": (
                    fit[
                        "rotation_orthogonality_error"
                    ]
                ),
                "world_point_layout": (
                    fit[
                        "world_layout"
                    ]
                ),
                "robot_point_layout": (
                    fit[
                        "robot_layout"
                    ]
                ),
                "distance_scale_diagnostic": (
                    scale_diagnostic
                ),
                "passed": quality_passed,
            }

            matrix_robot_from_world = (
                fit[
                    "matrix_robot_from_world"
                ]
            )

            matrix_world_from_robot = (
                fit[
                    "matrix_world_from_robot"
                ]
            )

            result[
                "robot_from_world"
            ] = {
                "transform_name": (
                    "T_robot_from_world"
                ),
                "source_frame": (
                    "CHARUCO_WORLD"
                ),
                "target_frame": (
                    "ROBOT_BASE"
                ),
                "equation": (
                    "P_robot = "
                    "R_robot_from_world "
                    "* P_world "
                    "+ t_robot_from_world"
                ),
                "rotation_3x3": (
                    matrix_robot_from_world[
                        :3,
                        :3,
                    ]
                ),
                "translation_mm": (
                    matrix_robot_from_world[
                        :3,
                        3,
                    ]
                ),
                "matrix_4x4": (
                    matrix_robot_from_world
                ),
            }

            result[
                "world_from_robot"
            ] = {
                "transform_name": (
                    "T_world_from_robot"
                ),
                "source_frame": (
                    "ROBOT_BASE"
                ),
                "target_frame": (
                    "CHARUCO_WORLD"
                ),
                "equation": (
                    "P_world = "
                    "R_world_from_robot "
                    "* P_robot "
                    "+ t_world_from_robot"
                ),
                "rotation_3x3": (
                    matrix_world_from_robot[
                        :3,
                        :3,
                    ]
                ),
                "translation_mm": (
                    matrix_world_from_robot[
                        :3,
                        3,
                    ]
                ),
                "matrix_4x4": (
                    matrix_world_from_robot
                ),
            }

            result[
                "scara_diagnostics"
            ] = {
                "world_origin_in_robot_mm": (
                    fit[
                        "translation_robot_from_world"
                    ]
                ),
                "mapped_world_x_heading_in_robot_xy_deg": (
                    fit[
                        "mapped_world_x_heading_in_robot_xy_deg"
                    ]
                ),
                "world_plane_in_robot": (
                    fit[
                        "world_plane_in_robot"
                    ]
                ),
                "interpretation": (
                    "For a normal SCARA installation, "
                    "world-plane tilt from robot XY "
                    "should usually be small."
                ),
            }

            result[
                "point_results"
            ] = point_rows

        except Exception as error:
            result[
                "failure_message"
            ] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

        safe_result = self._json_safe(
            result
        )

        (
            profile_path,
            report_path,
            csv_path,
        ) = self._write_files(
            output_folder,
            safe_result,
            point_rows,
        )

        safe_result[
            "profile_file_path"
        ] = profile_path

        safe_result[
            "report_file_path"
        ] = report_path

        safe_result[
            "residual_csv_file_path"
        ] = csv_path

        # Rewrite the JSON so it includes its own output paths.
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
                calibration_success=bool(
                    safe_result[
                        "calibration_success"
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
                robot_from_world_transform_json=(
                    safe_result.get(
                        "robot_from_world",
                        {},
                    )
                ),
                world_from_robot_transform_json=(
                    safe_result.get(
                        "world_from_robot",
                        {},
                    )
                ),
                calibration_profile_json=(
                    safe_result
                ),
                profile_file_path=(
                    profile_path
                ),
                report_file_path=(
                    report_path
                ),
                residual_csv_file_path=(
                    csv_path
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
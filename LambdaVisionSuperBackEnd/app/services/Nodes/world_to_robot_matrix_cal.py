from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import json
import math

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


class WorldPointToRobotFrameInput(BaseModel):

    execute_in: Any = Field(
        default="GO",
        title="execute",
        description=UIDataType.EXECUTE.value,
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

    calibration_profile_path: str = Field(
        ...,
        title="World-Robot Calibration Profile JSON Path",
        description=UIDataType.STRING.value,
    )


class WorldPointToRobotFrameOutput(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    conversion_success: bool = Field(
        ...,
        title="Conversion Success",
        description=UIDataType.BOOLEAN.value,
    )

    robot_x_mm: float = Field(
        ...,
        title="Robot X (mm)",
        description=UIDataType.NUMBER.value,
    )

    robot_y_mm: float = Field(
        ...,
        title="Robot Y (mm)",
        description=UIDataType.NUMBER.value,
    )

    robot_z_mm: float = Field(
        ...,
        title="Robot Z (mm)",
        description=UIDataType.NUMBER.value,
    )

    robot_point: Dict[str, Any] = Field(
        ...,
        title="Robot Point",
        description=UIDataType.DICT.value,
    )

    calculation_details: Dict[str, Any] = Field(
        ...,
        title="Calculation Details",
        description=UIDataType.DICT.value,
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
class WorldPointToRobotFrameNode(
    BaseNode[
        WorldPointToRobotFrameInput,
        WorldPointToRobotFrameOutput,
    ]
):

    """
    Convert a point from CHARUCO_WORLD frame
    into ROBOT_BASE frame.

    The world-to-robot transformation matrix is loaded
    automatically from a World-Robot calibration JSON profile.

    Equation:

        P_robot = T_robot_from_world @ P_world
    """

    INPUT_SCHEMA = WorldPointToRobotFrameInput
    OUTPUT_SCHEMA = WorldPointToRobotFrameOutput

    NODE_TYPE = NodeType.PROGRAM

    UI_LABEL = "World Point To Robot Frame"

    UI_DESCRIPTION = (
        "Convert XYZ point from ChArUco world coordinates "
        "to robot base coordinates using a calibration profile"
    )

    UI_COLOR = "bg-orange-600"

    NODE_TIMEOUT = 5.0

    CONFIG_FIELDS = []

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

    # =========================================================================
    # Calibration profile
    # =========================================================================

    @staticmethod
    def _load_calibration_profile(
        profile_path: Path,
    ) -> Dict[str, Any]:

        if not profile_path.is_file():
            raise ValueError(
                "World-Robot calibration profile does not exist: "
                + str(profile_path)
            )

        try:
            text = profile_path.read_text(
                encoding="utf-8"
            )
        except Exception as error:
            raise ValueError(
                "Failed to read World-Robot calibration profile: "
                + str(error)
            ) from error

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid World-Robot calibration JSON: "
                + str(error)
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                "World-Robot calibration profile "
                "must contain a JSON object."
            )

        return payload

    @staticmethod
    def _extract_world_to_robot_matrix(
        payload: Dict[str, Any],
    ) -> np.ndarray:

        matrix_value = None

        # =============================================================
        # Preferred format produced by
        # CALIBRATE_WORLD_TO_ROBOT_FRAME:
        #
        # {
        #     "robot_from_world": {
        #         "matrix_4x4": [...]
        #     }
        # }
        # =============================================================

        robot_from_world = payload.get(
            "robot_from_world"
        )

        if isinstance(
            robot_from_world,
            dict,
        ):
            matrix_value = (
                robot_from_world.get(
                    "matrix_4x4"
                )
            )

        # =============================================================
        # Compatibility:
        #
        # {
        #     "world_to_robot": {
        #         "matrix_4x4": [...]
        #     }
        # }
        # =============================================================

        if matrix_value is None:

            world_to_robot = payload.get(
                "world_to_robot"
            )

            if isinstance(
                world_to_robot,
                dict,
            ):
                matrix_value = (
                    world_to_robot.get(
                        "matrix_4x4"
                    )
                )

        # =============================================================
        # Simple test file:
        #
        # {
        #     "matrix_4x4": [...]
        # }
        # =============================================================

        if matrix_value is None:
            matrix_value = payload.get(
                "matrix_4x4"
            )

        if matrix_value is None:
            raise ValueError(
                "Calibration profile does not contain "
                "robot_from_world.matrix_4x4."
            )

        matrix = np.asarray(
            matrix_value,
            dtype=np.float64,
        )

        # =============================================================
        # Validate shape
        # =============================================================

        if matrix.shape != (4, 4):
            raise ValueError(
                "World-to-robot matrix must have shape 4x4. "
                f"Received {matrix.shape}."
            )

        # =============================================================
        # Validate finite numbers
        # =============================================================

        if not np.all(
            np.isfinite(matrix)
        ):
            raise ValueError(
                "World-to-robot matrix contains "
                "non-finite values."
            )

        # =============================================================
        # Validate homogeneous last row
        # =============================================================

        expected_last_row = np.array(
            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            dtype=np.float64,
        )

        if not np.allclose(
            matrix[3, :],
            expected_last_row,
            atol=1e-6,
        ):
            raise ValueError(
                "Invalid homogeneous transformation matrix. "
                "Last row must be [0, 0, 0, 1]."
            )

        # =============================================================
        # Validate rotation
        # =============================================================

        rotation = matrix[
            :3,
            :3,
        ]

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

        if abs(
            determinant - 1.0
        ) > 1e-4:
            raise ValueError(
                "Invalid rotation matrix. "
                f"det(R) = {determinant:.9f}, "
                "expected approximately 1."
            )

        if orthogonality_error > 1e-4:
            raise ValueError(
                "Rotation matrix is not orthonormal. "
                f"error = {orthogonality_error:.9e}"
            )

        return matrix

    # =========================================================================
    # Execute
    # =========================================================================

    async def execute(
        self,
    ) -> Optional[str]:

        try:

            # =========================================================
            # Read world point
            # =========================================================

            world_x = self._as_finite_float(
                self.local_input.world_x_mm,
                "world_x_mm",
            )

            world_y = self._as_finite_float(
                self.local_input.world_y_mm,
                "world_y_mm",
            )

            world_z = self._as_finite_float(
                self.local_input.world_z_mm,
                "world_z_mm",
            )

            # =========================================================
            # Resolve calibration profile
            # =========================================================

            profile_path = Path(
                self.local_input
                .calibration_profile_path
            ).expanduser()

            profile_payload = (
                self._load_calibration_profile(
                    profile_path
                )
            )

            transform = (
                self._extract_world_to_robot_matrix(
                    profile_payload
                )
            )

            # =========================================================
            # Construct homogeneous world point
            #
            #     [Xw]
            #     [Yw]
            #     [Zw]
            #     [ 1]
            #
            # =========================================================

            world_point_h = np.array(
                [
                    world_x,
                    world_y,
                    world_z,
                    1.0,
                ],
                dtype=np.float64,
            )

            # =========================================================
            # WORLD -> ROBOT
            #
            # P_robot =
            #     T_robot_from_world
            #     @
            #     P_world
            #
            # =========================================================

            robot_point_h = (
                transform
                @ world_point_h
            )

            robot_x = float(
                robot_point_h[0]
            )

            robot_y = float(
                robot_point_h[1]
            )

            robot_z = float(
                robot_point_h[2]
            )

            # =========================================================
            # Output
            # =========================================================

            robot_point = {
                "frame": "ROBOT_BASE",
                "units": "millimetres",
                "x_mm": robot_x,
                "y_mm": robot_y,
                "z_mm": robot_z,
            }

            calculation_details = {
                "source_frame": "CHARUCO_WORLD",
                "target_frame": "ROBOT_BASE",

                "equation": (
                    "P_robot = "
                    "T_robot_from_world "
                    "@ P_world"
                ),

                "calibration_profile_path": str(
                    profile_path.resolve()
                ),

                "world_point_mm": [
                    world_x,
                    world_y,
                    world_z,
                ],

                "world_point_homogeneous": (
                    world_point_h.tolist()
                ),

                "world_to_robot_matrix_4x4": (
                    transform.tolist()
                ),

                "robot_point_mm": [
                    robot_x,
                    robot_y,
                    robot_z,
                ],
            }

            self.local_output = (
                self.OUTPUT_SCHEMA(

                    conversion_success=True,

                    robot_x_mm=robot_x,
                    robot_y_mm=robot_y,
                    robot_z_mm=robot_z,

                    robot_point=robot_point,

                    calculation_details=(
                        calculation_details
                    ),

                    failure_message="",

                    execute_success="GO",
                    execute_failed="GO",
                )
            )

            return "execute_success"

        except Exception as error:

            self.local_output = (
                self.OUTPUT_SCHEMA(

                    conversion_success=False,

                    robot_x_mm=0.0,
                    robot_y_mm=0.0,
                    robot_z_mm=0.0,

                    robot_point={},

                    calculation_details={},

                    failure_message=(
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),

                    execute_success="GO",
                    execute_failed="GO",
                )
            )

            return "execute_failed"
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


# =============================================================================
# Generic source-patching helpers
# =============================================================================


def replace_once(
    content: str,
    old: str,
    new: str,
    description: str,
) -> str:
    count = content.count(old)

    if count != 1:
        raise RuntimeError(
            f"Cannot safely replace {description}. "
            f"Expected exactly one match, found {count}."
        )

    return content.replace(
        old,
        new,
        1,
    )


def replace_between(
    content: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    description: str,
) -> str:
    start_index = content.find(
        start_marker
    )

    if start_index < 0:
        raise RuntimeError(
            f"Cannot find start marker for {description}."
        )

    end_index = content.find(
        end_marker,
        start_index + len(start_marker),
    )

    if end_index < 0:
        raise RuntimeError(
            f"Cannot find end marker for {description}."
        )

    return (
        content[:start_index]
        + replacement.rstrip()
        + "\n\n"
        + content[end_index:]
    )


def remove_config_field(
    content: str,
    field_id: str,
) -> str:
    """
    Remove one complete UIConfigField(...) block using balanced parentheses.
    """

    marker = (
        "        UIConfigField(\n"
        f'            id="{field_id}",'
    )

    start_index = content.find(
        marker
    )

    if start_index < 0:
        raise RuntimeError(
            f"Cannot find configuration field: {field_id}"
        )

    depth = 0
    opened = False
    end_index = None

    for index in range(
        start_index,
        len(content),
    ):
        character = content[index]

        if character == "(":
            depth += 1
            opened = True

        elif character == ")":
            depth -= 1

            if opened and depth == 0:
                end_index = index + 1

                # Include the comma after UIConfigField(...).
                while (
                    end_index < len(content)
                    and content[end_index]
                    in " \t"
                ):
                    end_index += 1

                if (
                    end_index < len(content)
                    and content[end_index] == ","
                ):
                    end_index += 1

                # Include trailing whitespace and one blank line.
                while (
                    end_index < len(content)
                    and content[end_index]
                    in " \t"
                ):
                    end_index += 1

                if (
                    end_index < len(content)
                    and content[end_index] == "\n"
                ):
                    end_index += 1

                if (
                    end_index < len(content)
                    and content[end_index] == "\n"
                ):
                    end_index += 1

                break

    if end_index is None:
        raise RuntimeError(
            f"Cannot determine the end of configuration field: {field_id}"
        )

    return (
        content[:start_index]
        + content[end_index:]
    )


# =============================================================================
# Individual modifications
# =============================================================================


def update_input_schema(
    content: str,
) -> str:
    content = replace_once(
        content,
        '''    image_path: str = Field(
        ...,
        title="ChArUco Reference Image",
        description=UIDataType.STRING.value,
    )''',
        '''    image_path: str = Field(
        ...,
        title="ChArUco Reference Image Path",
        description=UIDataType.STRING.value,
    )''',
        "reference image input title",
    )

    content = replace_once(
        content,
        '''    camera_profile_json: Dict[str, Any] = Field(
        ...,
        title="Intrinsic Camera Profile",
        description=UIDataType.JSON.value,
    )''',
        '''    camera_matrix_json: List[List[float]] = Field(
        ...,
        title="Camera Matrix K",
        description=UIDataType.JSON.value,
    )

    distortion_coefficients_json: List[float] = Field(
        ...,
        title="Distortion Coefficients D",
        description=UIDataType.JSON.value,
    )''',
        "manual K and D inputs",
    )

    content = replace_once(
        content,
        '''    board_info_json: Dict[str, Any] = Field(
        ...,
        title="ChArUco Board Config",
        description=UIDataType.JSON.value,
    )''',
        '''    board_config_file_path: str = Field(
        ...,
        title="ChArUco Board Config File Path",
        description=UIDataType.STRING.value,
    )''',
        "board config file-path input",
    )

    return content


def simplify_config_fields(
    content: str,
) -> str:
    fields_to_remove = [
        "world_origin_mode",
        "require_image_size_match",
        "pose_solver",
        "ransac_iterations",
        "ransac_reprojection_error_px",
        "ransac_confidence",
        "minimum_positive_depth_ratio",
    ]

    for field_id in fields_to_remove:
        content = remove_config_field(
            content,
            field_id,
        )

    # More appropriate defaults for a deliberately captured reference image.
    content = replace_once(
        content,
        '''            id="min_charuco_corners",
            label="Minimum ChArUco Corners",
            type=UIConfigType.NUMBER.value,
            default=12,''',
        '''            id="min_charuco_corners",
            label="Minimum ChArUco Corners",
            type=UIConfigType.NUMBER.value,
            default=15,''',
        "minimum corner default",
    )

    content = replace_once(
        content,
        '''            id="min_corner_ratio",
            label="Minimum ChArUco Corner Ratio",
            type=UIConfigType.NUMBER.value,
            default=0.30,''',
        '''            id="min_corner_ratio",
            label="Minimum ChArUco Corner Ratio",
            type=UIConfigType.NUMBER.value,
            default=0.50,''',
        "minimum corner-ratio default",
    )

    content = replace_once(
        content,
        '''            id="max_reprojection_rmse_px",
            label="Maximum Extrinsics RMSE (px)",
            type=UIConfigType.NUMBER.value,
            default=1.0,''',
        '''            id="max_reprojection_rmse_px",
            label="Maximum Extrinsics RMSE (px)",
            type=UIConfigType.NUMBER.value,
            default=0.8,''',
        "maximum extrinsics RMSE default",
    )

    return content


def fix_world_coordinate_definition(
    content: str,
) -> str:
    replacement = '''        # The world-coordinate convention is fixed:
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
        )'''

    content = replace_between(
        content,
        '''        world_origin_mode = str(
            self.get_config_field_value(''',
        '''        # Rebase all ChArUco corner coordinates''',
        replacement,
        "fixed ChArUco coordinate convention",
    )

    return content


def remove_image_size_matching(
    content: str,
) -> str:
    replacement = '''        # No hard image-size comparison is performed.
        #
        # K and D are copied manually into this node. The engineer is
        # responsible for ensuring that they belong to the same camera,
        # lens, focus, ROI, crop, and image resolution as this image.'''

    content = replace_between(
        content,
        '''        required_size = intrinsic_data.get(
            "image_size"
        )''',
        '''        gray = cv2.cvtColor(''',
        replacement,
        "intrinsic image-size matching",
    )

    return content


def make_solver_internal(
    content: str,
) -> str:
    # Ignore any old serialized pose_solver value.
    content = replace_between(
        content,
        '''        solver = str(
            self.get_config_field_value(''',
        '''        minimum_positive_depth_ratio = (''',
        '''        # Solver strategy is internal and deliberately hidden from
        # the engineer-facing UI.
        solver = "IPPE_THEN_ITERATIVE"''',
        "internal pose-solver selection",
    )

    # All board points must be in front of the camera.
    content = replace_between(
        content,
        '''        minimum_positive_depth_ratio = (''',
        '''        candidates: List[''',
        '''        # This is a fixed physical rule rather than a tunable
        # quality parameter.
        minimum_positive_depth_ratio = 1.0''',
        "fixed positive-depth requirement",
    )

    old_branch_start = '''        elif solver in {
            "IPPE_THEN_ITERATIVE",
            "ITERATIVE",
        }:'''

    old_branch_end = '''        else:
            raise ValueError(
                "Unknown pose_solver: "
                + solver
            )'''

    new_branch = '''        elif solver in {
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
                pass'''

    content = replace_between(
        content,
        old_branch_start,
        old_branch_end,
        new_branch,
        "IPPE multi-solution pose branch",
    )

    return content


def update_execute_inputs(
    content: str,
) -> str:
    content = replace_once(
        content,
        '''        image_path = Path(
            self.local_input.image_path
        ).expanduser()

        fallback_output_folder = (''',
        '''        image_path = Path(
            self.local_input.image_path
        ).expanduser()

        board_config_path = Path(
            self.local_input
            .board_config_file_path
        ).expanduser()

        fallback_output_folder = (''',
        "board config path initialization",
    )

    content = replace_once(
        content,
        '''            "reference_image": str(
                image_path.resolve()
            ),
            "pose_success": False,''',
        '''            "reference_image": str(
                image_path.resolve()
            ),
            "board_config_file": str(
                board_config_path.resolve()
            ),
            "pose_success": False,''',
        "board config path in result",
    )

    new_loading_block = '''            intrinsic_data = (
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
            )'''

    content = replace_between(
        content,
        '''            intrinsic_data = (
                self._extract_camera_profile(''',
        '''            detection = (''',
        new_loading_block,
        "manual K/D and board-file loading",
    )

    # image_size and distortion_model are no longer obtained from a complete
    # intrinsic profile. Record the size of the actual reference image.
    content = replace_once(
        content,
        '''                "calibration_image_size": (
                    intrinsic_data[
                        "image_size"
                    ]
                ),
                "distortion_model": (
                    intrinsic_data[
                        "distortion_model"
                    ]
                ),''',
        '''                "reference_image_size": (
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
                ),''',
        "intrinsic information in result",
    )

    return content


def improve_debug_origin_display(
    content: str,
) -> str:
    origin_drawing_code = '''        # Explicitly project world origin [0, 0, 0].
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

'''

    content = replace_once(
        content,
        '''        camera_position = transform_data[
            "camera_position_world"
        ]''',
        origin_drawing_code
        + '''        camera_position = transform_data[
            "camera_position_world"
        ]''',
        "world-origin annotation",
    )

    content = replace_once(
        content,
        '''            (
                f"Positive depth: "
                f"{statistics['positive_depth_ratio']:.4f}"
            ),''',
        '''            (
                "All board points in front: "
                f"{statistics['positive_depth_ratio'] >= 1.0}"
            ),''',
        "positive-depth debug text",
    )

    content = replace_once(
        content,
        '''            (
                "World origin: "
                f"{board_data['world_origin_mode']}"
            ),''',
        '''            (
                "World origin: ChArUco ID 0 at pixel "
                f"({origin_pixel[0]}, {origin_pixel[1]})"
            ),
            (
                "Axis convention: native ChArUco X/Y/Z"
            ),''',
        "world-origin debug description",
    )

    content = replace_once(
        content,
        '''                "Green=detected | Red=reprojected | "
                "Yellow=residual"''',
        '''                "Green=detected | Red=reprojected | "
                "Yellow=residual | Magenta=origin"''',
        "debug legend",
    )

    return content


def update_documentation(
    content: str,
) -> str:
    content = replace_once(
        content,
        '''    Default world origin:
        ChArUco chessboard corner ID 0.''',
        '''    World-coordinate convention:
        ChArUco chessboard corner ID 0 is always [0, 0, 0].
        Axis directions remain the native ChArUco X/Y/Z directions.''',
        "node coordinate documentation",
    )

    return content


# =============================================================================
# Validation
# =============================================================================


def validate_result(
    content: str,
) -> None:
    required_fragments = [
        "camera_matrix_json: List[List[float]]",
        "distortion_coefficients_json: List[float]",
        "board_config_file_path: str",
        'world_origin_mode = "CHARUCO_CORNER_0"',
        "cv2.solvePnPGeneric(",
        "minimum_positive_depth_ratio = 1.0",
        "WORLD ORIGIN - CHARUCO ID 0",
        '"image_size_match_check": (',
    ]

    forbidden_fragments = [
        'id="world_origin_mode"',
        'id="require_image_size_match"',
        'id="pose_solver"',
        'id="ransac_iterations"',
        'id="ransac_reprojection_error_px"',
        'id="ransac_confidence"',
        'id="minimum_positive_depth_ratio"',
        ".camera_profile_json",
        ".board_info_json",
    ]

    for fragment in required_fragments:
        if fragment not in content:
            raise RuntimeError(
                "Patch validation failed. Missing: "
                + fragment
            )

    for fragment in forbidden_fragments:
        if fragment in content:
            raise RuntimeError(
                "Patch validation failed. "
                "Obsolete fragment remains: "
                + fragment
            )

    compile(
        content,
        "<simplified_charuco_extrinsics>",
        "exec",
    )


# =============================================================================
# Main
# =============================================================================


def default_output_path(
    source_path: Path,
) -> Path:
    return source_path.with_name(
        source_path.stem
        + "_simplified"
        + source_path.suffix
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Simplify the ChArUco extrinsics node interface "
            "while retaining robust pose filtering and debug output."
        )
    )

    parser.add_argument(
        "source",
        type=Path,
        help="Path to the existing charuco_find_extrinsics.py file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            "Output Python file. Defaults to "
            "<source_stem>_simplified.py."
        ),
    )

    args = parser.parse_args()

    source_path = (
        args.source
        .expanduser()
        .resolve()
    )

    output_path = (
        args.output
        .expanduser()
        .resolve()
        if args.output is not None
        else default_output_path(
            source_path
        )
    )

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source file does not exist: {source_path}"
        )

    content = source_path.read_text(
        encoding="utf-8",
    )

    content = update_input_schema(
        content
    )

    content = simplify_config_fields(
        content
    )

    content = fix_world_coordinate_definition(
        content
    )

    content = remove_image_size_matching(
        content
    )

    content = make_solver_internal(
        content
    )

    content = update_execute_inputs(
        content
    )

    content = improve_debug_origin_display(
        content
    )

    content = update_documentation(
        content
    )

    validate_result(
        content
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        content,
        encoding="utf-8",
    )

    print(
        "ChArUco extrinsics node simplified successfully."
    )
    print(f"Source : {source_path}")
    print(f"Output : {output_path}")


if __name__ == "__main__":
    main()
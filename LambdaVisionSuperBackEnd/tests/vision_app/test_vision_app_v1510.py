from types import SimpleNamespace

import numpy as np

from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.models import (
    NormalizedRect,
    UtilitiesConfig,
    UtilityActiveGatherConfig,
    UtilityGatherAugmentation,
    UtilityGatherPlan,
    UtilityGatherRoi,
    UtilityGatherRoute,
    VisionProgramDefinition,
    WorkspaceDefinition,
)
from app.services.vision_app.utilities_runtime import UtilityGatherRuntime


def _image():
    yy, xx = np.mgrid[:120, :160]
    return np.dstack([(xx % 255).astype(np.uint8), (yy % 255).astype(np.uint8), ((xx + yy) % 255).astype(np.uint8)])


def _plan(root, *, augmentation=True):
    return UtilityGatherPlan(
        base_dir=str(root),
        routes=[
            UtilityGatherRoute(output_id='__full__', destination='full'),
            UtilityGatherRoute(output_id='pem', destination='pem'),
        ],
        rois=[UtilityGatherRoi(roi_id='pem', name='PEM', rect=NormalizedRect(x=.25, y=.25, w=.35, h=.35))],
        augmentation=UtilityGatherAugmentation(
            enabled=augmentation,
            include_original=True,
            extra_variants=4 if augmentation else 0,
            shift_x_pct=.05,
            shift_y_pct=.05,
            min_scale=1.0,
            max_scale=1.10,
            min_iou=.70,
        ),
    )


def test_roi_sampling_augmentation_is_deterministic_and_multiplies_samples(tmp_path):
    runtime = UtilityGatherRuntime()
    plan = _plan(tmp_path)
    result = runtime.save_frame(_image(), plan, stem='part_001')
    assert result['failed_count'] == 0
    assert result['saved_count'] == 6  # full + original ROI + four deterministic variants
    assert len(list((tmp_path / 'full').glob('*.jpg'))) == 1
    assert len(list((tmp_path / 'pem').glob('*.jpg'))) == 5

    roi = plan.rois[0]
    first = runtime._variant_rects(roi, plan.augmentation, seed_stem='fixed')
    second = runtime._variant_rects(roi, plan.augmentation, seed_stem='fixed')
    assert first == second
    assert first[0][0] == 'orig'
    assert all(runtime._iou(runtime._rect_tuple(roi.rect), rect) >= .70 for _, rect in first)


def test_workspace_utilities_config_defaults_off():
    ws = WorkspaceDefinition(workspace_id='workspace_1')
    assert ws.utilities.gathering.mode == 'off'
    assert ws.utilities.gathering.samples_per_cycle == 1
    assert ws.utilities.gathering.plan.augmentation.include_original is True


class _Repo:
    def __init__(self, program): self.program = program
    def get(self, program_id):
        assert program_id == self.program.program_id
        return self.program


def _program(tmp_path, mode):
    plan = UtilityGatherPlan(
        base_dir=str(tmp_path),
        routes=[UtilityGatherRoute(output_id='__full__', destination='frames')],
        rois=[],
    )
    ws = WorkspaceDefinition(
        workspace_id='workspace_1',
        alias='front',
        utilities=UtilitiesConfig(gathering=UtilityActiveGatherConfig(mode=mode, plan=plan, samples_per_cycle=1, interval_ms=0)),
    )
    return VisionProgramDefinition(program_id='program_1', name='Program', workspaces=[ws], active_workspace_id='workspace_1')


def test_both_mode_gathers_primary_frame_then_runs_working_on_same_frame(tmp_path):
    program = _program(tmp_path, 'both')
    manager = AutomationManager(repository=_Repo(program))
    seen = {}
    working = SimpleNamespace(overall_ok=True)

    def fake_run(program_id, image=None, workspace_alias=None):
        seen['image'] = np.ascontiguousarray(image.copy())
        seen['workspace'] = workspace_alias
        return working

    manager.run_inspection = fake_run  # type: ignore[method-assign]
    source = _image()
    cycle = manager.run_workspace_cycle('program_1', image=source, workspace_alias='front')
    assert cycle['mode'] == 'both'
    assert cycle['working'] is working
    assert cycle['utilities']['saved_count'] == 1
    assert np.array_equal(seen['image'], source)
    assert seen['workspace'] == 'front'


def test_utilities_only_never_calls_working(tmp_path):
    program = _program(tmp_path, 'utilities_only')
    manager = AutomationManager(repository=_Repo(program))

    def should_not_run(*args, **kwargs):
        raise AssertionError('Working must not execute in utilities_only mode')

    manager.run_inspection = should_not_run  # type: ignore[method-assign]
    cycle = manager.run_workspace_cycle('program_1', image=_image(), workspace_alias='front')
    assert cycle['working'] is None
    assert cycle['utilities']['samples_processed'] == 1
    assert cycle['utilities']['saved_count'] == 1

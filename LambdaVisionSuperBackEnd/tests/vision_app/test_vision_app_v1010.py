from __future__ import annotations

import numpy as np

from app.services.vision_app.models import MasterRoi, NormalizedRect, VisionProgramDefinition
from app.services.vision_app.runtime import VisionProgramRuntime


class _DebugStore:
    def __init__(self):
        self.images = []

    def new_run(self):
        return "debug-test"

    def put(self, run_id, key, image, **meta):
        self.images.append((key, np.asarray(image).copy(), meta))

    def refs(self, run_id):
        return []


def test_roi_filter_preview_starts_with_roi_crop_not_global_image():
    master = np.zeros((100, 200, 3), dtype=np.uint8)
    test = np.zeros_like(master)
    program = VisionProgramDefinition(program_id="p", name="P")
    program.master.rois = [
        MasterRoi(
            roi_id="roi_1",
            name="ROI 1",
            rect=NormalizedRect(x=0.25, y=0.20, w=0.30, h=0.40),
        )
    ]
    debug = _DebugStore()
    runtime = VisionProgramRuntime(debug_store=debug)

    runtime.preview_scope_filters(program, master, test, scope_id="roi_1")

    assert debug.images
    key, image, meta = debug.images[0]
    assert key == "preview_input"
    assert image.shape[:2] == (40, 60)
    assert meta["scope"] == "roi_1"
    assert meta["phase"] == "input"
    assert "ROI 1" in meta["label"]

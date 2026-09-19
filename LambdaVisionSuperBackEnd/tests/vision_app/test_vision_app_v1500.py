from pathlib import Path

import cv2
import numpy as np

from app.services.vision_app.models import NormalizedRect, UtilityBatchRequest, UtilityGatherPlan, UtilityGatherRoi, UtilityGatherRoute
from app.services.vision_app.utilities_runtime import UtilityGatherRuntime


def _image() -> np.ndarray:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    image[20:60, 50:110] = (10, 120, 240)
    return image


def _plan(root: Path) -> UtilityGatherPlan:
    return UtilityGatherPlan(
        base_dir=str(root),
        routes=[
            UtilityGatherRoute(output_id='__full__', destination='full'),
            UtilityGatherRoute(output_id='pem', destination='pem_ok'),
        ],
        rois=[UtilityGatherRoi(roi_id='pem', name='PEM', rect=NormalizedRect(x=.25, y=.2, w=.3, h=.4))],
    )


def test_utilities_gather_saves_full_frame_and_roi(tmp_path: Path):
    runtime = UtilityGatherRuntime()
    result = runtime.save_frame(_image(), _plan(tmp_path), stem='sample')
    assert result['saved_count'] == 2
    full = cv2.imread(str(tmp_path / 'full' / 'sample.jpg'))
    roi = cv2.imread(str(tmp_path / 'pem_ok' / 'sample.jpg'))
    assert full.shape[:2] == (100, 200)
    assert roi.shape[:2] == (40, 60)


def test_utilities_offline_batch_reuses_one_extraction_plan(tmp_path: Path):
    source = tmp_path / 'raw'
    source.mkdir()
    cv2.imwrite(str(source / 'a.jpg'), _image())
    cv2.imwrite(str(source / 'b.png'), _image())
    plan = _plan(tmp_path / 'out')
    payload = plan.model_dump() if hasattr(plan, 'model_dump') else plan.dict()
    request = UtilityBatchRequest(source_dir=str(source), **payload)
    result = UtilityGatherRuntime().process_folder(request)
    assert result['source_count'] == 2
    assert result['processed_count'] == 2
    assert result['saved_count'] == 4
    assert len(list((tmp_path / 'out' / 'pem_ok').glob('*.jpg'))) == 2

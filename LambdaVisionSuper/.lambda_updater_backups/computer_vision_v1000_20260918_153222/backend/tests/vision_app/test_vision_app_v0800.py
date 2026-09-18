from pathlib import Path
from types import SimpleNamespace
import io

import cv2
import numpy as np

from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.decision_runtime import DecisionScriptError, run_decision_script
from app.services.vision_app.models import (
    CameraConfig,
    MasterRoi,
    NormalizedRect,
    ScopePipelineConfig,
    VisionProgramDefinition,
    WorkingServiceBinding,
)
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.roi_search import locate_all
from app.services.vision_app.runtime import VisionProgramRuntime
from app.services.vision_labs.image.types import ColorSpace, ImageFrame


def _png_bytes(image):
    ok, encoded = cv2.imencode('.png', image)
    assert ok
    return encoded.tobytes()


def test_repository_migrates_v07_contract(tmp_path: Path):
    root = tmp_path / 'legacy'
    root.mkdir()
    (root / 'program.json').write_text('''{
      "version":1,"program_id":"legacy","name":"Legacy",
      "io":{},"master":{"rois":[],"master_shape":[]},
      "working":{"global_services":[],"station_services":{}}
    }''')
    repo = VisionProgramRepository(tmp_path)
    program = repo.get('legacy')
    assert program.version == 2
    assert program.camera.driver == 'manual'
    assert program.master.locator.method == 'manual'
    assert program.working.station_execution == 'sequential'


class _HttpResponse:
    status = 200
    headers = {'content-type': 'image/jpeg'}
    def __init__(self, raw): self.raw = raw
    def read(self): return self.raw
    def __enter__(self): return self
    def __exit__(self, *args): return False


def test_generic_url_camera_capture_and_focus():
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    image[:, 20:25] = 255
    raw = _png_bytes(image)
    seen = []
    def opener(request, timeout=0):
        seen.append((request.full_url, timeout))
        if 'capture' in request.full_url:
            return _HttpResponse(raw)
        return _HttpResponse(b'{"ok":true}')
    camera = CameraController(urlopen=opener)
    config = CameraConfig(driver='url', capture_url='http://pi.local/capture', focus_url_template='http://pi.local/focus?x={x}&y={y}&w={w}&h={h}')
    captured = camera.capture(config)
    assert captured.shape == image.shape
    result = camera.focus(config, x=.5, y=.4, w=1, h=.8)
    assert result['status'] == 200
    assert 'x=0.5' in result['url']


def test_decision_dsl():
    script = '''
if logic["sample"]["score"]["mean"] >= 0.8 and logic_ok:
    result = "OK"
else:
    result = "NG"
'''
    ok, result = run_decision_script(script, {'logic': {'sample': {'score': {'mean': .9}}}, 'logic_ok': True, 'filter_ok': True})
    assert ok and result == 'OK'
    try:
        run_decision_script('import os\nresult="OK"', {})
        assert False, 'import must be rejected'
    except DecisionScriptError:
        pass


class _ServiceRepo:
    def get(self, service_id, version=None):
        lab_type = 'image_processing' if service_id.startswith('filter') else 'sampling_geometry'
        return SimpleNamespace(service_id=service_id, version=1, inputs={'image': SimpleNamespace(type='Image')}, outputs={}, lab_type=lab_type)


class _Run:
    def __init__(self, outputs): self.outputs = outputs


class _ServiceRuntime:
    def run(self, service, inputs):
        artifact = next(iter(inputs.values()))
        if service.service_id.startswith('filter'):
            data = np.asarray(artifact.data).copy()
            data = np.clip(data.astype(np.int16) + 5, 0, 255).astype(np.uint8)
            return _Run({'image': ImageFrame(data=data, color_space=ColorSpace.BGR, source_id='filtered')})
        return _Run({'score': np.array([0.95], dtype=np.float32)})


def test_global_filter_logic_decision_then_station_scope():
    runtime = VisionProgramRuntime(service_repository=_ServiceRepo(), service_runtime=_ServiceRuntime())
    roi = MasterRoi(roi_id='r1', name='Station 1', rect=NormalizedRect(x=.2, y=.2, w=.3, h=.3))
    global_scope = ScopePipelineConfig(
        enable_filter=True,
        filter_services=[WorkingServiceBinding(binding_id='f1', service_id='filter-a', alias='filter')],
        enable_logic=True,
        logic_services=[WorkingServiceBinding(binding_id='l1', service_id='logic-a', alias='sample')],
        enable_decision=True,
    )
    global_scope.decision.script = 'if logic["sample"]["score"]["mean"] > 0.8:\n    result="OK"\nelse:\n    result="NG"\n'
    local_scope = ScopePipelineConfig(enable_logic=True, logic_services=[WorkingServiceBinding(binding_id='l2', service_id='logic-b', alias='local')], enable_decision=True)
    program = VisionProgramDefinition(program_id='p', name='P')
    program.master.rois = [roi]
    program.working.global_scope = global_scope
    program.working.station_scopes = {'r1': local_scope}
    master = np.zeros((100, 120, 3), dtype=np.uint8)
    test = np.zeros_like(master)
    result = runtime.run_test(program, master, test)
    assert result.overall_ok
    assert result.global_scope and result.global_scope.ok
    assert len(result.stations) == 1 and result.stations[0].ok
    assert any(item.phase == 'filter' for item in result.benchmarks)
    assert any(item.phase == 'decision' for item in result.benchmarks)
    assert any(item.key == 'global_filtered_final' for item in result.debug_images)


def test_program_wide_locator_family_manual():
    program = VisionProgramDefinition(program_id='p', name='P')
    program.master.rois = [MasterRoi(roi_id='a', name='A', rect=NormalizedRect(x=.1,y=.1,w=.2,h=.2)), MasterRoi(roi_id='b', name='B', rect=NormalizedRect(x=.5,y=.5,w=.2,h=.2))]
    image = np.zeros((100,100,3), dtype=np.uint8)
    found = locate_all(program.master.rois, image, image, program.master.locator)
    assert [item.method for item in found] == ['manual','manual']

from pathlib import Path

import cv2
import numpy as np

from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import MasterRoi, NormalizedRect, RoiSearchConfig, VisionProgramDefinition
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.roi_search import locate_blur_template, locate_fourier, locate_manual


def test_repository_roundtrip_and_master(tmp_path: Path):
    repo = VisionProgramRepository(tmp_path)
    program = VisionProgramDefinition(program_id="demo", name="Demo")
    repo.save(program)
    assert repo.get("demo").name == "Demo"
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (60, 55), (255, 255, 255), -1)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    shape = repo.save_master_bytes("demo", encoded.tobytes())
    assert shape == [80, 120, 3]
    assert repo.load_master("demo").shape == image.shape


def test_manual_and_blur_template_roi_search():
    master = np.zeros((160, 220, 3), dtype=np.uint8)
    cv2.rectangle(master, (60, 50), (105, 95), (255, 255, 255), -1)
    test = np.zeros_like(master)
    cv2.rectangle(test, (72, 58), (117, 103), (255, 255, 255), -1)
    roi = MasterRoi(
        roi_id="r1",
        name="Station 1",
        rect=NormalizedRect(x=60 / 220, y=50 / 160, w=45 / 220, h=45 / 160),
        search=RoiSearchConfig(method="blur_template", blur_kernel=5, template_threshold=0.4),
    )
    manual = locate_manual(roi, test)
    assert manual.rect == roi.rect
    found = locate_blur_template(roi, master, test)
    assert found.found
    assert abs(found.rect.x * 220 - 72) <= 2
    assert abs(found.rect.y * 160 - 58) <= 2


def test_fourier_phase_search_translation():
    rng = np.random.default_rng(7)
    master = np.zeros((180, 220, 3), dtype=np.uint8)
    patch = rng.integers(0, 255, size=(50, 60), dtype=np.uint8)
    master[60:110, 70:130] = cv2.cvtColor(patch, cv2.COLOR_GRAY2BGR)
    test = np.zeros_like(master)
    test[66:116, 78:138] = cv2.cvtColor(patch, cv2.COLOR_GRAY2BGR)
    roi = MasterRoi(
        roi_id="r2",
        name="Fourier",
        rect=NormalizedRect(x=70 / 220, y=60 / 180, w=60 / 220, h=50 / 180),
        search=RoiSearchConfig(method="fourier"),
    )
    found = locate_fourier(roi, master, test)
    assert found.found
    assert abs(found.rect.x * 220 - 78) < 6
    assert abs(found.rect.y * 180 - 66) < 6


class _Response:
    bits = [True]
    def isError(self):
        return False


class _FakeClient:
    writes = []
    def __init__(self, host, port=502):
        self.host, self.port = host, port
    def connect(self):
        return True
    def close(self):
        pass
    def read_discrete_inputs(self, address, count=1, device_id=1):
        return _Response()
    def read_coils(self, address, count=1, device_id=1):
        return _Response()
    def write_coil(self, address, value, device_id=1):
        self.writes.append((address, value, device_id))
        return _Response()


def test_modbus_controller_contract():
    from app.services.vision_app.models import ModbusIOConfig
    controller = ModbusIOController(client_factory=_FakeClient)
    config = ModbusIOConfig(host="127.0.0.1", trigger_address=4, ok_coil=8, ng_coil=9, pulse_seconds=0.001)
    assert controller.read_trigger(config) is True
    controller.pulse_result(config, ok=True, seconds=0.001)
    assert _FakeClient.writes[-2:] == [(8, True, 1), (8, False, 1)]

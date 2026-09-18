from __future__ import annotations

from threading import Event, Lock, Thread
from time import perf_counter, sleep

from app.services.vision_app.control_runtime import ControlMapperRuntime
from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import TriggerRunnerStatus
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.runtime import VisionProgramRuntime


class VisionTriggerRunnerManager:
    def __init__(self, repository=None, runtime=None, camera=None, io=None) -> None:
        self.repository = repository or VisionProgramRepository()
        self.runtime = runtime or VisionProgramRuntime()
        self.camera = camera or CameraController()
        self.io = io or ModbusIOController()
        self._threads: dict[str, Thread] = {}
        self._stops: dict[str, Event] = {}
        self._status: dict[str, TriggerRunnerStatus] = {}
        self._lock = Lock()

    def status(self, program_id: str) -> TriggerRunnerStatus:
        with self._lock:
            return self._status.get(program_id, TriggerRunnerStatus(program_id=program_id))

    def start(self, program_id: str) -> TriggerRunnerStatus:
        with self._lock:
            thread = self._threads.get(program_id)
            if thread and thread.is_alive():
                return self._status[program_id]
            stop = Event()
            status = TriggerRunnerStatus(program_id=program_id, armed=True)
            self._stops[program_id] = stop
            self._status[program_id] = status
            thread = Thread(target=self._loop, args=(program_id, stop), daemon=True, name=f"vision-trigger-{program_id}")
            self._threads[program_id] = thread
            thread.start()
            return status

    def stop(self, program_id: str) -> TriggerRunnerStatus:
        with self._lock:
            stop = self._stops.get(program_id)
            if stop:
                stop.set()
            status = self._status.get(program_id, TriggerRunnerStatus(program_id=program_id))
            status.armed = False
            return status

    def _loop(self, program_id: str, stop: Event) -> None:
        previous = False
        while not stop.is_set():
            try:
                program = self.repository.get(program_id)
                if not program.io.enabled or not program.camera.enabled or program.camera.driver == "manual":
                    raise RuntimeError("Trigger runner requires enabled I/O and a non-manual Camera driver")
                triggered = self.io.read_trigger(program.io)
                status = self._status[program_id]
                status.last_triggered = triggered
                if triggered and not previous:
                    actions = ControlMapperRuntime.actions_for_modbus_trigger(program.control)
                    if "run_inspection" in actions:
                        cycle_start = perf_counter()
                        status.running_cycle = True
                        try:
                            image = self.camera.capture(program.camera)
                            master = self.repository.load_master(program_id)
                            result = self.runtime.run_test(program, master, image)
                            if "out_ok" in actions and result.overall_ok:
                                self.io.pulse_result(program.io, ok=True)
                            elif "out_ng" in actions and not result.overall_ok:
                                self.io.pulse_result(program.io, ok=False)
                            elif not any(action in actions for action in ("out_ok", "out_ng")):
                                # Backward default: a Modbus inspection trigger also reports its final result.
                                self.io.pulse_result(program.io, ok=result.overall_ok)
                            status.last_result = "OK" if result.overall_ok else "NG"
                            status.last_error = ""
                            status.cycles += 1
                        except Exception as exc:
                            status.last_result = "ERROR"
                            status.last_error = str(exc)
                        finally:
                            status.last_cycle_ms = (perf_counter() - cycle_start) * 1000.0
                            status.running_cycle = False
                previous = triggered
                stop.wait(max(0.01, program.io.poll_interval_ms / 1000.0))
            except Exception as exc:
                with self._lock:
                    status = self._status.setdefault(program_id, TriggerRunnerStatus(program_id=program_id, armed=True))
                    status.last_error = str(exc)
                stop.wait(0.5)
        with self._lock:
            status = self._status.setdefault(program_id, TriggerRunnerStatus(program_id=program_id))
            status.armed = False
            status.running_cycle = False

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import shutil
import sys
import py_compile

VERSION = "0.1.2"
BACKUP_DIRNAME = ".lambda_updater_backups"

OLD_FE = '''  uploadInput: async (\n    sessionId: string,\n    file: File,\n    sourceName = 'image',\n  ): Promise<any> => {\n    // IMPORTANT: use native FormData transport here and DO NOT set Content-Type manually.\n    // The browser must generate the multipart boundary. The shared axiosClient has\n    // application/json as a default header, which can interfere with multipart upload.\n    const formData = new FormData();\n    formData.append('file', file, file.name);\n\n    const controller = new AbortController();\n    const timeoutId = window.setTimeout(() => controller.abort(), 30_000);\n\n    try {\n      const url = `${readGateway()}${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`;\n      const response = await fetch(url, {\n        method: 'POST',\n        body: formData,\n        signal: controller.signal,\n      });\n\n      const contentType = response.headers.get('content-type') || '';\n      let payload: any = null;\n      if (contentType.includes('application/json')) {\n        payload = await response.json();\n      } else {\n        const text = await response.text();\n        payload = text ? { detail: text } : {};\n      }\n\n      if (!response.ok) {\n        const detail = payload?.detail || payload?.message || `HTTP ${response.status}`;\n        throw new Error(`Image upload failed: ${detail}`);\n      }\n\n      return payload;\n    } catch (error: any) {\n      if (error?.name === 'AbortError') {\n        throw new Error('Image upload timed out after 30 seconds');\n      }\n      throw error;\n    } finally {\n      window.clearTimeout(timeoutId);\n    }\n  },\n'''

NEW_FE = '''  uploadInput: async (\n    sessionId: string,\n    file: File,\n    sourceName = 'image',\n  ): Promise<any> => {\n    // Image LAB uses a raw binary upload path. This deliberately avoids multipart\n    // parsing and the shared axios JSON Content-Type. The source name is already\n    // carried by the URL, so no multipart metadata is required.\n    const controller = new AbortController();\n    const timeoutId = window.setTimeout(() => controller.abort(), 30_000);\n\n    try {\n      const url = `${readGateway()}${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`;\n      const bytes = await file.arrayBuffer();\n      const response = await fetch(url, {\n        method: 'POST',\n        body: bytes,\n        signal: controller.signal,\n      });\n\n      const contentType = response.headers.get('content-type') || '';\n      let payload: any = null;\n      if (contentType.includes('application/json')) {\n        payload = await response.json();\n      } else {\n        const text = await response.text();\n        payload = text ? { detail: text } : {};\n      }\n\n      if (!response.ok) {\n        const detail = payload?.detail || payload?.message || `HTTP ${response.status}`;\n        throw new Error(`Image upload failed: ${detail}`);\n      }\n\n      return payload;\n    } catch (error: any) {\n      if (error?.name === 'AbortError') {\n        throw new Error('Image upload timed out after 30 seconds');\n      }\n      throw error;\n    } finally {\n      window.clearTimeout(timeoutId);\n    }\n  },\n'''

OLD_BE = '''@router.post("/sessions/{session_id}/input/{source_name}", summary="Upload an image into session RAM")
async def upload_input(
    session_id: str,
    source_name: str,
    file: UploadFile = File(...),
):
    try:
        session = session_manager.get(session_id)
        raw = await file.read()
        array = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Uploaded file could not be decoded as an image")
        if image.ndim == 2:
            color_space = ColorSpace.GRAY
        elif image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            color_space = ColorSpace.BGR
        else:
            color_space = ColorSpace.BGR
        frame = ImageFrame(data=image, color_space=color_space, source_id=source_name)
        session.set_source(source_name, frame)
        return {
            "success": True,
            "session_id": session_id,
            "source_name": source_name,
            "revision": session.revision,
            "shape": list(frame.shape),
            "color_space": frame.color_space.value,
        }
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)
'''

NEW_BE = '''@router.post("/sessions/{session_id}/input/{source_name}", summary="Upload raw image bytes into session RAM")
async def upload_input(
    session_id: str,
    source_name: str,
    request: Request,
):
    try:
        session = session_manager.get(session_id)
        raw = await request.body()
        if not raw:
            raise ValueError("Image upload body is empty")
        array = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"Uploaded body could not be decoded as an image ({len(raw)} bytes)")
        if image.ndim == 2:
            color_space = ColorSpace.GRAY
        elif image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            color_space = ColorSpace.BGR
        else:
            color_space = ColorSpace.BGR
        frame = ImageFrame(data=image, color_space=color_space, source_id=source_name)
        session.set_source(source_name, frame)
        return {
            "success": True,
            "session_id": session_id,
            "source_name": source_name,
            "revision": session.revision,
            "bytes_received": len(raw),
            "shape": list(frame.shape),
            "color_space": frame.color_space.value,
        }
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)
'''


def find_frontend(start: Path) -> Path | None:
    for p in [start, start.parent, start / "LambdaVisionSuper", start.parent / "LambdaVisionSuper"]:
        if (p / "src/api/imageLabApi.ts").exists():
            return p.resolve()
    return None


def find_backend(start: Path) -> Path | None:
    for p in [start, start.parent, start / "LambdaVisionSuperBackEnd", start.parent / "LambdaVisionSuperBackEnd"]:
        if (p / "app/api/v1/endpoints/image_lab_api.py").exists():
            return p.resolve()
    return None


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label} block, found {count}")
    return text.replace(old, new, 1)


def scan(fe: Path, be: Path) -> int:
    fe_file = fe / "src/api/imageLabApi.ts"
    be_file = be / "app/api/v1/endpoints/image_lab_api.py"
    ft = fe_file.read_text()
    bt = be_file.read_text()
    fe_status = "ALREADY RAW" if NEW_FE in ft else "PATCH NEEDED" if OLD_FE in ft else "UNKNOWN"
    be_status = "ALREADY RAW" if NEW_BE in bt else "PATCH NEEDED" if OLD_BE in bt else "UNKNOWN"
    print("="*78)
    print("IMAGE PROCESSING LAB RAW UPLOAD FIX V0.1.2")
    print("="*78)
    print(f"Frontend : {fe}")
    print(f"Backend  : {be}")
    print(f"FE upload: {fe_status}")
    print(f"BE upload: {be_status}")
    print("\nTransport after patch:")
    print("  File -> ArrayBuffer -> HTTP request body -> request.body() -> cv2.imdecode")
    print("  No FormData / multipart parser / axios JSON header")
    return 0 if fe_status != "UNKNOWN" and be_status != "UNKNOWN" else 2


def apply(fe: Path, be: Path) -> int:
    fe_file = fe / "src/api/imageLabApi.ts"
    be_file = be / "app/api/v1/endpoints/image_lab_api.py"
    ft = fe_file.read_text()
    bt = be_file.read_text()

    if NEW_FE not in ft:
        ft = replace_exact(ft, OLD_FE, NEW_FE, "frontend upload")
    if NEW_BE not in bt:
        bt = replace_exact(bt, OLD_BE, NEW_BE, "backend upload")

    # Request is already imported by the original generated endpoint. If not, make it available.
    first_lines = bt.splitlines()[:8]
    if not any("Request" in line and "fastapi" in line for line in first_lines):
        bt = bt.replace("from fastapi import ", "from fastapi import Request, ", 1)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    fe_backup = fe / BACKUP_DIRNAME / f"image_lab_raw_upload_v0012_{stamp}"
    be_backup = be / BACKUP_DIRNAME / f"image_lab_raw_upload_v0012_{stamp}"
    fe_backup.mkdir(parents=True, exist_ok=True)
    be_backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fe_file, fe_backup / "imageLabApi.ts")
    shutil.copy2(be_file, be_backup / "image_lab_api.py")

    fe_file.write_text(ft)
    be_file.write_text(bt)
    print(f"[PATCH] {fe_file}")
    print(f"[PATCH] {be_file}")
    print(f"[OK] FE backup: {fe_backup}")
    print(f"[OK] BE backup: {be_backup}")
    return 0


def verify(fe: Path, be: Path) -> int:
    fe_file = fe / "src/api/imageLabApi.ts"
    be_file = be / "app/api/v1/endpoints/image_lab_api.py"
    ft = fe_file.read_text()
    bt = be_file.read_text()
    checks = {
        "FE uses ArrayBuffer": "const bytes = await file.arrayBuffer();" in ft,
        "FE sends raw body": "body: bytes," in ft,
        "FE no FormData in upload block": "const formData = new FormData();" not in ft[ft.index("uploadInput: async"):ft.index("setPipeline: async")],
        "BE reads request.body": "raw = await request.body()" in bt,
        "BE reports bytes_received": '"bytes_received": len(raw)' in bt,
        "BE no UploadFile parameter": "file: UploadFile = File(...)" not in bt,
    }
    for name, ok in checks.items():
        print(f"[{'OK' if ok else 'FAIL'}] {name}")
    try:
        py_compile.compile(str(be_file), doraise=True)
        print("[OK] Backend Python syntax")
    except Exception as exc:
        print(f"[FAIL] Backend Python syntax: {exc}")
        checks["syntax"] = False
    if not all(checks.values()):
        return 2
    print("[OK] Image LAB raw upload transport verified.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["scan", "apply", "verify"])
    ap.add_argument("--frontend", type=Path)
    ap.add_argument("--backend", type=Path)
    args = ap.parse_args()
    cwd = Path.cwd().resolve()
    fe = args.frontend.resolve() if args.frontend else find_frontend(cwd)
    be = args.backend.resolve() if args.backend else find_backend(cwd)
    if not fe or not be:
        print("[ERROR] Could not locate both LambdaVisionSuper and LambdaVisionSuperBackEnd.")
        print("Use --frontend /path/to/LambdaVisionSuper --backend /path/to/LambdaVisionSuperBackEnd")
        return 2
    if args.command == "scan": return scan(fe, be)
    if args.command == "apply": return apply(fe, be)
    return verify(fe, be)

if __name__ == "__main__":
    raise SystemExit(main())

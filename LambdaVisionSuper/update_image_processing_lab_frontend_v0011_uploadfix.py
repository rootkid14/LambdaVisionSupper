#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import shutil
import sys

VERSION = "0.1.1"
BACKUP_DIRNAME = ".lambda_updater_backups"

OLD_BLOCK = '''  uploadInput: async (\n    sessionId: string,\n    file: File,\n    sourceName = 'image',\n  ): Promise<any> => {\n    const formData = new FormData();\n    formData.append('file', file);\n    const response = await axiosClient.post(\n      `${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`,\n      formData,\n      { headers: { 'Content-Type': 'multipart/form-data' } },\n    );\n    return response.data;\n  },\n'''

NEW_BLOCK = '''  uploadInput: async (\n    sessionId: string,\n    file: File,\n    sourceName = 'image',\n  ): Promise<any> => {\n    // IMPORTANT: use native FormData transport here and DO NOT set Content-Type manually.\n    // The browser must generate the multipart boundary. The shared axiosClient has\n    // application/json as a default header, which can interfere with multipart upload.\n    const formData = new FormData();\n    formData.append('file', file, file.name);\n\n    const controller = new AbortController();\n    const timeoutId = window.setTimeout(() => controller.abort(), 30_000);\n\n    try {\n      const url = `${readGateway()}${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`;\n      const response = await fetch(url, {\n        method: 'POST',\n        body: formData,\n        signal: controller.signal,\n      });\n\n      const contentType = response.headers.get('content-type') || '';\n      let payload: any = null;\n      if (contentType.includes('application/json')) {\n        payload = await response.json();\n      } else {\n        const text = await response.text();\n        payload = text ? { detail: text } : {};\n      }\n\n      if (!response.ok) {\n        const detail = payload?.detail || payload?.message || `HTTP ${response.status}`;\n        throw new Error(`Image upload failed: ${detail}`);\n      }\n\n      return payload;\n    } catch (error: any) {\n      if (error?.name === 'AbortError') {\n        throw new Error('Image upload timed out after 30 seconds');\n      }\n      throw error;\n    } finally {\n      window.clearTimeout(timeoutId);\n    }\n  },\n'''


def find_root(start: Path) -> Path | None:
    start = start.resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "src" / "api" / "imageLabApi.ts").exists():
            return candidate
        if (candidate / "api" / "imageLabApi.ts").exists():
            return candidate
    return None


def api_path(root: Path) -> Path:
    p = root / "src" / "api" / "imageLabApi.ts"
    if p.exists():
        return p
    return root / "api" / "imageLabApi.ts"


def status(root: Path) -> tuple[str, Path]:
    path = api_path(root)
    if not path.exists():
        return "MISSING", path
    text = path.read_text(encoding="utf-8")
    if NEW_BLOCK in text:
        return "ALREADY FIXED", path
    if OLD_BLOCK in text:
        return "PATCH NEEDED", path
    if "uploadInput: async" in text:
        return "UNKNOWN VARIANT", path
    return "UPLOAD FUNCTION MISSING", path


def scan(root: Path) -> int:
    st, path = status(root)
    print("=" * 78)
    print("IMAGE PROCESSING LAB FE UPLOAD FIX V0.1.1")
    print("=" * 78)
    print(f"Project : {root}")
    print(f"Target  : {path}")
    print(f"Status  : {st}")
    print()
    print("Fixes:")
    print("  - remove manual multipart/form-data header")
    print("  - bypass axiosClient JSON default for file upload")
    print("  - let browser generate multipart boundary")
    print("  - add 30 second upload timeout")
    print("  - surface backend error detail to FE")
    if st == "PATCH NEEDED":
        print("\nNext:\n  python update_image_processing_lab_frontend_v0011_uploadfix.py apply")
        return 0
    return 0 if st == "ALREADY FIXED" else 2


def apply(root: Path) -> int:
    st, path = status(root)
    if st == "ALREADY FIXED":
        print("[OK] Upload fix already applied.")
        return 0
    if st != "PATCH NEEDED":
        print(f"[ERROR] Refusing to patch: {st}")
        print(f"        Target: {path}")
        return 2

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / BACKUP_DIRNAME / f"image_lab_frontend_v0011_uploadfix_{stamp}"
    backup_target = backup_dir / path.relative_to(root)
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_target)

    text = path.read_text(encoding="utf-8")
    count = text.count(OLD_BLOCK)
    if count != 1:
        print(f"[ERROR] Expected exactly one old upload block, found {count}.")
        return 2
    text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    path.write_text(text, encoding="utf-8")

    print(f"[PATCH] {path.relative_to(root)}")
    print(f"[OK] Backup: {backup_dir}")
    print("\nRun:\n  python update_image_processing_lab_frontend_v0011_uploadfix.py verify")
    return 0


def verify(root: Path) -> int:
    st, path = status(root)
    print("=" * 78)
    print("VERIFY IMAGE PROCESSING LAB FE UPLOAD FIX V0.1.1")
    print("=" * 78)
    if st != "ALREADY FIXED":
        print(f"[FAIL] Status: {st}")
        return 2
    text = path.read_text(encoding="utf-8")
    checks = {
        "native fetch upload": "const response = await fetch(url" in text,
        "no forced multipart header": "{ headers: { 'Content-Type': 'multipart/form-data' } }" not in text,
        "30s timeout": "30_000" in text and "AbortController" in text,
        "gateway-aware URL": "readGateway()}${api_version}/image-lab" in text,
        "error detail": "Image upload failed:" in text,
    }
    failed = False
    for name, ok in checks.items():
        print(f"[{'OK' if ok else 'FAIL'}] {name}")
        failed |= not ok
    if failed:
        return 2
    print("[OK] Image Processing LAB frontend upload fix verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["scan", "apply", "verify"])
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = find_root(args.project)
    if root is None:
        print("[ERROR] Cannot find frontend root containing src/api/imageLabApi.ts.")
        print("        Use --project /path/to/LambdaVisionSuper")
        return 2
    if args.command == "scan":
        return scan(root)
    if args.command == "apply":
        return apply(root)
    return verify(root)


if __name__ == "__main__":
    sys.exit(main())

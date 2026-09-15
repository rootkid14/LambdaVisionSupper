#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import py_compile
import shutil
from pathlib import Path


def resolve_roots(frontend_arg, backend_arg):
    cwd = Path.cwd().resolve()
    fe_candidates = []
    be_candidates = []

    if frontend_arg:
        fe_candidates.append(Path(frontend_arg).expanduser().resolve())
    if backend_arg:
        be_candidates.append(Path(backend_arg).expanduser().resolve())

    fe_candidates += [cwd, cwd / "LambdaVisionSuper", cwd.parent / "LambdaVisionSuper"]
    be_candidates += [cwd, cwd / "LambdaVisionSuperBackEnd", cwd.parent / "LambdaVisionSuperBackEnd"]

    frontend = next((p for p in fe_candidates if (p / "src/api/imageLabApi.ts").exists()), None)
    backend = next((p for p in be_candidates if (p / "app/api/v1/endpoints/image_lab_api.py").exists()), None)

    if frontend is None:
        raise RuntimeError("Cannot locate frontend root. Use --frontend /path/to/LambdaVisionSuper")
    if backend is None:
        raise RuntimeError("Cannot locate backend root. Use --backend /path/to/LambdaVisionSuperBackEnd")
    return frontend, backend


def backup(frontend, backend, files):
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    root = frontend / ".lambda_updater_backups" / f"image_lab_upload_transport_v0013_{stamp}"
    root.mkdir(parents=True, exist_ok=True)
    for path in files:
        if not path.exists():
            continue
        try:
            rel = path.relative_to(frontend)
            prefix = Path("frontend")
        except ValueError:
            rel = path.relative_to(backend)
            prefix = Path("backend")
        dest = root / prefix / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return root


def patch_frontend(text):
    marker_start = "  uploadInput: async ("
    marker_end = "\n\n  setPipeline: async ("
    start = text.find(marker_start)
    end = text.find(marker_end, start)
    if start < 0 or end < 0:
        raise RuntimeError("Could not locate ImageLabAPI.uploadInput block")

    new_block = '''  uploadInput: async (
    sessionId: string,
    file: File,
    sourceName = 'image',
  ): Promise<any> => {
    try {
      console.info(
        '[IMAGE LAB] Upload start',
        { sessionId, sourceName, name: file.name, size: file.size, type: file.type },
      );

      const response = await axiosClient.post(
        `${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`,
        file,
        {
          headers: {
            'Content-Type': 'application/octet-stream',
            'X-Image-Filename': encodeURIComponent(file.name),
          },
          timeout: 30_000,
          transformRequest: [(data) => data],
        },
      );

      console.info(
        '[IMAGE LAB] Upload complete',
        { status: response.status, bytesReceived: response.data?.bytes_received },
      );
      return response.data;
    } catch (error: any) {
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        'Unknown upload error';

      if (error?.code === 'ECONNABORTED') {
        throw new Error('Image upload timed out after 30 seconds');
      }
      throw new Error(`Image upload failed: ${detail}`);
    }
  },'''

    updated = text[:start] + new_block + text[end:]
    return updated, updated != text


def patch_backend(text):
    old = '''        session = session_manager.get(session_id)
        raw = await request.body()
        if not raw:
'''
    if old not in text:
        if "[IMAGE LAB UPLOAD] START" in text:
            return text, False
        raise RuntimeError("Could not locate backend raw body receive block")

    new = '''        session = session_manager.get(session_id)

        content_length = request.headers.get("content-length")
        content_type = request.headers.get("content-type")
        filename = request.headers.get("x-image-filename")
        print(
            f"[IMAGE LAB UPLOAD] START sid={session_id} source={source_name} "
            f"length={content_length} type={content_type} file={filename}",
            flush=True,
        )

        try:
            raw = await asyncio.wait_for(request.body(), timeout=15.0)
        except asyncio.TimeoutError as exc:
            print(
                f"[IMAGE LAB UPLOAD] BODY TIMEOUT sid={session_id} source={source_name}",
                flush=True,
            )
            raise HTTPException(
                status_code=408,
                detail="Timed out while receiving image request body",
            ) from exc

        print(
            f"[IMAGE LAB UPLOAD] BODY OK sid={session_id} bytes={len(raw)}",
            flush=True,
        )

        if not raw:
'''
    updated = text.replace(old, new, 1)
    return updated, updated != text


def scan(frontend, backend):
    fe = frontend / "src/api/imageLabApi.ts"
    be = backend / "app/api/v1/endpoints/image_lab_api.py"
    fe_text = fe.read_text(encoding="utf-8")
    be_text = be.read_text(encoding="utf-8")

    upload_slice = fe_text[fe_text.find("uploadInput: async"):fe_text.find("setPipeline: async")]
    fe_ok = (
        "application/octet-stream" in upload_slice
        and "axiosClient.post(" in upload_slice
        and "file.arrayBuffer()" not in upload_slice
        and "fetch(" not in upload_slice
    )
    be_ok = "[IMAGE LAB UPLOAD] START" in be_text

    print("=" * 78)
    print("IMAGE PROCESSING LAB UPLOAD TRANSPORT FIX V0.1.3")
    print("=" * 78)
    print(f"Frontend : {frontend}")
    print(f"Backend  : {backend}")
    print()
    print(f"FE upload transport : {'OK' if fe_ok else 'PATCH NEEDED'}")
    print(f"BE receive tracing  : {'OK' if be_ok else 'PATCH NEEDED'}")
    return 0


def apply(frontend, backend):
    fe = frontend / "src/api/imageLabApi.ts"
    be = backend / "app/api/v1/endpoints/image_lab_api.py"

    fe_old = fe.read_text(encoding="utf-8")
    be_old = be.read_text(encoding="utf-8")
    fe_new, fe_changed = patch_frontend(fe_old)
    be_new, be_changed = patch_backend(be_old)

    if not fe_changed and not be_changed:
        print("[OK] Nothing to patch.")
        return 0

    root = backup(frontend, backend, [fe, be])
    if fe_changed:
        fe.write_text(fe_new, encoding="utf-8")
        print("[PATCH] frontend src/api/imageLabApi.ts")
    if be_changed:
        be.write_text(be_new, encoding="utf-8")
        print("[PATCH] backend app/api/v1/endpoints/image_lab_api.py")

    print(f"[OK] Backup: {root}")
    return 0


def verify(frontend, backend):
    fe = frontend / "src/api/imageLabApi.ts"
    be = backend / "app/api/v1/endpoints/image_lab_api.py"
    fe_text = fe.read_text(encoding="utf-8")
    be_text = be.read_text(encoding="utf-8")
    upload_slice = fe_text[fe_text.find("uploadInput: async"):fe_text.find("setPipeline: async")]

    checks = [
        ("FE uses axiosClient.post", "axiosClient.post(" in upload_slice),
        ("FE sends File directly", "transformRequest: [(data) => data]" in upload_slice),
        ("FE uses application/octet-stream", "'Content-Type': 'application/octet-stream'" in upload_slice),
        ("FE upload has no arrayBuffer", "file.arrayBuffer()" not in upload_slice),
        ("FE upload has no native fetch", "fetch(" not in upload_slice),
        ("BE logs endpoint entry", "[IMAGE LAB UPLOAD] START" in be_text),
        ("BE has body receive timeout", "asyncio.wait_for(request.body(), timeout=15.0)" in be_text),
        ("BE logs body completion", "[IMAGE LAB UPLOAD] BODY OK" in be_text),
    ]

    print("=" * 78)
    print("VERIFY IMAGE PROCESSING LAB UPLOAD TRANSPORT FIX V0.1.3")
    print("=" * 78)

    failed = False
    for label, ok in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label}")
        failed = failed or not ok

    try:
        py_compile.compile(str(be), doraise=True)
        print("[OK] Backend Python syntax")
    except Exception as exc:
        print(f"[FAIL] Backend Python syntax: {exc}")
        failed = True

    if failed:
        return 1

    print("[OK] Image LAB upload transport v0.1.3 verified.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["scan", "apply", "verify"])
    parser.add_argument("--frontend")
    parser.add_argument("--backend")
    args = parser.parse_args()

    try:
        frontend, backend = resolve_roots(args.frontend, args.backend)
        if args.command == "scan":
            return scan(frontend, backend)
        if args.command == "apply":
            return apply(frontend, backend)
        return verify(frontend, backend)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

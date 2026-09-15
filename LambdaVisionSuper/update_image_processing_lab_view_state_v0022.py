#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import subprocess
from pathlib import Path


VERSION = "0.2.2"


def resolve_frontend(frontend_arg: str | None) -> Path:
    cwd = Path.cwd().resolve()
    candidates = []

    if frontend_arg:
        candidates.append(Path(frontend_arg).expanduser().resolve())

    candidates += [
        cwd,
        cwd / "LambdaVisionSuper",
        cwd.parent / "LambdaVisionSuper",
    ]

    frontend = next(
        (
            p for p in candidates
            if (
                p
                / "src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx"
            ).exists()
            and (
                p
                / "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
            ).exists()
        ),
        None,
    )

    if frontend is None:
        raise RuntimeError(
            "Cannot locate Lambda Vision frontend. "
            "Use --frontend /path/to/LambdaVisionSuper"
        )

    return frontend


def backup(frontend: Path, paths: list[Path]) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    root = (
        frontend
        / ".lambda_updater_backups"
        / f"image_lab_view_state_v0022_{stamp}"
    )
    root.mkdir(parents=True, exist_ok=True)

    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(frontend)
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    return root


def patch_zoom_view(text: str) -> tuple[str, bool]:
    changed = False

    old_props = """interface Props {
  src?: string;
  alt: string;
}"""
    new_props = """interface Props {
  src?: string;
  alt: string;

  // Reset the camera only when the logical viewer source changes.
  // The preview blob URL is allowed to change continuously (e.g. Latest)
  // without destroying the user's zoom/pan state.
  resetKey?: string;
}"""
    if old_props in text:
        text = text.replace(old_props, new_props, 1)
        changed = True

    old_sig = "export const ZoomPanImageView = ({ src, alt }: Props) => {"
    new_sig = "export const ZoomPanImageView = ({ src, alt, resetKey }: Props) => {"
    if old_sig in text:
        text = text.replace(old_sig, new_sig, 1)
        changed = True

    old_effect = """  useEffect(() => {
    resetView();
  }, [src, resetView]);"""
    new_effect = """  useEffect(() => {
    resetView();
  }, [resetKey, resetView]);"""
    if old_effect in text:
        text = text.replace(old_effect, new_effect, 1)
        changed = True

    if (
        "resetKey?: string;" not in text
        or "({ src, alt, resetKey }: Props)" not in text
        or "}, [resetKey, resetView]);" not in text
    ):
        raise RuntimeError(
            "ZoomPanImageView.tsx did not match the expected v0.2.1 structure."
        )

    return text, changed


def patch_workbench(text: str) -> tuple[str, bool]:
    changed = False

    old_import = "import { useRef, useState, type CSSProperties } from 'react';"
    new_import = "import { useEffect, useRef, useState, type CSSProperties } from 'react';"
    if old_import in text:
        text = text.replace(old_import, new_import, 1)
        changed = True

    old_icons = """  Loader2,
  Play,
  Plus,
  RotateCcw,
  Square,
  X,"""
    new_icons = """  Loader2,
  Maximize2,
  Minimize2,
  Play,
  Plus,
  RotateCcw,
  Square,
  X,"""
    if old_icons in text:
        text = text.replace(old_icons, new_icons, 1)
        changed = True

    old_resize_state = """  const [size, setSize] = useState<{
    width: number;
    height: number;
  } | null>(null);

  const selected = sources.find("""
    new_resize_state = """  const [size, setSize] = useState<{
    width: number;
    height: number;
  } | null>(null);

  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(
        document.fullscreenElement === paneRef.current,
      );
    };

    document.addEventListener(
      'fullscreenchange',
      handleFullscreenChange,
    );

    return () => {
      document.removeEventListener(
        'fullscreenchange',
        handleFullscreenChange,
      );
    };
  }, []);

  const toggleFullscreen = async () => {
    const paneElement = paneRef.current;
    if (!paneElement) return;

    try {
      if (document.fullscreenElement === paneElement) {
        await document.exitFullscreen();
      } else {
        await paneElement.requestFullscreen();
      }
    } catch (error) {
      console.error(
        '[IMAGE LAB] Failed to toggle full view',
        error,
      );
    }
  };

  const selected = sources.find("""
    if old_resize_state in text:
        text = text.replace(old_resize_state, new_resize_state, 1)
        changed = True

    old_style = """      style={
        size
          ? {
              flex: '0 0 auto',
              width: size.width,
              height: size.height,
            }
          : defaultPaneStyle(paneCount)
      }"""
    new_style = """      style={
        isFullscreen
          ? {
              flex: '0 0 auto',
              width: '100vw',
              height: '100vh',
            }
          : size
            ? {
                flex: '0 0 auto',
                width: size.width,
                height: size.height,
              }
            : defaultPaneStyle(paneCount)
      }"""
    if old_style in text:
        text = text.replace(old_style, new_style, 1)
        changed = True

    old_buttons = """        {size && (
          <button
            onClick={() => setSize(null)}
            title="Reset pane size"
            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
          >
            <RotateCcw size={12} />
          </button>
        )}

        {paneCount > 1 && ("""
    new_buttons = """        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit full view' : 'Full view'}
          className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
        >
          {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
        </button>

        {size && !isFullscreen && (
          <button
            onClick={() => setSize(null)}
            title="Reset pane size"
            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
          >
            <RotateCcw size={12} />
          </button>
        )}

        {paneCount > 1 && !isFullscreen && ("""
    if old_buttons in text:
        text = text.replace(old_buttons, new_buttons, 1)
        changed = True

    old_zoom_call = """          <ZoomPanImageView
            src={url}
            alt={
              selected?.label
              ?? 'Image LAB preview'
            }
          />"""
    new_zoom_call = """          <ZoomPanImageView
            src={url}
            alt={
              selected?.label
              ?? 'Image LAB preview'
            }
            resetKey={`${pane.id}:${selected?.key ?? 'latest'}`}
          />"""
    if old_zoom_call in text:
        text = text.replace(old_zoom_call, new_zoom_call, 1)
        changed = True

    old_resize_handle = """      <div
        role="separator"
        aria-label="Resize viewer"
        title="Drag to resize this view"
        className="absolute bottom-0 right-0 z-30 h-5 w-5 cursor-nwse-resize" """
    # Don't rely on the exact trailing spacing; guard by injecting conditional
    # wrapper around the existing resize handle if it has not been wrapped yet.
    if "{!isFullscreen && (" not in text:
        marker = """      <div
        role="separator"
        aria-label="Resize viewer\""""
        if marker in text:
            start = text.find(marker)
            # Find the end of the resize handle by the unique trailing child block.
            end_marker = """      </div>
    </section>"""
            end = text.find(end_marker, start)
            if end < 0:
                raise RuntimeError("Could not locate the end of viewer resize handle.")
            handle_block = text[start:end + len("      </div>")]
            wrapped = """      {!isFullscreen && (
        <>
""" + handle_block + """
        </>
      )}"""
            text = text[:start] + wrapped + text[end + len("      </div>"):]
            changed = True

    required = [
        "resetKey={`${pane.id}:${selected?.key ?? 'latest'}`}",
        "const [isFullscreen, setIsFullscreen] = useState(false);",
        "paneElement.requestFullscreen()",
        "document.exitFullscreen()",
        "Maximize2",
        "Minimize2",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(
            "ImageWorkbench.tsx did not match expected v0.2.1 structure. "
            f"Missing after patch: {missing}"
        )

    return text, changed


def scan(frontend: Path) -> int:
    zoom = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx"
    )
    workbench = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
    )

    zoom_text = zoom.read_text(encoding="utf-8")
    workbench_text = workbench.read_text(encoding="utf-8")

    zoom_ok = (
        "resetKey?: string;" in zoom_text
        and "}, [resetKey, resetView]);" in zoom_text
    )
    full_ok = (
        "requestFullscreen()" in workbench_text
        and "resetKey={`${pane.id}:${selected?.key ?? 'latest'}`}" in workbench_text
    )

    print("=" * 80)
    print("IMAGE PROCESSING LAB VIEW STATE / FULL VIEW V0.2.2")
    print("=" * 80)
    print(f"Frontend : {frontend}")
    print()
    print(f"Latest zoom/pan persistence : {'OK' if zoom_ok else 'PATCH NEEDED'}")
    print(f"Per-pane Full View          : {'OK' if full_ok else 'PATCH NEEDED'}")
    print()
    print("Behavior:")
    print("  - Latest preview blob may change without resetting zoom/pan.")
    print("  - Changing the viewer dropdown source resets that viewer to fit.")
    print("  - Full View uses the same pane/component, so zoom/pan state is preserved.")
    print("  - ESC or the Minimize button exits Full View.")
    return 0


def apply(frontend: Path) -> int:
    zoom = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx"
    )
    workbench = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
    )

    zoom_old = zoom.read_text(encoding="utf-8")
    workbench_old = workbench.read_text(encoding="utf-8")

    zoom_new, zoom_changed = patch_zoom_view(zoom_old)
    workbench_new, workbench_changed = patch_workbench(workbench_old)

    if not zoom_changed and not workbench_changed:
        print("[OK] Nothing to patch.")
        return 0

    backup_root = backup(frontend, [zoom, workbench])

    if zoom_changed:
        zoom.write_text(zoom_new, encoding="utf-8")
        print("[PATCH] ZoomPanImageView.tsx")

    if workbench_changed:
        workbench.write_text(workbench_new, encoding="utf-8")
        print("[PATCH] ImageWorkbench.tsx")

    print(f"[OK] Backup: {backup_root}")
    print("Run verify next.")
    return 0


def verify(frontend: Path, skip_build: bool) -> int:
    zoom = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx"
    )
    workbench = (
        frontend
        / "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
    )

    zoom_text = zoom.read_text(encoding="utf-8")
    workbench_text = workbench.read_text(encoding="utf-8")

    checks = [
        (
            "ZoomPanImageView has logical resetKey",
            "resetKey?: string;" in zoom_text,
        ),
        (
            "Preview src change no longer resets camera",
            "}, [src, resetView]);" not in zoom_text,
        ),
        (
            "Logical source change resets camera",
            "}, [resetKey, resetView]);" in zoom_text,
        ),
        (
            "Workbench passes stable pane/source reset key",
            "resetKey={`${pane.id}:${selected?.key ?? 'latest'}`}" in workbench_text,
        ),
        (
            "Pane supports browser Fullscreen API",
            "paneElement.requestFullscreen()" in workbench_text,
        ),
        (
            "Pane can exit Full View",
            "document.exitFullscreen()" in workbench_text,
        ),
        (
            "Fullscreen state tracks ESC/browser exit",
            "'fullscreenchange'" in workbench_text,
        ),
        (
            "Full View controls use maximize/minimize icons",
            "Maximize2" in workbench_text and "Minimize2" in workbench_text,
        ),
    ]

    print("=" * 80)
    print("VERIFY IMAGE PROCESSING LAB VIEW STATE / FULL VIEW V0.2.2")
    print("=" * 80)

    failed = False
    for label, ok in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label}")
        failed = failed or not ok

    if (
        not skip_build
        and (frontend / "package.json").exists()
        and (frontend / "node_modules").exists()
    ):
        proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(frontend),
        )
        if proc.returncode == 0:
            print("[OK] Frontend npm build")
        else:
            print("[FAIL] Frontend npm build")
            failed = True
    else:
        print("[SKIP] Frontend npm build")

    if failed:
        print("[FAIL] Verification failed.")
        return 1

    print("[OK] Image Processing LAB v0.2.2 verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["scan", "apply", "verify"],
    )
    parser.add_argument("--frontend")
    parser.add_argument(
        "--skip-build",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        frontend = resolve_frontend(args.frontend)

        if args.command == "scan":
            return scan(frontend)

        if args.command == "apply":
            return apply(frontend)

        return verify(
            frontend,
            skip_build=args.skip_build,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import datetime as dt
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".vite",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".lambda_updater_backups",
    ".venv",
    "venv",
    "env",
    ".env",
    "storage",
    "logs",
    "log",
    "datasets",
    "dataset",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".txt",
    ".css",
    ".scss",
    ".html",
    ".sh",
    ".ps1",
    ".bat",
}

MAX_SYMBOL_BYTES = 256_000


def git_info(root: Path) -> tuple[str, str]:
    def run(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(root),
                text=True,
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    return (
        run("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        run("rev-parse", "--short", "HEAD") or "unknown",
    )


def should_ignore(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True

    return any(part in IGNORED_DIRS for part in relative.parts)


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for current, dirs, names in os.walk(root):
        current_path = Path(current)

        dirs[:] = [
            name
            for name in dirs
            if name not in IGNORED_DIRS
            and not should_ignore(current_path / name, root)
        ]

        for name in names:
            path = current_path / name

            if should_ignore(path, root):
                continue

            files.append(path)

    return sorted(files, key=lambda item: str(item.relative_to(root)).lower())


def classify(project: str, relative: Path) -> str:
    parts = relative.parts
    suffix = relative.suffix.lower()
    name = relative.name.lower()
    text = "/".join(parts).lower()

    if "tests" in parts or "test" in parts or name.startswith("test_"):
        return "Tests"

    if "docs" in parts or suffix == ".md":
        return "Documentation"

    if "tools" in parts or "scripts" in parts or name.startswith("update_"):
        return "Tools / Updaters"

    if project == "FE":
        if "src/api" in text:
            return "Frontend API Clients"
        if "src/pages" in text:
            return "Frontend Pages"
        if "src/components" in text:
            if "visionlabs" in text:
                return "Frontend Vision LAB Components"
            return "Frontend Components"
        if "src/store" in text or "src/state" in text or "src/hooks" in text:
            return "Frontend State / Hooks"
        if "src/types" in text or name.endswith("types.ts") or name.endswith("types.tsx"):
            return "Frontend Types"
        if "assets" in parts or suffix in {".png", ".jpg", ".jpeg", ".svg", ".ico"}:
            return "Frontend Assets"
        if name in {"package.json", "vite.config.ts", "vite.config.js", "tsconfig.json"}:
            return "Frontend Build / Config"
        if "src" in parts:
            return "Frontend Source"
        return "Frontend Project / Config"

    if "app/api" in text:
        return "Backend API"
    if "vision_labs/image/operators" in text:
        return "Backend Image LAB Operators"
    if "vision_labs/image" in text:
        return "Backend Image LAB Core"
    if "vision_labs/service" in text:
        return "Backend Lab Service"
    if "vision_labs" in text:
        return "Backend Vision LAB Core"
    if "services" in parts:
        return "Backend Services"
    if "models" in parts or "schemas" in parts:
        return "Backend Models / Schemas"
    if name in {"requirements.txt", "pyproject.toml", "setup.cfg", "pytest.ini"}:
        return "Backend Build / Config"
    if suffix == ".py":
        return "Backend Python Source"

    return "Backend Project / Config"


def infer_purpose(project: str, relative: Path) -> str:
    name = relative.name
    stem = relative.stem
    text = "/".join(relative.parts).lower()

    rules = [
        ("operatorlibrary", "Image Processing LAB operator/filter selector UI."),
        ("filterguidemodal", "Standalone filter guide and isolated test playground UI."),
        ("operatorguide", "Human-readable filter explanations, tuning tips and parameter guidance."),
        ("imageprocessinglabpage", "Top-level Image Processing LAB page and layout."),
        ("imageworkbench", "Image viewer workbench, upload/run controls and multi-view layout."),
        ("processstack", "Image Processing LAB stack editor and operator parameter controls."),
        ("zoompanimageview", "Reusable zoom/pan raster viewer."),
        ("useimagelabcontroller", "Image Processing LAB frontend state/runtime controller."),
        ("imagelabapi", "Frontend client for Image Processing LAB backend APIs."),
        ("labserviceapi", "Frontend client for versioned Lab Service APIs."),
        ("labview", "Vision LAB launcher and deployed Lab Service hub."),
        ("advanced_families", "Advanced pure-raster Image LAB operator implementations."),
        ("basic_families", "Basic Image LAB operator family implementations."),
        ("builtins", "Core/builtin Image LAB operator implementations."),
        ("registry", "Operator or service registry and discovery logic."),
        ("pipeline", "Pipeline definition, validation, compilation or graph contracts."),
        ("runtime", "Runtime execution orchestration."),
        ("repository", "Persistent repository/storage access and version management."),
        ("models", "Data models and serialized contracts."),
        ("lab_service_api", "REST endpoints for deployed Lab Services and manual runs."),
        ("image_lab_api", "REST/WebSocket endpoints for Image Processing LAB sessions."),
        ("generate_llm_context_map", "Generates the full-system LLM context/file inventory."),
    ]

    normalized = stem.replace("-", "_").replace(".", "_").lower()

    for needle, purpose in rules:
        if needle in normalized:
            return purpose

    if relative.suffix.lower() in {".md"}:
        return "Project documentation / LLM context note."

    if "test" in text:
        return "Regression or integration tests."

    if relative.suffix.lower() == ".py":
        return f"Python module `{stem}`."
    if relative.suffix.lower() in {".ts", ".tsx"}:
        return f"TypeScript module/component `{stem}`."
    if relative.suffix.lower() == ".json":
        return "JSON configuration or package metadata."
    if relative.suffix.lower() in {".yaml", ".yml", ".toml", ".ini", ".cfg"}:
        return "Project configuration."
    if relative.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".ico"}:
        return "Static visual asset."

    return "Project file."


def python_symbols(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return []

    result: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            result.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append(f"def {node.name}")

    return result[:10]


def ts_symbols(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []

    patterns = [
        r"export\s+(?:const|function|class|interface|type)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"class\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"interface\s+([A-Za-z_][A-Za-z0-9_]*)",
    ]

    result: list[str] = []

    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)

            if name not in result:
                result.append(name)

            if len(result) >= 10:
                return result

    return result


def symbols_for(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_SYMBOL_BYTES:
            return []
    except OSError:
        return []

    suffix = path.suffix.lower()

    if suffix == ".py":
        return python_symbols(path)

    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return ts_symbols(path)

    return []


def markdown_escape(value: str) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", " ")
    )


def human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    return f"{size / (1024 * 1024):.1f} MB"


def write_map(
    frontend: Path,
    backend: Path,
    output: Path,
) -> None:
    projects = [
        ("FE", frontend),
        ("BE", backend),
    ]

    rows = []
    category_counts = Counter()
    extension_counts = Counter()
    project_counts = Counter()

    for project, root in projects:
        branch, commit = git_info(root)

        for path in collect_files(root):
            relative = path.relative_to(root)
            category = classify(project, relative)
            purpose = infer_purpose(project, relative)
            symbols = symbols_for(path)
            size = path.stat().st_size

            rows.append(
                {
                    "project": project,
                    "root": root,
                    "relative": relative,
                    "category": category,
                    "purpose": purpose,
                    "symbols": symbols,
                    "size": size,
                    "branch": branch,
                    "commit": commit,
                }
            )

            category_counts[category] += 1
            extension_counts[path.suffix.lower() or "<none>"] += 1
            project_counts[project] += 1

    rows.sort(
        key=lambda item: (
            item["project"],
            item["category"],
            str(item["relative"]).lower(),
        )
    )

    now = dt.datetime.now().astimezone()
    fe_branch, fe_commit = git_info(frontend)
    be_branch, be_commit = git_info(backend)

    lines = [
        "# Lambda Vision — Full System File Map",
        "",
        "> Generated automatically. Re-run the generator after structural code changes.",
        "",
        f"- Generated: `{now.isoformat(timespec='seconds')}`",
        f"- Frontend root: `{frontend}`",
        f"- Frontend git: `{fe_branch}` @ `{fe_commit}`",
        f"- Backend root: `{backend}`",
        f"- Backend git: `{be_branch}` @ `{be_commit}`",
        f"- Files indexed: **{len(rows)}** (FE {project_counts['FE']} / BE {project_counts['BE']})",
        "",
        "## How to use this file with an LLM",
        "",
        "1. Give the LLM this file first when opening a new conversation about the codebase.",
        "2. Identify the module/category relevant to the task.",
        "3. Load only the referenced source files plus the latest matching `docs/llm_context/updates/*.md` note.",
        "4. If the codebase changed structurally, regenerate this map before relying on it.",
        "",
        "This inventory intentionally excludes dependency/build/runtime-data directories such as "
        "`node_modules`, `.git`, virtual environments, `dist/build`, caches, runtime `storage`, logs, "
        "datasets, and updater backups.",
        "",
        "## System module summary",
        "",
        "| Module / category | Files |",
        "| --- | ---: |",
    ]

    for category, count in sorted(category_counts.items()):
        lines.append(f"| {markdown_escape(category)} | {count} |")

    lines += [
        "",
        "## Suggested context bundles",
        "",
        "### Image Processing LAB frontend",
        "",
        "- `FE:src/Pages/ImageProcessingLabPage.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts`",
        "- `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx`",
        "- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`",
        "- `FE:src/api/imageLabApi.ts`",
        "",
        "### Image Processing LAB backend",
        "",
        "- `BE:app/services/vision_labs/image/`",
        "- `BE:app/api/v1/endpoints/image_lab_api.py`",
        "- `BE:tests/vision_labs/image/`",
        "",
        "### Lab Service",
        "",
        "- `FE:src/Pages/LabView.tsx`",
        "- `FE:src/api/labServiceApi.ts`",
        "- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`",
        "- `BE:app/services/vision_labs/service/`",
        "- `BE:app/api/v1/endpoints/lab_service_api.py`",
        "- `BE:tests/vision_labs/test_lab_service_core.py`",
        "",
        "## Full file inventory",
        "",
        "| Project | Module | File | Size | Purpose | Key symbols |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]

    for row in rows:
        symbol_text = ", ".join(row["symbols"]) if row["symbols"] else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    row["project"],
                    markdown_escape(row["category"]),
                    f"`{row['project']}:{row['relative'].as_posix()}`",
                    human_size(row["size"]),
                    markdown_escape(row["purpose"]),
                    markdown_escape(symbol_text),
                ]
            )
            + " |"
        )

    lines += [
        "",
        "## File-extension summary",
        "",
        "| Extension | Files |",
        "| --- | ---: |",
    ]

    for extension, count in sorted(extension_counts.items()):
        lines.append(f"| `{extension}` | {count} |")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    frontend = Path(args.frontend).expanduser().resolve()
    backend = Path(args.backend).expanduser().resolve()
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else frontend / "docs/llm_context/SYSTEM_FILE_MAP.md"
    )

    write_map(frontend, backend, output)
    print(f"[OK] Wrote system context map: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

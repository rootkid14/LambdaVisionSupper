#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import datetime as dt
import fnmatch
import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


GENERATOR_VERSION = "2.1"

# ---------------------------------------------------------------------------
# Source selection
# ---------------------------------------------------------------------------

IGNORED_DIR_NAMES = {
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
    "outputs",
    "output",
    "checkpoints",
    "weights",
    "runs",
}

# These are intentionally source/config/documentation oriented.
SOURCE_EXTENSIONS = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".css",
    ".scss",
    ".html",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".bat",
}

# JSON is useful only when it is a meaningful project config/manifest.
MEANINGFUL_JSON_NAMES = {
    "package.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "tauri.conf.json",
}

MEANINGFUL_TEXT_NAMES = {
    "requirements.txt",
    "pytest.ini",
    "Dockerfile",
    "Makefile",
    ".gitignore",
    ".python-version",
}

EXCLUDED_BINARY_DATA_EXTENSIONS = {
    ".npz",
    ".npy",
    ".pt",
    ".pth",
    ".onnx",
    ".engine",
    ".weights",
    ".h5",
    ".hdf5",
    ".pkl",
    ".pickle",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".parquet",
    ".arrow",
    ".csv",
    ".xlsx",
    ".xls",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".gif",
    ".ico",
    ".icns",
    ".svg",
    ".mp4",
    ".avi",
    ".mov",
    ".bin",
    ".dll",
    ".so",
    ".dylib",
    ".exe",
}

GENERATED_CONTEXT_NAMES = {
    "ts_context_for_llm.txt",
    "tsx_context_for_llm.txt",
}

GENERATED_SCHEMA_PATH_PARTS = {
    "src-tauri/gen/schemas",
}

MAX_SYMBOL_BYTES = 320_000
MAX_IMPORT_BYTES = 500_000


# ---------------------------------------------------------------------------
# Project-aware architecture model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModuleProfile:
    key: str
    project: str
    title: str
    description: str
    patterns: tuple[str, ...]
    boundary: str = ""
    context_priority: int = 50


def _profiles() -> tuple[ModuleProfile, ...]:
    return (
        # Frontend
        ModuleProfile(
            "fe_app_shell",
            "FE",
            "Frontend Application Shell & Routing",
            "React/Vite application entry points, global routes, and the main navigation/home surface.",
            (
                "exact:src/main.tsx",
                "exact:src/App.tsx",
                "exact:src/App.css",
                "exact:src/Pages/MainScreen.tsx",
            ),
            "Owns navigation/composition only; domain logic should remain in the feature modules.",
            10,
        ),
        ModuleProfile(
            "fe_image_lab",
            "FE",
            "Image Processing LAB UI",
            "Interactive raster-processing editor: operator library, stack, viewers, Live/Manual execution, filter playground, and Image LAB API client.",
            (
                "exact:src/Pages/ImageProcessingLabPage.tsx",
                "prefix:src/components/VisionLabs/ImageProcessing/",
                "exact:src/api/imageLabApi.ts",
            ),
            "Edits ImagePipelineDefinition and talks to Image LAB sessions. It must not inherit or depend on legacy BaseNode/Sequencer semantics.",
            5,
        ),
        ModuleProfile(
            "fe_sampling_geometry",
            "FE",
            "Sampling / Geometry LAB UI",
            "Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction.",
            (
                "exact:src/Pages/SamplingGeometryLabPage.tsx",
                "prefix:src/components/VisionLabs/SamplingGeometry/",
                "exact:src/api/samplingGeometryApi.ts",
            ),
            "Consumes raster sources directly or through Lab Services and can deploy typed sampling_geometry services.",
            5,
        ),
        ModuleProfile(
            "fe_lab_service",
            "FE",
            "Lab Service Hub UI",
            "Deployed/versioned Lab Service cards, manual runner, edit navigation, and Lab Service API client.",
            (
                "exact:src/Pages/LabView.tsx",
                "exact:src/api/labServiceApi.ts",
            ),
            "Consumes the generic Lab Service contract; currently Image Processing is the first runtime adapter.",
            6,
        ),
        ModuleProfile(
            "fe_sequencer",
            "FE",
            "App Builder / Sequencer UI",
            "Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.",
            (
                "exact:src/Pages/ProgrammingPage.tsx",
                "exact:src/Pages/SequencerPage.tsx",
                "prefix:src/components/ProgramMode/",
                "prefix:src/UI_Engine/SequencerComponents/",
                "exact:src/Stores/FlowStore.tsx",
                "exact:src/utils/FlowCompiler.ts",
                "exact:src/utils/FlowUtils.ts",
                "exact:src/api/nodeApi.ts",
            ),
            "This is the general automation/agentic graph system. Keep its node model separate from Vision LAB ImageOperator.",
            8,
        ),
        ModuleProfile(
            "fe_inspection_engine",
            "FE",
            "Inspection UI Engine",
            "Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.",
            (
                "exact:src/Pages/InspectionPage.tsx",
                "prefix:src/UI_Engine/UIEngineComponents/",
                "prefix:src/UI_Engine/UIEngineStores/",
                "prefix:src/UI_Engine/UIEngineHelper/",
                "prefix:src/UI_Engine/hooks/",
            ),
            "UI-engine state/canvas layer; treat separately from the Vision LAB editor unless an explicit adapter is introduced.",
            15,
        ),
        ModuleProfile(
            "fe_fleet",
            "FE",
            "Fleet / Resource UI",
            "Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.",
            (
                "exact:src/Pages/FleetDashboard.tsx",
                "prefix:src/components/Fleet/",
                "exact:src/Stores/FleetDashboardStores.ts",
                "exact:src/api/fleetApi.ts",
            ),
            context_priority=20,
        ),
        ModuleProfile(
            "fe_database",
            "FE",
            "Database UI",
            "Database page, table/query panels and grids, database store, and database API client.",
            (
                "exact:src/Pages/DatabasePage.tsx",
                "prefix:src/components/DataBaseEngine/",
                "exact:src/Stores/DatabaseEngineStore.ts",
                "exact:src/api/dbEngineApi.ts",
            ),
            context_priority=20,
        ),
        ModuleProfile(
            "fe_project_compiler",
            "FE",
            "Project Compiler",
            "Frontend project/compiler utilities used to transform or package project definitions.",
            ("prefix:src/ProjectCompiler/",),
            context_priority=35,
        ),
        ModuleProfile(
            "fe_shared_ui",
            "FE",
            "Shared Frontend UI & Utilities",
            "Reusable navigation/action UI and generic frontend utilities shared by feature modules.",
            (
                "prefix:src/Commons/",
                "exact:src/utils/ColorConst.ts",
                "exact:src/utils/imageUtils.ts",
            ),
            context_priority=40,
        ),
        ModuleProfile(
            "fe_tauri",
            "FE",
            "Desktop / Tauri Host",
            "Rust/Tauri desktop shell and its hand-authored configuration.",
            (
                "prefix:src-tauri/src/",
                "exact:src-tauri/Cargo.toml",
                "exact:src-tauri/build.rs",
                "exact:src-tauri/tauri.conf.json",
                "prefix:src-tauri/capabilities/",
            ),
            context_priority=50,
        ),
        ModuleProfile(
            "fe_tools_docs",
            "FE",
            "Frontend Tools & LLM Context Docs",
            "Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.",
            (
                "prefix:tools/",
                "glob:update_*.py",
                "prefix:docs/llm_context/",
            ),
            context_priority=70,
        ),

        # Backend
        ModuleProfile(
            "be_app_shell",
            "BE",
            "Backend Application Shell & API Router",
            "FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.",
            (
                "exact:app/main.py",
                "exact:app/core/config.py",
                "exact:app/api/root_api.py",
                "exact:app/api/v1/api.py",
                "exact:app/api/v1/endpoints/utils.py",
            ),
            "Composes feature routers; feature execution belongs to domain services.",
            10,
        ),
        ModuleProfile(
            "be_sequencer",
            "BE",
            "Legacy App Builder / Sequencer Runtime",
            "General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes.",
            (
                "exact:app/api/v1/endpoints/graph_api.py",
                "exact:app/schemas/graph.py",
                "exact:app/services/node_registry.py",
                "exact:app/services/LogicObjects.py",
                "exact:app/services/LogicPoolManager.py",
                "exact:app/services/LVSTypes.py",
                "prefix:app/services/Nodes/",
            ),
            "Do not make Vision LAB ImageOperator inherit BaseNode. Integration should occur through explicit adapters/services.",
            8,
        ),
        ModuleProfile(
            "be_vision_core",
            "BE",
            "Vision LAB Core Contracts",
            "LAB-level shared port/parameter specifications and common Vision LAB package contracts.",
            (
                "exact:app/services/vision_labs/__init__.py",
                "prefix:app/services/vision_labs/core/",
            ),
            "Common LAB vocabulary only; specialized LABs keep specialized domain models.",
            5,
        ),
        ModuleProfile(
            "be_image_lab",
            "BE",
            "Image Processing LAB Backend",
            "ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.",
            (
                "exact:app/api/v1/endpoints/image_lab_api.py",
                "prefix:app/services/vision_labs/image/",
            ),
            "Pure raster processing. Registration/comparison/inspection semantics belong in other LABs.",
            4,
        ),
        ModuleProfile(
            "be_sampling_geometry",
            "BE",
            "Sampling / Geometry LAB Backend",
            "Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API.",
            (
                "exact:app/api/v1/endpoints/sampling_geometry_api.py",
                "prefix:app/services/vision_labs/sampling_geometry/",
            ),
            "Feature-extraction backbone. It does not decide OK/NG and does not own model representation/training semantics.",
            4,
        ),
        ModuleProfile(
            "be_lab_service",
            "BE",
            "Lab Service Backend",
            "Versioned deployable LAB snapshots, repository, generic runtime facade, run store, pruning, and Lab Service REST API.",
            (
                "exact:app/api/v1/endpoints/lab_service_api.py",
                "prefix:app/services/vision_labs/service/",
            ),
            "LabServiceRuntime is the future callable boundary for Dataset/Sampling/Sequencer/Agentic integrations; callers should not duplicate LAB execution logic.",
            5,
        ),
        ModuleProfile(
            "be_fleet",
            "BE",
            "Fleet / Device / Infrastructure Backend",
            "Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.",
            (
                "exact:app/api/v1/endpoints/infra_api.py",
                "exact:app/services/ConnectionBus.py",
                "exact:app/services/DevicePoolManager.py",
                "exact:app/external_libs/camera_core.py",
                "prefix:app/external_libs/MvImport/",
            ),
            context_priority=20,
        ),
        ModuleProfile(
            "be_database",
            "BE",
            "Database Backend",
            "Database CRUD/query API and database manager.",
            (
                "exact:app/api/v1/endpoints/db_api.py",
                "exact:app/services/DatabaseManager.py",
            ),
            context_priority=20,
        ),
        ModuleProfile(
            "be_shared_utils",
            "BE",
            "Shared Backend Utilities",
            "Generic file/image/network helpers shared by backend domains.",
            ("prefix:app/services/utils/",),
            context_priority=40,
        ),
        ModuleProfile(
            "be_research",
            "BE",
            "Research / Experiments / Training",
            "Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.",
            (
                "glob:e1108*.py",
                "glob:e5204*.py",
                "glob:engineer_*.py",
                "glob:entropy_*.py",
                "exact:get_26D_vectors.py",
                "exact:run_compare_mlp_cnn.py",
                "glob:kiemtra*.py",
                "exact:modultest.py",
                "exact:concate_image.py",
                "exact:chuongtrinhchupanh.py",
                "exact:clean_req.py",
            ),
            "Treat as research tooling unless a production module imports it explicitly.",
            80,
        ),
        ModuleProfile(
            "be_tests",
            "BE",
            "Backend Tests",
            "Regression and integration tests.",
            ("prefix:tests/",),
            context_priority=60,
        ),
        ModuleProfile(
            "be_tools",
            "BE",
            "Backend Tools / Updaters",
            "Backend-side updater and maintenance scripts.",
            ("glob:update_*.py",),
            context_priority=70,
        ),
    )


MODULE_PROFILES = _profiles()
PROFILE_BY_KEY = {profile.key: profile for profile in MODULE_PROFILES}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return ""


def git_metadata(root: Path) -> dict[str, object]:
    branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() or "unknown"
    commit = run_git(root, "rev-parse", "--short", "HEAD").strip() or "unknown"
    status = [
        line.rstrip()
        for line in run_git(root, "status", "--short").splitlines()
        if line.strip()
    ]
    return {
        "branch": branch,
        "commit": commit,
        "dirty": bool(status),
        "status": status[:100],
    }


def git_candidate_paths(root: Path) -> list[Path] | None:
    raw = run_git(
        root,
        "ls-files",
        "-co",
        "--exclude-standard",
        "-z",
    )
    if not raw:
        return None

    result = []
    for entry in raw.split("\x00"):
        if not entry:
            continue
        path = root / entry
        if path.is_file():
            result.append(path)
    return sorted(set(result), key=lambda item: item.as_posix().lower())


def walk_candidate_paths(root: Path) -> list[Path]:
    files: list[Path] = []

    for current, dirs, names in os.walk(root):
        current_path = Path(current)

        dirs[:] = [
            name
            for name in dirs
            if name not in IGNORED_DIR_NAMES
        ]

        for name in names:
            path = current_path / name
            if path.is_file():
                files.append(path)

    return sorted(files, key=lambda item: item.as_posix().lower())


def all_candidate_paths(root: Path) -> list[Path]:
    return git_candidate_paths(root) or walk_candidate_paths(root)


def ignored_by_directory(relative: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES for part in relative.parts)


def generated_or_redundant(relative: Path) -> bool:
    posix = relative.as_posix()

    if relative.name in GENERATED_CONTEXT_NAMES:
        return True

    if any(part in posix for part in GENERATED_SCHEMA_PATH_PARTS):
        return True

    if relative.name.endswith(".lock"):
        return True

    if relative.name in {"package-lock.json", "Cargo.lock"}:
        return True

    return False


def source_relevance(path: Path, root: Path) -> tuple[bool, str]:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False, "outside-root"

    if ignored_by_directory(relative):
        return False, "ignored-directory"

    if generated_or_redundant(relative):
        return False, "generated/redundant"

    suffix = path.suffix.lower()

    if suffix in EXCLUDED_BINARY_DATA_EXTENSIONS:
        return False, f"binary/data:{suffix or '<none>'}"

    if relative.name in MEANINGFUL_TEXT_NAMES:
        return True, "meaningful-config"

    if suffix == ".json":
        if relative.name in MEANINGFUL_JSON_NAMES:
            return True, "meaningful-config"
        if "capabilities" in relative.parts:
            return True, "meaningful-config"
        return False, "generated/aux-json"

    if suffix in SOURCE_EXTENSIONS:
        return True, "source"

    return False, f"non-source:{suffix or '<none>'}"


def pattern_match(relative: Path, pattern: str) -> bool:
    posix = relative.as_posix()

    if pattern.startswith("exact:"):
        return posix == pattern[6:]

    if pattern.startswith("prefix:"):
        return posix.startswith(pattern[7:])

    if pattern.startswith("glob:"):
        return fnmatch.fnmatch(posix, pattern[5:])

    return False


def module_for(project: str, relative: Path) -> ModuleProfile | None:
    for profile in MODULE_PROFILES:
        if profile.project != project:
            continue
        if any(pattern_match(relative, pattern) for pattern in profile.patterns):
            return profile
    return None


def fallback_module(project: str, relative: Path) -> str:
    posix = relative.as_posix()

    if project == "FE":
        if posix.startswith("src/"):
            return "Frontend — Unclassified Source"
        if posix.startswith("src-tauri/"):
            return "Desktop / Tauri — Unclassified"
        return "Frontend — Project / Config"

    if posix.startswith("app/"):
        return "Backend — Unclassified App Source"
    return "Backend — Unclassified Project Source"


def module_title(project: str, relative: Path) -> tuple[str, str | None]:
    profile = module_for(project, relative)
    if profile:
        return profile.title, profile.key
    return fallback_module(project, relative), None


def human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def md_escape(value: str) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", " ")
    )


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Code intelligence
# ---------------------------------------------------------------------------

def python_symbols(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    result = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            result.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append(f"def {node.name}")

    return result[:12]


def ts_symbols(source: str) -> list[str]:
    patterns = (
        r"export\s+(?:default\s+)?(?:const|function|class|interface|type|enum)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"export\s*\{\s*([A-Za-z_][A-Za-z0-9_]*)",
    )

    result = []
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            if name not in result:
                result.append(name)
            if len(result) >= 12:
                return result

    return result


def symbols_for(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_SYMBOL_BYTES:
            return []
    except OSError:
        return []

    source = read_text_safe(path)
    suffix = path.suffix.lower()

    if suffix in {".py", ".pyi"}:
        return python_symbols(source)

    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return ts_symbols(source)

    return []


def python_imports(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return sorted(set(imports))


def ts_imports(source: str) -> list[str]:
    matches = re.findall(
        r"""(?:import|export)\s+(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]""",
        source,
    )
    return sorted(set(matches))


def imports_for(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_IMPORT_BYTES:
            return []
    except OSError:
        return []

    source = read_text_safe(path)
    suffix = path.suffix.lower()

    if suffix in {".py", ".pyi"}:
        return python_imports(source)

    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return ts_imports(source)

    return []


def python_api_routes(source: str) -> list[tuple[str, str, str]]:
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    methods = {"get", "post", "put", "delete", "patch", "websocket"}
    result = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr not in methods:
                continue

            if not decorator.args:
                continue

            arg = decorator.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                result.append((func.attr.upper(), arg.value, node.name))

    return result


def frontend_routes(source: str) -> list[str]:
    result = re.findall(
        r"""<Route\b[^>]*\bpath\s*=\s*["']([^"']+)["']""",
        source,
    )
    return sorted(set(result))


def infer_purpose(project: str, relative: Path, profile: ModuleProfile | None) -> str:
    name = relative.name
    stem = relative.stem
    normalized = stem.replace("-", "_").replace(".", "_").lower()

    exact = {
        "app": "Frontend route composition / application shell." if project == "FE" else "Application module.",
        "main": "Frontend bootstrap entry point." if project == "FE" else "FastAPI backend bootstrap/entry point.",
        "operatorlibrary": "Image LAB operator selector and per-filter guide launcher.",
        "filterguidemodal": "Standalone filter documentation and isolated test playground.",
        "operatorguide": "Filter explanations, tuning guidance, and parameter help.",
        "imageprocessinglabpage": "Top-level Image Processing LAB page/layout.",
        "imageworkbench": "Image LAB upload/run/viewer workbench.",
        "processingstack": "Image LAB stack editor, ordering, parameters, and exposed service outputs.",
        "zoompanimageview": "Reusable zoom/pan/fullscreen raster viewer.",
        "useimagelabcontroller": "Image LAB frontend controller for sessions, Live/Manual execution, viewers, and service editing.",
        "imagelabapi": "Frontend Image LAB REST/WebSocket API client.",
        "labserviceapi": "Frontend Lab Service API client.",
        "labview": "Vision LAB launcher and deployed Lab Service hub/manual runner.",
        "node_registry": "Legacy BaseNode/NODE_REGISTRY contract and node registration.",
        "logicobjects": "Legacy compiled graph execution object.",
        "logicpoolmanager": "Legacy deployed graph/LogicObject pool and execution lifecycle.",
        "lvstypes": "Legacy sequencer/node UI/runtime type definitions.",
        "graph_api": "Legacy App Builder/Sequencer graph deployment and execution API.",
        "pipeline": "Image LAB pipeline schema, validation, compilation, and graph contracts.",
        "registry": "Image LAB operator registry/catalog and stable operator IDs.",
        "session": "Interactive Image LAB session, preview, realtime and session management.",
        "runtime": (
            "Lab Service runtime/pruning/run store."
            if "vision_labs/service" in relative.as_posix()
            else "Image LAB artifact cache and pipeline runtime."
        ),
        "models": "Lab Service typed deploy/run contracts.",
        "repository": (
            "Versioned Lab Service persistence."
            if "vision_labs/service" in relative.as_posix()
            else "Saved Image LAB pipeline persistence."
        ),
        "image_lab_api": "Image LAB session/pipeline/operator REST and WebSocket API.",
        "lab_service_api": "Versioned Lab Service deploy/run/preview REST API.",
        "databasemanager": "Database access and dynamic table management.",
        "devicepoolmanager": "Backend device/resource pool lifecycle.",
        "connectionbus": "Backend resource/device connection bus.",
        "generate_llm_context_map": "Project-aware LLM context compiler.",
    }

    if normalized in exact:
        return exact[normalized]

    if profile:
        return profile.description

    suffix = relative.suffix.lower()
    if suffix in {".py", ".pyi"}:
        return f"Python source module `{stem}`."
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return f"TypeScript/JavaScript source `{stem}`."
    if suffix == ".rs":
        return f"Rust source module `{stem}`."
    if suffix == ".md":
        return "Project documentation."
    return "Project source/configuration file."


# ---------------------------------------------------------------------------
# Dependency resolution
# ---------------------------------------------------------------------------

def python_module_to_candidates(import_name: str) -> list[str]:
    parts = import_name.split(".")
    base = "/".join(parts)
    return [base + ".py", base + "/__init__.py"]


def resolve_python_import(import_name: str, known_paths: set[str]) -> str | None:
    for candidate in python_module_to_candidates(import_name):
        if candidate in known_paths:
            return candidate

    # For "from app.foo.bar import X", the module may be a package parent.
    parts = import_name.split(".")
    while len(parts) > 1:
        parts.pop()
        base = "/".join(parts)
        for candidate in (base + ".py", base + "/__init__.py"):
            if candidate in known_paths:
                return candidate

    return None


def resolve_ts_import(
    source_rel: Path,
    import_name: str,
    known_paths: set[str],
) -> str | None:
    if not import_name.startswith("."):
        return None

    base = (source_rel.parent / import_name)
    raw = PurePosixPath(base.as_posix()).as_posix()

    candidates = [
        raw,
        raw + ".ts",
        raw + ".tsx",
        raw + ".js",
        raw + ".jsx",
        raw + "/index.ts",
        raw + "/index.tsx",
        raw + "/index.js",
        raw + "/index.jsx",
    ]

    # Normalize path components without requiring existence on this machine.
    normalized_candidates = []
    for candidate in candidates:
        parts = []
        for part in PurePosixPath(candidate).parts:
            if part == ".":
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        normalized_candidates.append("/".join(parts))

    for candidate in normalized_candidates:
        if candidate in known_paths:
            return candidate

    return None


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@dataclass
class FileRecord:
    project: str
    root: Path
    path: Path
    relative: Path
    module: str
    module_key: str | None
    purpose: str
    size: int
    symbols: list[str]
    imports: list[str]


def build_inventory(project: str, root: Path):
    included: list[FileRecord] = []
    excluded = Counter()
    excluded_extensions = Counter()

    for path in all_candidate_paths(root):
        relative = path.relative_to(root)
        relevant, reason = source_relevance(path, root)

        if not relevant:
            excluded[reason] += 1
            excluded_extensions[path.suffix.lower() or "<none>"] += 1
            continue

        profile = module_for(project, relative)
        module = profile.title if profile else fallback_module(project, relative)

        included.append(
            FileRecord(
                project=project,
                root=root,
                path=path,
                relative=relative,
                module=module,
                module_key=profile.key if profile else None,
                purpose=infer_purpose(project, relative, profile),
                size=path.stat().st_size,
                symbols=symbols_for(path),
                imports=imports_for(path),
            )
        )

    included.sort(
        key=lambda record: (
            record.module,
            record.relative.as_posix().lower(),
        )
    )
    return included, excluded, excluded_extensions


# ---------------------------------------------------------------------------
# Context bundles
# ---------------------------------------------------------------------------

BUNDLE_DEFINITIONS = {
    "Image Processing LAB": {
        "purpose": "Raster-processing editor, operator framework, sessions/runtime, filter playground, and Image LAB API.",
        "minimal": (
            ("FE", "src/Pages/ImageProcessingLabPage.tsx"),
            ("FE", "src/components/VisionLabs/ImageProcessing/useImageLabController.ts"),
            ("FE", "src/components/VisionLabs/ImageProcessing/types.ts"),
            ("FE", "src/api/imageLabApi.ts"),
            ("BE", "app/services/vision_labs/image/operator.py"),
            ("BE", "app/services/vision_labs/image/pipeline.py"),
            ("BE", "app/services/vision_labs/image/runtime.py"),
            ("BE", "app/services/vision_labs/image/session.py"),
            ("BE", "app/services/vision_labs/image/types.py"),
            ("BE", "app/api/v1/endpoints/image_lab_api.py"),
        ),
        "deep": (
            ("FE", "src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx"),
            ("FE", "src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx"),
            ("FE", "src/components/VisionLabs/ImageProcessing/operatorGuide.ts"),
            ("FE", "src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx"),
            ("FE", "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"),
            ("FE", "src/components/VisionLabs/ImageProcessing/pipelineUtils.ts"),
            ("BE", "app/services/vision_labs/image/registry.py"),
            ("BE", "app/services/vision_labs/image/operators/builtins.py"),
            ("BE", "app/services/vision_labs/image/operators/basic_families.py"),
            ("BE", "app/services/vision_labs/image/operators/advanced_families.py"),
            ("BE", "tests/vision_labs/image/test_image_lab_core.py"),
        ),
    },
    "Sampling / Geometry LAB": {
        "purpose": "Geometry extraction, spatial signal sampling, Fourier/statistical descriptors, and reusable feature-extraction services.",
        "minimal": (
            ("FE", "src/Pages/SamplingGeometryLabPage.tsx"),
            ("FE", "src/components/VisionLabs/SamplingGeometry/useSamplingGeometryController.ts"),
            ("FE", "src/components/VisionLabs/SamplingGeometry/types.ts"),
            ("FE", "src/api/samplingGeometryApi.ts"),
            ("BE", "app/services/vision_labs/sampling_geometry/operator.py"),
            ("BE", "app/services/vision_labs/sampling_geometry/pipeline.py"),
            ("BE", "app/services/vision_labs/sampling_geometry/runtime.py"),
            ("BE", "app/services/vision_labs/sampling_geometry/session.py"),
            ("BE", "app/api/v1/endpoints/sampling_geometry_api.py"),
        ),
        "deep": (
            ("FE", "src/components/VisionLabs/SamplingGeometry/"),
            ("BE", "app/services/vision_labs/sampling_geometry/operators/"),
            ("BE", "app/services/vision_labs/sampling_geometry/preview.py"),
            ("BE", "app/services/vision_labs/sampling_geometry/serialization.py"),
            ("BE", "tests/vision_labs/sampling_geometry/"),
            ("BE", "app/services/vision_labs/service/runtime.py"),
        ),
    },
    "Lab Service": {
        "purpose": "Versioned deployable LAB snapshots and the callable/manual-run service boundary.",
        "minimal": (
            ("FE", "src/Pages/LabView.tsx"),
            ("FE", "src/api/labServiceApi.ts"),
            ("FE", "src/components/VisionLabs/ImageProcessing/useImageLabController.ts"),
            ("BE", "app/services/vision_labs/service/models.py"),
            ("BE", "app/services/vision_labs/service/repository.py"),
            ("BE", "app/services/vision_labs/service/runtime.py"),
            ("BE", "app/api/v1/endpoints/lab_service_api.py"),
        ),
        "deep": (
            ("BE", "tests/vision_labs/test_lab_service_core.py"),
            ("BE", "app/services/vision_labs/image/pipeline.py"),
            ("BE", "app/services/vision_labs/image/runtime.py"),
        ),
    },
    "App Builder / Sequencer": {
        "purpose": "General automation graph editor/runtime based on BaseNode, LogicObject and LogicPoolManager.",
        "minimal": (
            ("FE", "src/Pages/ProgrammingPage.tsx"),
            ("FE", "src/Pages/SequencerPage.tsx"),
            ("FE", "src/Stores/FlowStore.tsx"),
            ("FE", "src/utils/FlowCompiler.ts"),
            ("FE", "src/api/nodeApi.ts"),
            ("BE", "app/services/node_registry.py"),
            ("BE", "app/services/LogicObjects.py"),
            ("BE", "app/services/LogicPoolManager.py"),
            ("BE", "app/services/LVSTypes.py"),
            ("BE", "app/api/v1/endpoints/graph_api.py"),
        ),
        "deep": (
            ("FE", "src/components/ProgramMode/"),
            ("FE", "src/UI_Engine/SequencerComponents/"),
            ("BE", "app/services/Nodes/"),
            ("BE", "app/schemas/graph.py"),
        ),
    },
    "Inspection UI Engine": {
        "purpose": "Inspection canvas/UI-engine state, tags, panels, keyboard triggers and Konva nodes.",
        "minimal": (
            ("FE", "src/Pages/InspectionPage.tsx"),
            ("FE", "src/UI_Engine/UIEngineStores/InspectionStore.ts"),
            ("FE", "src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx"),
            ("FE", "src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx"),
            ("FE", "src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx"),
        ),
        "deep": (
            ("FE", "src/UI_Engine/UIEngineComponents/"),
            ("FE", "src/UI_Engine/UIEngineStores/"),
            ("FE", "src/UI_Engine/UIEngineHelper/"),
        ),
    },
    "Fleet / Device": {
        "purpose": "Resource/device discovery, pools, connections and camera/device infrastructure.",
        "minimal": (
            ("FE", "src/Pages/FleetDashboard.tsx"),
            ("FE", "src/api/fleetApi.ts"),
            ("BE", "app/api/v1/endpoints/infra_api.py"),
            ("BE", "app/services/ConnectionBus.py"),
            ("BE", "app/services/DevicePoolManager.py"),
        ),
        "deep": (
            ("FE", "src/components/Fleet/"),
            ("FE", "src/Stores/FleetDashboardStores.ts"),
            ("BE", "app/external_libs/camera_core.py"),
        ),
    },
    "Database": {
        "purpose": "Database UI, dynamic table/query API, and database manager.",
        "minimal": (
            ("FE", "src/Pages/DatabasePage.tsx"),
            ("FE", "src/api/dbEngineApi.ts"),
            ("FE", "src/Stores/DatabaseEngineStore.ts"),
            ("BE", "app/api/v1/endpoints/db_api.py"),
            ("BE", "app/services/DatabaseManager.py"),
        ),
        "deep": (
            ("FE", "src/components/DataBaseEngine/"),
        ),
    },
}


def expand_bundle_item(
    project: str,
    requested: str,
    records_by_project: dict[str, list[FileRecord]],
) -> list[str]:
    result = []
    for record in records_by_project.get(project, []):
        path = record.relative.as_posix()
        if requested.endswith("/"):
            if path.startswith(requested):
                result.append(path)
        elif path == requested:
            result.append(path)
    return result


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------

def render_index(
    frontend: Path,
    backend: Path,
    records: list[FileRecord],
    git_meta: dict[str, dict[str, object]],
    output_dir: Path,
) -> str:
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    module_counts = Counter(record.module for record in records)
    fe_count = sum(1 for record in records if record.project == "FE")
    be_count = sum(1 for record in records if record.project == "BE")

    lines = [
        "# Lambda Vision — LLM Context Index",
        "",
        "> Start here when opening a new LLM conversation about this codebase.",
        "",
        f"- Generator: `v{GENERATOR_VERSION}`",
        f"- Generated: `{now}`",
        f"- Source files indexed: **{len(records)}** (FE {fe_count} / BE {be_count})",
        f"- Frontend git: `{git_meta['FE']['branch']}` @ `{git_meta['FE']['commit']}`"
        + (" · **DIRTY**" if git_meta["FE"]["dirty"] else " · clean"),
        f"- Backend git: `{git_meta['BE']['branch']}` @ `{git_meta['BE']['commit']}`"
        + (" · **DIRTY**" if git_meta["BE"]["dirty"] else " · clean"),
        "",
        "## Recommended handoff order",
        "",
        "For a **new chat**, normally provide:",
        "",
        "1. `SYSTEM_CONTEXT_INDEX.md` — this compact index.",
        "2. `SYSTEM_ARCHITECTURE.md` — system boundaries and execution flows.",
        "3. The latest relevant `updates/*.md` note.",
        "4. Only then load the exact source bundle from `SYSTEM_CONTEXT_BUNDLES.md`.",
        "5. Use `SYSTEM_FILE_MAP.md` when the task needs broader source navigation.",
        "",
        "Do **not** start by dumping the whole codebase into context.",
        "",
        "## Critical architecture boundary",
        "",
        "- **Legacy App Builder / Sequencer**: `BaseNode` / `NODE_REGISTRY` → `LogicObject` → `LogicPoolManager`.",
        "- **Vision LAB**: specialized LAB contracts; Image Processing uses `ImageOperator` / operator registry → `ImagePipelineRuntime` / `ImageLabSession`.",
        "- **Lab Service**: versioned callable wrapper around LAB execution; intended future integration boundary for Dataset, Sampling/Geometry, Sequencer and Agentic callers.",
        "- Do not merge the Legacy `BaseNode` hierarchy into the Image LAB operator hierarchy unless an explicit adapter is designed.",
        "",
        "## Detected modules",
        "",
        "| Module | Files |",
        "| --- | ---: |",
    ]

    for module, count in sorted(module_counts.items()):
        lines.append(f"| {md_escape(module)} | {count} |")

    dirty_lines = []
    for project in ("FE", "BE"):
        status = git_meta[project]["status"]
        if status:
            dirty_lines.append(f"### {project} dirty files")
            dirty_lines.append("")
            dirty_lines.extend(f"- `{line}`" for line in status)
            dirty_lines.append("")

    if dirty_lines:
        lines += ["", "## Current working-tree changes", ""] + dirty_lines

    lines += [
        "## Generated context documents",
        "",
        "- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.",
        "- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.",
        "- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.",
        "- `updates/*.md` — change-specific architectural notes.",
        "",
    ]

    return "\n".join(lines)


def render_architecture(
    records: list[FileRecord],
    module_edges: Counter[tuple[str, str]],
    api_routes: list[tuple[str, str, str, str]],
    ui_routes: list[tuple[str, str]],
) -> str:
    records_by_module = defaultdict(list)
    for record in records:
        records_by_module[record.module].append(record)

    detected_profiles = []
    for profile in sorted(MODULE_PROFILES, key=lambda p: (p.context_priority, p.title)):
        files = records_by_module.get(profile.title, [])
        if files:
            detected_profiles.append((profile, files))

    lines = [
        "# Lambda Vision — System Architecture",
        "",
        "> Project-aware architecture snapshot generated from the current source tree.",
        "",
        "## 1. High-level architecture",
        "",
        "Lambda Vision currently contains two important execution families plus supporting domains:",
        "",
        "```text",
        "Frontend / Desktop",
        "│",
        "├─ App Builder / Sequencer UI ───────────────┐",
        "│                                             ▼",
        "│                                  Legacy Graph Runtime",
        "│                                  BaseNode / NODE_REGISTRY",
        "│                                  LogicObject / LogicPoolManager",
        "│",
        "├─ Vision LAB Hub",
        "│    ├─ Image Processing LAB ────────────────┐",
        "│    │                                       ▼",
        "│    │                              Image LAB Session/Runtime",
        "│    │                              ImageOperator Registry",
        "│    │",
        "│    ├─ Sampling / Geometry LAB ─────────────┐",
        "│    │                                       ▼",
        "│    │                              SamplingGeometryRuntime",
        "│    │                              Geometry / Spatial / Spectral",
        "│    │",
        "│    └─ Lab Services ────────────────────────┐",
        "│                                            ▼",
        "│                                   LabServiceRuntime",
        "│                                   versioned LAB snapshots",
        "│",
        "├─ Fleet / Resource UI ───────────── Device/Infrastructure Backend",
        "└─ Database UI ───────────────────── Database Backend",
        "```",
        "",
        "## 2. Architectural invariants",
        "",
        "1. **General automation and Vision LAB are deliberately separate abstractions.**",
        "   Legacy automation uses `BaseNode`; Image Processing uses `ImageOperator`.",
        "2. **Image Processing LAB is raster-centric.** Operators should not know master/query, inspection spec, station OK/NG, or alignment semantics.",
        "3. **Lab Service is the reusable callable boundary.** A service is a versioned LAB pipeline snapshot with typed inputs and named outputs.",
        "4. **Interactive LAB sessions and deployed services are different lifecycles.** Interactive sessions optimize editing/tuning; deployed services optimize stable invocation.",
        "5. **Future cross-LAB composition should use explicit typed contracts/adapters**, not implicit imports between specialized internals.",
        "",
        "## 3. Execution flows",
        "",
        "### Image Processing LAB",
        "",
        "```text",
        "ImageProcessingLabPage",
        "  → useImageLabController",
        "  → imageLabApi",
        "  → /api/v1/image-lab",
        "  → ImageLabSessionManager / ImageLabSession",
        "  → ImagePipelineRuntime",
        "  → ImageOperatorRegistry",
        "  → raster operators",
        "```",
        "",
        "### Sampling / Geometry LAB",
        "",
        "```text",
        "SamplingGeometryLabPage",
        "  → useSamplingGeometryController",
        "  → samplingGeometryApi",
        "  → /api/v1/sampling-geometry",
        "  → SamplingGeometrySession",
        "  → SamplingGeometryRuntime",
        "  → workspace operator registry",
        "  → geometry / profiles / features / spectra",
        "```",
        "",
        "### Lab Service",
        "",
        "```text",
        "LabView / Image LAB deploy UI",
        "  → labServiceApi",
        "  → /api/v1/lab-services",
        "  → LabServiceRepository (versions/snapshots)",
        "  → LabServiceRuntime",
        "  → current LAB adapter (Image Processing today)",
        "  → named service outputs",
        "```",
        "",
        "### Legacy App Builder / Sequencer",
        "",
        "```text",
        "Programming/Sequencer UI",
        "  → nodeApi / graph API",
        "  → NODE_REGISTRY / BaseNode",
        "  → LogicObject graph",
        "  → LogicPoolManager",
        "  → registered Nodes / devices / actions",
        "```",
        "",
        "## 4. Detected modules",
        "",
    ]

    for profile, files in detected_profiles:
        lines += [
            f"### {profile.title}",
            "",
            profile.description,
            "",
            f"- Detected files: **{len(files)}**",
        ]
        if profile.boundary:
            lines.append(f"- Boundary: {profile.boundary}")

        important = sorted(
            files,
            key=lambda r: (
                0 if r.relative.name in {
                    "App.tsx",
                    "main.py",
                    "runtime.py",
                    "pipeline.py",
                    "repository.py",
                    "node_registry.py",
                    "LogicObjects.py",
                    "LogicPoolManager.py",
                    "LabView.tsx",
                    "ImageProcessingLabPage.tsx",
                } else 1,
                r.relative.as_posix(),
            ),
        )[:8]

        if important:
            lines.append("- Key files:")
            lines.extend(
                f"  - `{record.project}:{record.relative.as_posix()}` — {record.purpose}"
                for record in important
            )
        lines.append("")

    if module_edges:
        lines += [
            "## 5. Internal module dependency edges",
            "",
            "Derived from Python/TypeScript imports. Counts are import edges between source files.",
            "",
            "| Source module | Depends on | Edges |",
            "| --- | --- | ---: |",
        ]
        for (source, target), count in module_edges.most_common(60):
            if source != target:
                lines.append(
                    f"| {md_escape(source)} | {md_escape(target)} | {count} |"
                )
        lines.append("")

    if api_routes:
        lines += [
            "## 6. Backend API routes",
            "",
            "| File | Method | Path | Handler |",
            "| --- | --- | --- | --- |",
        ]
        for file_path, method, route, handler in sorted(api_routes):
            lines.append(
                f"| `{file_path}` | `{method}` | `{route}` | `{handler}` |"
            )
        lines.append("")

    if ui_routes:
        lines += [
            "## 7. Frontend routes",
            "",
            "| File | Route |",
            "| --- | --- |",
        ]
        for file_path, route in sorted(ui_routes):
            lines.append(f"| `{file_path}` | `{route}` |")
        lines.append("")

    return "\n".join(lines)


def render_bundles(
    records_by_project: dict[str, list[FileRecord]],
) -> str:
    all_known = {
        project: {record.relative.as_posix() for record in records}
        for project, records in records_by_project.items()
    }

    lines = [
        "# Lambda Vision — LLM Context Bundles",
        "",
        "> Use these bundles to load only the source needed for a task.",
        "",
        "## Usage",
        "",
        "- **Minimal**: start here for design/review/small changes.",
        "- **Deep**: add these when implementing or debugging across boundaries.",
        "- Always add the latest relevant `docs/llm_context/updates/*.md` note.",
        "",
    ]

    for name, bundle in BUNDLE_DEFINITIONS.items():
        lines += [
            f"## {name}",
            "",
            bundle["purpose"],
            "",
            "### Minimal context",
            "",
        ]

        minimal_paths = []
        for project, requested in bundle["minimal"]:
            expanded = expand_bundle_item(project, requested, records_by_project)
            minimal_paths.extend((project, path) for path in expanded)

        if minimal_paths:
            lines.extend(f"- `{project}:{path}`" for project, path in minimal_paths)
        else:
            lines.append("- _No matching files detected._")

        lines += ["", "### Deep context", ""]

        deep_paths = []
        for project, requested in bundle["deep"]:
            expanded = expand_bundle_item(project, requested, records_by_project)
            deep_paths.extend((project, path) for path in expanded)

        if deep_paths:
            lines.extend(f"- `{project}:{path}`" for project, path in deep_paths)
        else:
            lines.append("- _No additional matching files detected._")

        lines.append("")

    return "\n".join(lines)


def render_file_map(
    frontend: Path,
    backend: Path,
    records: list[FileRecord],
    excluded: dict[str, Counter],
    excluded_extensions: dict[str, Counter],
    git_meta: dict[str, dict[str, object]],
) -> str:
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    module_counts = Counter(record.module for record in records)

    lines = [
        "# Lambda Vision — Source File Map",
        "",
        "> Clean source/config inventory for LLM-assisted development. Runtime data and binary artifacts are excluded by default.",
        "",
        f"- Generator: `v{GENERATOR_VERSION}`",
        f"- Generated: `{now}`",
        f"- Frontend root: `{frontend}`",
        f"- Frontend git: `{git_meta['FE']['branch']}` @ `{git_meta['FE']['commit']}`",
        f"- Backend root: `{backend}`",
        f"- Backend git: `{git_meta['BE']['branch']}` @ `{git_meta['BE']['commit']}`",
        f"- Included source/config files: **{len(records)}**",
        "",
        "## Module summary",
        "",
        "| Module | Files |",
        "| --- | ---: |",
    ]

    for module, count in sorted(module_counts.items()):
        lines.append(f"| {md_escape(module)} | {count} |")

    lines += [
        "",
        "## Exclusion summary",
        "",
        "The generator intentionally excludes binary datasets, model weights, images/assets, dependency/build output, runtime storage, caches, lockfiles, generated context dumps and generated schemas.",
        "",
        "| Project | Excluded reason | Count |",
        "| --- | --- | ---: |",
    ]

    for project in ("FE", "BE"):
        for reason, count in excluded[project].most_common():
            lines.append(
                f"| {project} | `{md_escape(reason)}` | {count} |"
            )

    lines += [
        "",
        "### Top excluded extensions",
        "",
        "| Project | Extension | Count |",
        "| --- | --- | ---: |",
    ]

    for project in ("FE", "BE"):
        for extension, count in excluded_extensions[project].most_common(20):
            lines.append(f"| {project} | `{extension}` | {count} |")

    lines += [
        "",
        "## Full source inventory",
        "",
        "| Project | Module | File | Size | Purpose | Key symbols |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]

    for record in sorted(
        records,
        key=lambda r: (
            r.project,
            r.module,
            r.relative.as_posix().lower(),
        ),
    ):
        symbols = ", ".join(record.symbols)
        lines.append(
            "| "
            + " | ".join(
                [
                    record.project,
                    md_escape(record.module),
                    f"`{record.project}:{record.relative.as_posix()}`",
                    human_size(record.size),
                    md_escape(record.purpose),
                    md_escape(symbols),
                ]
            )
            + " |"
        )

    unclassified = [
        record
        for record in records
        if record.module_key is None
    ]

    lines += [
        "",
        "## Generator coverage diagnostics",
        "",
        f"- Unclassified source/config files: **{len(unclassified)}**",
    ]

    if unclassified:
        lines.append("- These files should be reviewed when improving the generator:")
        lines.extend(
            f"  - `{record.project}:{record.relative.as_posix()}`"
            for record in unclassified[:100]
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main compilation
# ---------------------------------------------------------------------------

def compile_context(
    frontend: Path,
    backend: Path,
    output_dir: Path,
) -> None:
    fe_records, fe_excluded, fe_excluded_ext = build_inventory("FE", frontend)
    be_records, be_excluded, be_excluded_ext = build_inventory("BE", backend)

    records = fe_records + be_records
    records_by_project = {
        "FE": fe_records,
        "BE": be_records,
    }

    known_paths = {
        "FE": {record.relative.as_posix() for record in fe_records},
        "BE": {record.relative.as_posix() for record in be_records},
    }

    module_lookup = {
        (record.project, record.relative.as_posix()): record.module
        for record in records
    }

    module_edges: Counter[tuple[str, str]] = Counter()

    for record in records:
        source_module = record.module

        for import_name in record.imports:
            target_path = None

            if record.project == "BE":
                target_path = resolve_python_import(
                    import_name,
                    known_paths["BE"],
                )
            else:
                target_path = resolve_ts_import(
                    record.relative,
                    import_name,
                    known_paths["FE"],
                )

            if target_path is None:
                continue

            target_module = module_lookup.get(
                (record.project, target_path)
            )

            if target_module and target_module != source_module:
                module_edges[(source_module, target_module)] += 1

    api_routes = []
    ui_routes = []

    for record in records:
        source = read_text_safe(record.path)

        if record.project == "BE" and record.path.suffix.lower() == ".py":
            for method, route, handler in python_api_routes(source):
                api_routes.append(
                    (
                        f"BE:{record.relative.as_posix()}",
                        method,
                        route,
                        handler,
                    )
                )

        if record.project == "FE" and record.path.suffix.lower() in {".tsx", ".jsx"}:
            for route in frontend_routes(source):
                ui_routes.append(
                    (f"FE:{record.relative.as_posix()}", route)
                )

    git_meta = {
        "FE": git_metadata(frontend),
        "BE": git_metadata(backend),
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    docs = {
        "SYSTEM_CONTEXT_INDEX.md": render_index(
            frontend,
            backend,
            records,
            git_meta,
            output_dir,
        ),
        "SYSTEM_ARCHITECTURE.md": render_architecture(
            records,
            module_edges,
            api_routes,
            ui_routes,
        ),
        "SYSTEM_CONTEXT_BUNDLES.md": render_bundles(
            records_by_project,
        ),
        "SYSTEM_FILE_MAP.md": render_file_map(
            frontend,
            backend,
            records,
            {"FE": fe_excluded, "BE": be_excluded},
            {"FE": fe_excluded_ext, "BE": be_excluded_ext},
            git_meta,
        ),
    }

    for name, content in docs.items():
        path = output_dir / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        print(f"[OK] Wrote {path}")

    print(
        "[OK] Context compile complete: "
        f"{len(records)} source/config files "
        f"(FE={len(fe_records)}, BE={len(be_records)})"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile Lambda Vision source architecture/context maps for LLM handoff."
    )
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    frontend = Path(args.frontend).expanduser().resolve()
    backend = Path(args.backend).expanduser().resolve()

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else frontend / "docs/llm_context"
    )

    compile_context(frontend, backend, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

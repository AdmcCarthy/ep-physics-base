"""Configuration for the domain libraries: a project file wins, the packaged defaults of the installed libraries come next.

A library reads its settings with `load_yaml("config/<name>.yaml")`.  If the project (the working directory, or `EP_PROJECT_ROOT`) has a file of that path, it is read: that is how a host
overrides a default.  Otherwise the file `<name>.yaml` is looked up in the `defaults/` folder of every library that registered itself with `register_defaults`.  So a library works on its
own, and a host that keeps its own `config/` folder sees no change.
"""

from __future__ import annotations

import importlib.resources as resources
import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(os.environ.get("EP_PROJECT_ROOT", Path.cwd()))
_DEFAULT_PACKAGES: list[str] = []


def register_defaults(package: str) -> None:
    """Make the `defaults/` folder of a library package visible to `load_yaml` (called from the package's `__init__`)."""
    if package not in _DEFAULT_PACKAGES:
        _DEFAULT_PACKAGES.append(package)


def resolve_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root unless it is already absolute."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _packaged(name: str) -> Any:
    for package in _DEFAULT_PACKAGES:
        candidate = resources.files(package) / "defaults" / name
        if candidate.is_file():
            return candidate
    return None


def _parse(text: str, label: str) -> dict[str, Any]:
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain a YAML mapping at top level")
    return data


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file into a dict: the project's file if it exists, else the packaged default of the same file name."""
    target = resolve_path(path)
    if target.is_file():
        return _parse(target.read_text(encoding="utf-8"), str(target))
    packaged = _packaged(Path(path).name)
    if packaged is not None:
        return _parse(packaged.read_text(encoding="utf-8"), f"packaged default {Path(path).name}")
    raise FileNotFoundError(f"{path}: not in the project and not among the packaged defaults of {_DEFAULT_PACKAGES}")


def load_defaults(name: str) -> dict[str, Any]:
    """Read a packaged default by file name, ignoring any project file."""
    packaged = _packaged(name)
    if packaged is None:
        raise FileNotFoundError(f"no packaged default named {name} in {_DEFAULT_PACKAGES}")
    return _parse(packaged.read_text(encoding="utf-8"), f"packaged default {name}")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursive merge: mappings are merged key by key, everything else (lists, scalars) in `override` replaces `base`."""
    out = dict(base)
    for key, value in override.items():
        out[key] = deep_merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else value
    return out


def load_unit_factors(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """The unit-factor file (`config/unit_factors.yaml`, or the file named in a pipeline config)."""
    return load_yaml((config or {}).get("unit_factors_file", "config/unit_factors.yaml"))

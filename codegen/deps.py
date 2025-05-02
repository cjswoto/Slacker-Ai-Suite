# codegen/deps.py
import os
import json
import re
from typing import Any, Dict, List, Optional, Union

# Simple pip spec regex
_VALID_SPEC = re.compile(r'^[A-Za-z0-9_.\-]+(?:[<>=!~]=?.+)?$')

def normalize_dependency(dep: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Turn a tech_spec dependency entry into a pip‐installable spec,
    or return None if it shouldn't be installed.
    """
    if isinstance(dep, str):
        spec = dep.strip()
    elif isinstance(dep, dict):
        name = dep.get("name", "").strip()
        version = dep.get("version", "").strip()
        if not name:
            return None
        spec = f"{name}=={version}" if version else name
    else:
        return None

    # Skip invalid specs
    if not _VALID_SPEC.match(spec):
        return None

    # Skip local-module names (e.g. 'gui' or generated_apps directories)
    if os.path.isdir(spec) or spec in {"gui", "generated_apps"}:
        return None

    return spec

def load_dependencies(tech_spec_path: str) -> List[str]:
    """
    Load tech_spec.json, normalize and filter entries,
    returning only real pip specs.
    """
    with open(tech_spec_path, "r", encoding="utf-8") as f:
        tech = json.load(f)

    deps: List[str] = []
    for entry in tech.get("dependencies", []):
        spec = normalize_dependency(entry)
        if spec:
            deps.append(spec)
    return deps

def diff_with_lock(deps: List[str], lockfile_path: str) -> List[str]:
    """
    Compare against a requirements.txt or lockfile to find mismatches.
    Opens the lockfile with errors='ignore' to avoid decoding issues.
    """
    try:
        with open(lockfile_path, "r", encoding="utf-8", errors="ignore") as f:
            locked = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return deps[:]  # no lock → everything considered missing

    mismatches: List[str] = []
    locked_map: Dict[str, Optional[str]] = {}
    for spec in locked:
        if "==" in spec:
            name, ver = spec.split("==", 1)
            locked_map[name.lower()] = ver
        else:
            locked_map[spec.lower()] = None

    for spec in deps:
        if "==" in spec:
            name, ver = spec.split("==", 1)
            if locked_map.get(name.lower()) != ver:
                mismatches.append(spec)
        else:
            if spec.lower() not in locked_map:
                mismatches.append(spec)

    return mismatches

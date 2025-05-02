# req_build.py

import os
import ast
import sys
import warnings

try:
    from importlib.metadata import distributions
except ImportError:
    from importlib_metadata import distributions

EXCLUDED_DIRS = {"venv", ".venv", "__pycache__", ".git", ".tox", ".mypy_cache", "node_modules"}

def find_python_files(root_dir):
    python_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if any(excl in dirpath for excl in EXCLUDED_DIRS):
            continue
        for f in filenames:
            if f.endswith(".py"):
                python_files.append(os.path.join(dirpath, f))
    return python_files

def extract_imports_from_file(filepath):
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=filepath)
        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    imports.add(n.module.split('.')[0])
    except Exception:
        pass
    return imports

def get_all_imports(source_files):
    all_imports = set()
    for file in source_files:
        all_imports |= extract_imports_from_file(file)
    return all_imports

def get_installed_packages():
    """Build a map of top-level imports to PyPI package names."""
    package_map = {}
    for dist in distributions():
        try:
            name = dist.metadata['Name']
            version = dist.version
            modules = set()
            top_level = dist.read_text('top_level.txt')
            if top_level:
                modules.update(line.strip().lower() for line in top_level.splitlines())
            # fallback: use the dist name as import base if nothing else
            if not modules:
                modules.add(name.lower().replace("-", "_"))
            for mod in modules:
                package_map[mod] = (name, version)
        except Exception:
            continue
    return package_map

def map_imports_to_packages(imports, installed_map):
    matched = {}
    unmatched = []
    for imp in imports:
        imp_lower = imp.lower()
        if imp_lower in installed_map:
            pkg_name, version = installed_map[imp_lower]
            matched[pkg_name] = version
        else:
            unmatched.append(imp)
    return matched, unmatched

def write_requirements(packages, filename="generated_requirements.txt"):
    with open(filename, "w") as f:
        for pkg in sorted(packages):
            f.write(f"{pkg}=={packages[pkg]}\n")
    print(f"[+] {len(packages)} packages written to {filename}")

def write_unmatched(unmatched, filename="unmatched_imports.txt"):
    if unmatched:
        with open(filename, "w") as f:
            for imp in sorted(unmatched):
                f.write(f"{imp}\n")
        print(f"[!] {len(unmatched)} unmatched imports written to {filename}")

def main():
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    root = os.path.abspath(os.path.dirname(__file__))
    print(f"[*] Scanning: {root}")

    py_files = find_python_files(root)
    print(f"[*] Found {len(py_files)} Python files")

    imports = get_all_imports(py_files)
    print(f"[+] Found {len(imports)} unique imports")

    installed_map = get_installed_packages()
    matched, unmatched = map_imports_to_packages(imports, installed_map)

    write_requirements(matched)
    write_unmatched(unmatched)

if __name__ == "__main__":
    main()

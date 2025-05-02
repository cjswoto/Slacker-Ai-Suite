# run_codegen_phase3.py
# -*- coding: utf-8 -*-
import os
import re
import sys
import subprocess
import traceback
import json

from config.loader import Config
from utils.logger import get_logger
from codegen.json_extractor import extract_first_json
from codegen.deps import load_dependencies, diff_with_lock
from utils.file_utils import atomic_write

logger = get_logger(__name__)
cfg    = Config()


def pip_install(pkg_str: str):
    logger.info(f"🔧 Installing package: {pkg_str}")
    subprocess.run([sys.executable, "-m", "pip", "install", pkg_str], check=True)


def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def collect_code(root: str) -> str:
    sections = []
    for dp, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(".py"):
                full = os.path.join(dp, fn)
                rel  = os.path.relpath(full, root)
                txt  = open(full, 'r', encoding='utf-8').read()
                sections.append(f"### FILE: {rel}\n{txt}")
    return "\n\n".join(sections)


def sanitize_and_write(root: str, refined: str):
    # Replace malformed Unicode arrows
    refined = refined.replace("â†’", "->").replace("→", "->")

    if "### FILE:" not in refined:
        logger.warning("⚠️ No code blocks found; skipping write.")
        return
    idx = refined.find("### FILE:")
    refined = refined[idx:]
    # Strip Markdown fences
    refined = re.sub(r'```(?:python)?', '', refined)
    refined = re.sub(r'\s*```$', '', refined)

    for part in refined.split("### FILE:"):
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        orig_path = lines[0].strip()
        code_lines = lines[1:]
        # Filter only code/comment lines
        filtered = []
        for line in code_lines:
            if line.startswith(("    ", "\t")):
                filtered.append(line)
            elif line.lstrip().startswith(("def ", "class ", "import ", "from ", "#")):
                filtered.append(line)
        code = "\n".join(filtered).rstrip() + "\n"

        # Compute correct destination path, stripping any leading project prefix
        abs_candidate = os.path.normpath(os.path.join(root, orig_path))
        rel = os.path.relpath(abs_candidate, start=root)
        project_name = os.path.basename(root)
        parts = rel.split(os.sep)
        if parts and parts[0] == project_name:
            rel = os.path.join(*parts[1:]) if len(parts) > 1 else ''
        dest = os.path.join(root, rel) if rel else os.path.join(root, os.path.basename(orig_path))

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(code)
        logger.info(f"Written refined code to: {dest}")


def auto_format(root: str):
    try:
        subprocess.run([sys.executable, "-m", "black", root],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Auto-formatted code with black.")
    except Exception:
        logger.warning("Black formatting skipped (not installed).")


def run_app(root: str):
    entry = os.path.join(root, "main.py")
    if not os.path.exists(entry):
        return False, "main.py not found"
    proc = subprocess.run([sys.executable, entry], cwd=root,
                          capture_output=True, text=True)
    if proc.returncode == 0:
        return True, ""
    return False, proc.stderr or proc.stdout


def extract_missing_module(error: str) -> str:
    m = re.search(r"No module named ['\"]([^'\"]+)['\"]", error)
    return m.group(1) if m else None


def main():
    try:
        root = open(cfg.get_path("last_project_path"), 'r', encoding='utf-8').read().strip()
        logger.info(f"☑ Phase 3: Running in {root}")

        # 1) Pre‐install dependencies
        deps = load_dependencies(cfg.get_path("tech_spec"))
        mismatches = diff_with_lock(deps, "requirements.txt")
        if mismatches:
            logger.warning(f"Dependency lock mismatches: {mismatches}")
        for pkg in deps:
            pip_install(pkg)
        logger.info("All declared dependencies installed.")

        # 2) Initial refinement
        blob = collect_code(root)
        refined = request_refinement(build_refinement_prompt(blob))
        sanitize_and_write(root, refined)
        auto_format(root)
        logger.info("☑ Phase 3: Initial refinement complete.")

        # 3) Run → install missing imports → refine loop
        attempt = 1
        while True:
            logger.info(f"▶️ Attempt {attempt}: Running application…")
            success, output = run_app(root)
            if success:
                logger.info("✅ Application ran successfully!")
                break

            missing = extract_missing_module(output)
            if missing:
                logger.warning(f"Missing module '{missing}', installing…")
                pip_install(missing)
                attempt += 1
                continue

            logger.error(f"❌ Runtime error:\n{output}")
            blob = collect_code(root)
            prompt = build_refinement_prompt(blob + "\n\nError:\n" + output)
            refined = request_refinement(prompt)
            sanitize_and_write(root, refined)
            auto_format(root)
            logger.info("🔄 Refined after error.")
            attempt += 1

        logger.info("🎯 Phase 3 complete: App runs without errors.")
    except Exception:
        logger.error("❌ Phase 3 failed with exception:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

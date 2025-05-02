# run_codegen_phase2.py
# -*- coding: utf-8 -*-
import sys
import os
import json
import logging

from config.loader import Config
from utils.logger import get_logger
from utils.file_utils import atomic_write
from codegen.json_extractor import extract_first_json
from codegen.tech_spec_generator import build_tech_spec_prompt, request_tech_spec
from codegen.spec_generator import send_prompt_for_spec
from samples.validate_spec import validate

# Configure root logger to DEBUG for maximum verbosity
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

cfg = Config()


def main():
    try:
        logger.info("Starting Phase 2: spec generation")

        # 1) Load user description
        desc_file = "samples/user_description.txt"
        if not os.path.exists(desc_file):
            logger.error(f"User description not found: {desc_file}")
            sys.exit(1)

        with open(desc_file, "r", encoding="utf-8") as f:
            desc = f.read().strip()
        logger.debug(f"Loaded user description (desc): {desc!r}")

        # 2) Generate tech spec prompt
        tech_prompt = build_tech_spec_prompt(desc)
        logger.debug(f"Generated tech spec prompt (tech_prompt): {tech_prompt!r}")

        # 3) Request tech spec
        raw_tech = request_tech_spec(tech_prompt)
        logger.debug(f"Received raw tech spec response (raw_tech): {raw_tech!r}")

        # 4) Extract JSON from tech spec response
        try:
            tech_spec = extract_first_json(raw_tech)
            logger.debug(f"Parsed tech_spec JSON: {json.dumps(tech_spec, indent=2)}")
        except Exception as ex:
            logger.error(f"Error extracting tech_spec JSON: {ex}")
            logger.error(f"Full raw_tech response:\n{raw_tech}")
            raise

        # Ensure entry_point ends with .py
        ep = tech_spec.get("entry_point", "")
        if not ep.endswith(".py"):
            logger.warning(f"Fixing entry_point from '{ep}' to 'main.py'")
            tech_spec["entry_point"] = "main.py"

        tech_path = cfg.get_path("tech_spec")
        atomic_write(tech_path, json.dumps(tech_spec, indent=2))
        logger.info(f"Tech spec written & validated: {tech_path}")

        validate(tech_path, cfg.get_path("tech_schema"))
        logger.debug(f"Validation of tech_spec at {tech_path} passed")

        # 5) Generate task spec
        raw_task = send_prompt_for_spec(json.dumps(tech_spec), model_name=cfg.model_name)
        logger.debug(f"Received raw task spec response (raw_task): {raw_task!r}")

        try:
            task_spec = extract_first_json(raw_task)
            logger.debug(f"Parsed task_spec JSON: {json.dumps(task_spec, indent=2)}")
        except Exception as ex:
            logger.error(f"Error extracting task_spec JSON: {ex}")
            # Fixed unterminated f-string by including newline escape
            logger.error(f"Full raw_task response:\n{raw_task}")
            raise

        # 5a) Normalize 'files' field into array of {path,purpose} if it's a dict
        files_field = task_spec.get("files")
        if isinstance(files_field, dict):
            normalized = []
            for folder, file_list in files_field.items():
                if isinstance(file_list, list):
                    for filename in file_list:
                        path = f"{folder}/{filename}"
                        normalized.append({"path": path, "purpose": ""})
            task_spec["files"] = normalized
            logger.debug(f"Normalized task_spec files to array: {json.dumps(normalized, indent=2)}")

        task_path = cfg.get_path("task_spec")
        atomic_write(task_path, json.dumps(task_spec, indent=2))
        logger.info(f"Task spec written & validated: {task_path}")

        # 6) Scaffold project files
        project_name = task_spec.get("project_name", "generated_project")
        logger.debug(f"Scaffolding project: {project_name}")
        root = os.path.join("generated_apps", project_name)
        os.makedirs(root, exist_ok=True)

        for file in task_spec.get("files", []):
            dest = os.path.join(root, file["path"])
            content = f'"""\n{file["purpose"]}\n"""\n\n# Write your code here.\n'
            atomic_write(dest, content)
            logger.debug(f"Scaffolded file: {dest} with purpose: {file['purpose']}")

        # 7) Record path for Phase 3
        last_path = cfg.get_path("last_project_path")
        atomic_write(last_path, root + "\n")
        logger.info(f"Phase 2 complete, project at: {root}")

    except Exception:
        logger.error("Phase 2 failed", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

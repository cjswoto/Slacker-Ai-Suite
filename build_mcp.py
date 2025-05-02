import os

# Directories to create for the full MCP-based codegen pipeline
BASE_DIRS = [
    "config",
    "config/prompt_templates",
    "samples/schemas",
    "samples/specs",
    "codegen",
    "codegen/prompt_templates",
    "utils",
    "generated_apps",
    "runtime",
    "gui",
    "cli",
    ".github/workflows",
    "docs",
    "testing",
    "output"
]

# Files to touch (create empty if not exist)
FILE_PATHS = [
    # Phase 0: Configuration
    "config/config.yaml",
    "config/loader.py",

    # Phase 0: Schemas & Validation
    "samples/schemas/tech_spec_schema.json",
    "samples/schemas/task_spec_schema.json",
    "samples/validate_spec.py",

    # Phase 1: Codegen modules
    "codegen/json_extractor.py",
    "codegen/tech_spec_generator.py",
    "codegen/spec_generator.py",
    "codegen/refiner.py",
    "codegen/deps.py",

    # Phase 2 & 3 entrypoints
    "run_codegen_phase2.py",
    "run_codegen_phase3.py",
    "run_evolution_cycle.py",

    # Phase 4: GUI
    "gui/main_window.py",
    "gui/spec_generator_gui.py",

    # Phase 5: CLI interfaces
    "cli/phase2.py",
    "cli/phase3.py",

    # Utilities
    "utils/file_utils.py",
    "utils/logger.py",

    # Runtime validators
    "runtime/ollama_client.py",
    "runtime/code_validator.py",
    "runtime/lint_validator.py",

    # Testing
    "testing/test_phase1.py",
    "testing/test_phase2.py",
    "testing/test_phase3.py",
    "testing/test_phase4.py",
    "testing/test_controller_gui.py",

    # CI config
    ".github/workflows/ci.yml",

    # Docs
    "docs/README.md"
]


def create_directories():
    for d in BASE_DIRS:
        os.makedirs(d, exist_ok=True)


def touch_files():
    for path in FILE_PATHS:
        dirp = os.path.dirname(path)
        if dirp:
            os.makedirs(dirp, exist_ok=True)
        if not os.path.exists(path):
            # create an empty file
            with open(path, 'w', encoding='utf-8'):
                pass


def main():
    create_directories()
    touch_files()


if __name__ == '__main__':
    main()

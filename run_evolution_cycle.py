import os
import json
from codegen.evolution_engine import EvolutionEngine
from codegen.task_spec_enhancer import enhance_spec_for_gui
from run_codegen_phase2 import main as codegen_phase2_main
from run_codegen_phase3 import main as codegen_phase3_main

PROJECT_NAME = "your-project-name"

def load_spec():
    with open("samples/task_spec.json", "r") as f:
        return json.load(f)

def main():
    project_path = os.path.join(os.getcwd(), PROJECT_NAME)

    evolution = EvolutionEngine(project_path)
    new_spec_path = evolution.evolve_project()

    print(f"✅ New task_spec.json created at {new_spec_path}")

    spec = load_spec()
    spec = enhance_spec_for_gui(spec)

    print("✅ Starting Codegen Phase 2 (new feature generation)...\n")
    codegen_phase2_main()

    print("✅ Starting Codegen Phase 3 (refinement)...\n")
    codegen_phase3_main()

    print("\n🎯 Evolution Cycle Complete.")

if __name__ == "__main__":
    main()

import os
import json
from codegen.self_analyzer import SelfAnalyzer
from codegen.feature_planner import build_feature_planning_prompt, request_feature_plan

class EvolutionEngine:
    def __init__(self, project_path, samples_folder="samples"):
        self.project_path = project_path
        self.samples_folder = samples_folder

    def evolve_project(self):
        analyzer = SelfAnalyzer(self.project_path)
        summary = analyzer.create_summary()

        planning_prompt = build_feature_planning_prompt(summary)
        new_spec_json = request_feature_plan(planning_prompt)

        new_spec_path = os.path.join(self.samples_folder, "task_spec.json")
        with open(new_spec_path, 'w', encoding='utf-8') as f:
            f.write(new_spec_json)

        return new_spec_path

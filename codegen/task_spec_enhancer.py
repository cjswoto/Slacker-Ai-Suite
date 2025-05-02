# codegen/task_spec_enhancer.py

"""
task_spec_enhancer.py

Provides functions to enhance or transform the task_spec.json between codegen phases,
for example to inject GUI-specific metadata or files.
"""

import copy
from typing import Dict, Any

def enhance_spec_for_gui(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhances the given task specification dictionary for GUI projects.

    Currently this is a no-op pass-through. You can modify it to:
      - Add boilerplate GUI files
      - Inject GUI dependencies into spec["dependencies"]
      - Tag files for special handling in Phase 3, etc.

    :param spec: Original task_spec loaded from samples/task_spec.json
    :return: A (deep-copied) spec dict with any enhancements applied
    """
    enhanced = copy.deepcopy(spec)

    # Example (uncomment to enable):
    # if any("gui" in f.get("purpose", "").lower() for f in enhanced.get("files", [])):
    #     # ensure tkinter is in dependencies
    #     deps = set(enhanced.setdefault("dependencies", []))
    #     deps.add("tkinter")
    #     enhanced["dependencies"] = list(deps)
    #
    #     # mark GUI flag in metadata
    #     enhanced.setdefault("metadata", {})["requires_gui"] = True

    return enhanced

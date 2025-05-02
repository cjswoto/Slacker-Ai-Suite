#!/usr/bin/env python
# generate_diagrams.py

import os
from graphviz import Digraph

# ── HARD-CODE GRAPHVIZ PATH ───────────────────────────────────────────────────────
# Adjust this if your dot.exe lives elsewhere
os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"

def generate_class_diagram(output_filename: str = 'class_diagram'):
    """
    Builds and renders the UML Class Diagram.
    Produces <output_filename>.png in the current directory.
    """
    class_diagram = Digraph('ClassDiagram', format='png')
    class_diagram.attr(rankdir='TB', fontsize='12')

    # Define classes and their attributes
    classes = {
        'CommandApp': ['view_mode: str', 'json_data: List[dict]', 'script_path_map: Dict[str,str]'],
        'CoreManager': ['ollama_url: str', 'kb_helper: KBManager', 'sessions: dict', 'current_session'],
        'ChatInterface': ['chat_display', 'entry'],
        'SessionPanel': [],
        'SettingsPanel': [],
        'KBManager': ['KB_FOLDER: str', 'INDEX_FILE: str', 'METADATA_FILE: str'],
        'LocalRetriever': []
    }

    # Create nodes
    for classname, attrs in classes.items():
        # record-style label: {ClassName|attr1\lattr2\l...}
        label = '{' + classname + '|' + ''.join(a + '\\l' for a in attrs) + '}'
        class_diagram.node(classname, shape='record', label=label)

    # Define relationships (edges with labels)
    relationships = [
        ('CommandApp', 'CoreManager', 'uses'),
        ('CoreManager', 'KBManager', 'manages'),
        ('CoreManager', 'LocalRetriever', 'queries'),
        ('ChatInterface', 'CoreManager', 'calls'),
        ('SessionPanel', 'CoreManager', 'calls'),
        ('SettingsPanel', 'CoreManager', 'calls'),
    ]
    for src, dst, lbl in relationships:
        class_diagram.edge(src, dst, label=lbl)

    # Render PNG
    class_diagram.render(output_filename, cleanup=True)
    print(f"[+] UML class diagram written to {output_filename}.png")


def generate_sequence_diagram(output_filename: str = 'sequence_diagram'):
    """
    Builds and renders the Sequence Diagram.
    Produces <output_filename>.png in the current directory.
    """
    seq = Digraph('SequenceDiagram', format='png')
    seq.attr(rankdir='LR', fontsize='12')

    # Participants as boxes
    participants = ['User', 'ChatInterface', 'CoreManager', 'API', 'KBManager', 'LocalRetriever']
    for p in participants:
        seq.node(p, shape='box')

    # Message flows
    messages = [
        ('User', 'ChatInterface', 'type prompt\nclick "Send"'),
        ('ChatInterface', 'CoreManager', 'send_chat(prompt, settings)'),
        ('CoreManager', 'API', 'POST /api/chat'),
        ('API', 'CoreManager', 'ai_response'),
        ('CoreManager', 'ChatInterface', 'return ai_response\nstore session'),

        # KB search flow
        ('User', 'ChatInterface', 'enter KB query\nclick "Search KB"'),
        ('ChatInterface', 'CoreManager', 'search_kb(query, top_k)'),
        ('CoreManager', 'KBManager', 'load_existing_index()'),
        ('KBManager', 'LocalRetriever', 'build_index_from_folder()'),
        ('CoreManager', 'LocalRetriever', 'query_index()'),
        ('LocalRetriever', 'CoreManager', 'results'),
        ('CoreManager', 'ChatInterface', 'return KB results'),
    ]
    for src, dst, lbl in messages:
        seq.edge(src, dst, label=lbl)

    # Render PNG
    seq.render(output_filename, cleanup=True)
    print(f"[+] Sequence diagram written to {output_filename}.png")


def main():
    generate_class_diagram()
    generate_sequence_diagram()


if __name__ == '__main__':
    main()

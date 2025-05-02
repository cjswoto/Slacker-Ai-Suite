#!/usr/bin/env python
# generate_ollama_diagrams.py

import os
from graphviz import Digraph

# ── HARD-CODE GRAPHVIZ PATH ───────────────────────────────────────────────────────
# Adjust this if your dot.exe lives elsewhere
os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"

def generate_class_diagram(output_filename: str = 'ollama_class_diagram'):
    """
    Builds and renders the UML Class Diagram for ollama/ modules.
    Produces <output_filename>.png in the current directory.
    """
    cd = Digraph('OllamaClassDiagram', format='png')
    cd.attr(rankdir='TB', fontsize='12')

    # Only classes defined under ollama/
    classes = {
        'CoreManager': [
            'ollama_url: str',
            'kb_helper: KBManager',
            'sessions: dict',
            'current_session: Session'
        ],
        'API': [
            'get_models(url) → List[str]',
            'chat(url,payload) → dict',
            'check_server_connection(url) → dict'
        ],
        'Search': [
            'perform_web_search(query,…) → dict'
        ],
        'SessionManager': [
            'new_session(model) → dict',
            'store_message_in_session(session,role,msg)',
            'export_session(session,file_path)'
        ],
        'ChatInterface': [
            'parent',
            'on_send_callback',
            'display_message(sender,msg)'
        ],
        'SessionPanel': [
            'list_sessions()',
            'create_session()',
            'export_session(id,path)'
        ],
        'SettingsPanel': [
            'get_models()',
            'apply_search_settings(k)',
            'apply_logging_settings(lvl)'
        ],
        'KBManager': [
            'ensure_kb_folder()',
            'load_existing_index() → (idx,chunks,meta)',
            'scan_and_update_kb() → bool'
        ]
    }

    # Create class nodes
    for name, attrs in classes.items():
        label = '{' + name + '|' + ''.join(attr + '\\l' for attr in attrs) + '}'
        cd.node(name, shape='record', label=label)

    # Define relationships
    rels = [
        ('ChatInterface', 'CoreManager', 'calls'),
        ('SessionPanel',   'CoreManager', 'calls'),
        ('SettingsPanel',  'CoreManager', 'calls'),
        ('CoreManager',    'API',         'uses'),
        ('CoreManager',    'Search',      'uses'),
        ('CoreManager',    'SessionManager','uses'),
        ('CoreManager',    'KBManager',   'manages')
    ]
    for src, dst, lbl in rels:
        cd.edge(src, dst, label=lbl)

    cd.render(output_filename, cleanup=True)
    print(f"[+] Class diagram written to {output_filename}.png")


def generate_sequence_diagram(output_filename: str = 'ollama_sequence_diagram'):
    """
    Builds and renders the Sequence Diagram for a chat + KB search flow
    within the ollama/ modules.
    Produces <output_filename>.png in the current directory.
    """
    sd = Digraph('OllamaSequence', format='png')
    sd.attr(rankdir='LR', fontsize='12')

    # Participants
    participants = ['User', 'ChatInterface', 'CoreManager', 'API', 'KBManager']
    for p in participants:
        sd.node(p, shape='box')

    # Message flow
    msgs = [
        # Chat flow
        ('User',          'ChatInterface', 'type prompt\nclick "Send"'),
        ('ChatInterface', 'CoreManager',   'send_chat(prompt, settings)'),
        ('CoreManager',   'API',           'POST /api/chat'),
        ('API',           'CoreManager',   'return ai_response'),
        ('CoreManager',   'ChatInterface', 'return ai_response\nstore session'),

        # KB search flow
        ('User',          'ChatInterface', 'enter KB query\nclick "Search KB"'),
        ('ChatInterface', 'CoreManager',   'search_kb(query, top_k)'),
        ('CoreManager',   'KBManager',     'load_existing_index()'),
        ('KBManager',     'CoreManager',   'return (idx,chunks,meta)'),
        ('CoreManager',   'ChatInterface', 'return KB results')
    ]

    for src, dst, lbl in msgs:
        sd.edge(src, dst, label=lbl)

    sd.render(output_filename, cleanup=True)
    print(f"[+] Sequence diagram written to {output_filename}.png")


def main():
    generate_class_diagram()
    generate_sequence_diagram()


if __name__ == '__main__':
    main()

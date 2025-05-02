#!/usr/bin/env python
# generate_rest_diagrams.py

import os
from graphviz import Digraph

# ── HARD-CODE GRAPHVIZ PATH ───────────────────────────────────────────────────────
os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"

def generate_class_diagram(output_filename: str = 'rest_class_diagram'):
    """
    Builds and renders the UML Class Diagram for non-ollama modules:
    - CommandApp (main.py)
    - BuildHelpers
    - LocalRetriever
    - ScriptsLoader (menuscripts)
    - OllamaDataPrep scripts
    - Wizard scripts
    """
    cd = Digraph('RestClassDiagram', format='png')
    cd.attr(rankdir='TB', fontsize='12')

    classes = {
        'CommandApp': [
            'view_mode: str',
            'json_data: List[dict]',
            'script_path_map: Dict[str,str]'
        ],
        'BuildHelpers': [
            'SCRIPTS: List[str]',
            'build_helpers()'
        ],
        'LocalRetriever': [
            'build_index_from_folder(path,...)',
            'query_index(idx, chunks, meta, query)'
        ],
        'ScriptsLoader': [
            'load_static_script_list()',
            'find_script_paths(entries)'
        ],
        'CutTrainFile': [
            'split_large_file(input, chunk_size)'
        ],
        'OllamaDataPrep': [
            'prepare_dataset(src, output)',
            'format_jsonl_entries()'
        ],
        'OllamaTrainer': [
            'train_model(config)',
            'monitor_progress()'
        ],
        'PDFMaster': [
            'extract_images(pdf, pages)',
            'export_text_chunks()'
        ],
        'CUDAWizard': [
            'check_cuda_installation()',
            'launch_installer()'
        ],
        'OCRWizard': [
            'locate_tesseract()',
            'validate_ocr()'
        ],
        'OllamaWizard': [
            'check_ollama_version()',
            'download_default_models()'
        ]
    }

    # Create class nodes
    for name, attrs in classes.items():
        label = '{' + name + '|' + ''.join(attr + '\\l' for attr in attrs) + '}'
        cd.node(name, shape='record', label=label)

    # Relationships among them
    rels = [
        ('CommandApp', 'ScriptsLoader', 'uses'),
        ('BuildHelpers', 'CommandApp', 'compiles'),
        ('CommandApp', 'LocalRetriever', 'uses'),
        ('CommandApp', 'BuildHelpers', 'invokes'),
        ('CutTrainFile', 'OllamaDataPrep', 'prepares'),
        ('OllamaDataPrep', 'OllamaTrainer', 'feeds'),
        ('PDFMaster', 'OllamaDataPrep', 'outputs'),
        ('CUDAWizard', 'CommandApp', 'launched_by'),
        ('OCRWizard', 'CommandApp', 'launched_by'),
        ('OllamaWizard', 'CommandApp', 'launched_by'),
    ]
    for src, dst, lbl in rels:
        cd.edge(src, dst, label=lbl)

    cd.render(output_filename, cleanup=True)
    print(f"[+] Class diagram written to {output_filename}.png")


def generate_sequence_diagram(output_filename: str = 'rest_sequence_diagram'):
    """
    Builds and renders the Sequence Diagram for flows in the rest of the code:
    - Launch script flow
    - Data prep & training flow
    - Wizard setup flows
    """
    sd = Digraph('RestSequence', format='png')
    sd.attr(rankdir='LR', fontsize='12')

    participants = [
        'User', 'CommandApp', 'ScriptsLoader',
        'BuildHelpers', 'LocalRetriever',
        'PDFMaster', 'OllamaDataPrep', 'OllamaTrainer',
        'CUDAWizard', 'OCRWizard', 'OllamaWizard'
    ]
    for p in participants:
        sd.node(p, shape='box')

    msgs = [
        # Script launch
        ('User', 'CommandApp', 'click script button'),
        ('CommandApp', 'ScriptsLoader', 'find_script_paths()'),
        ('CommandApp', 'ScriptsLoader', 'load_static_script_list()'),
        ('CommandApp', 'BuildHelpers', 'invoke build_helpers()'),
        ('BuildHelpers', 'CommandApp', 'compiled executables'),

        # Data prep & training
        ('User', 'PDFMaster', 'select PDF + export'),
        ('PDFMaster', 'OllamaDataPrep', 'export_text_chunks()'),
        ('User', 'OllamaDataPrep', 'run data_prep()'),
        ('OllamaDataPrep', 'OllamaTrainer', 'start fine-tuning'),
        ('OllamaTrainer', 'OllamaDataPrep', 'training complete'),

        # Wizard flows
        ('User', 'CUDAWizard', 'launch CUDA setup'),
        ('CUDAWizard', 'CommandApp', 'update config'),
        ('User', 'OCRWizard', 'launch OCR setup'),
        ('OCRWizard', 'CommandApp', 'update config'),
        ('User', 'OllamaWizard', 'launch Ollama setup'),
        ('OllamaWizard', 'CommandApp', 'update config'),
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


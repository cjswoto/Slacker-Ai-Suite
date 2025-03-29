# SLACKER IT – AI Suite

A comprehensive set of **local AI** tools and scripts, covering everything from knowledge-base management to model fine-tuning and PDF data extraction.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Primary GUI Tools](#primary-gui-tools)
  - [Backend Modules](#backend-modules)
- [Scripts Overview](#scripts-overview)
- [License](#license)

---

## Overview

**SLACKER IT – AI Suite** provides an end-to-end solution for:
- **Local AI inference** (using Ollama and other open-source tools)
- **Knowledge base** creation and management
- **PDF text/image extraction**
- **Model fine-tuning** with quantization, LoRA, and more

It features multiple **GUI applications** for user-friendly interaction, alongside **backend modules** handling API calls, session management, web search, and local retrieval.

---

## Key Features

- **Ollama Setup Wizard** – Simplifies installing and configuring the **Ollama** local AI platform  
- **Knowledge Base Manager** – Add and manage text documents in a local knowledge base  
- **Chat Interface** – Interact with local AI models in a user-friendly chat window  
- **PDF Tools** – Convert PDF text into training data, or extract images from PDFs  
- **Model Trainer** – Fine-tune models with LoRA, quantization, and more  
- **Session Management** – Save and restore conversation data, track logs  

---

## Directory Structure

```bash
OllamaFace3/
├── fine-tuned-model/        # Model checkpoints & config
├── kb/                      # Local knowledge base scripts/data
├── local/                   # local_retriever.py for FAISS-based retrieval
├── ollama/
│   ├── core/                # Backend modules: api, core_manager, search, session
│   ├── gui/                 # Chat GUIs, etc.
│   └── OllamaWizard.py      # Setup wizard for Ollama
├── OllamaDataPrep/          # Data prep & training scripts (cuttrainfile, PDFMaster, etc.)
├── output/                  # Generated artifacts (datasets, logs)
├── resources/               # Additional images/data
├── venv/                    # (optional) Python virtual environment
├── main.py                  # Central launcher (SLACKER IT – AI Suite)
├── requirements.txt
└── README.md
```

---

## Installation

1. **Clone or download** this repository.
2. (Optional) **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate    # macOS/Linux
   venv\Scripts\activate       # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Make sure you have **Python 3.7+** and any additional libraries your scripts require (e.g., `torch`, `transformers`, `faiss-cpu`, `Pillow`, etc.).

---

## Usage

### Primary GUI Tools

- **`main.py`** – Launches a unified interface to access all tools in the suite (e.g., knowledge base manager, Ollama wizard, PDF tools, etc.).
- **`OllamaWizard.py`** – Guides you through installing and configuring **Ollama**. Checks system prerequisites, helps with model downloads.
- **`kb_gui.py`** – Manage local text documents, update the knowledge base index, and handle file-based knowledge.
- **`chat_gui_main.py`** – A user-friendly chat interface to interact with your local AI model.
- **`cuttrainfile.py`** – Extract text from PDFs to generate training datasets.
- **`ollamadataprep.py`** / **`ollamatrainer.py`** – Tools for advanced data preparation and model fine-tuning.
- **`PDFMaster.py`** – Extract images from PDFs (e.g., for data or reference).

### Backend Modules

- **`api.py`** – Interacts with the **Ollama** API for listing models, generating responses, and checking server status.
- **`core_manager.py`** – Orchestrates session handling, merges web search/local retrieval results into prompts, and calls `api.py`.
- **`search.py`** – Provides web search capabilities (DuckDuckGo, Google) for context gathering.
- **`session.py`** – Loads, saves, and exports conversation sessions (JSON-based).
- **`local_retriever.py`** – Builds FAISS indexes and retrieves local text chunks for knowledge-based AI prompts.

---

## Scripts Overview

| Script Name        | Purpose                                                   |
|--------------------|-----------------------------------------------------------|
| **`main.py`**      | Central launcher for the entire SLACKER IT – AI Suite     |
| **`OllamaWizard.py`** | Installs/configures Ollama, checks prerequisites, downloads models |
| **`kb_gui.py`**    | GUI for managing local KB text files and indexes          |
| **`chat_gui_main.py`** | Interactive chat interface with local AI models        |
| **`cuttrainfile.py`**  | Generates training datasets from PDFs                 |
| **`ollamadataprep.py`** | Additional data prep scripts (merging text, formatting, etc.) |
| **`ollamatrainer.py`**  | Fine-tune models using quantization, LoRA, etc.       |
| **`PDFMaster.py`** | Extract images from PDF documents                          |
| **`CUDAWizard.py`**| Checks for CUDA installation, helps install if missing    |

**Backend**:
| Script Name        | Purpose                                                   |
|--------------------|-----------------------------------------------------------|
| **`api.py`**       | Communicates with Ollama’s API for model listing, generating responses, etc. |
| **`core_manager.py`** | Orchestrates session data, merges search results, calls `api.py` |
| **`search.py`**    | Web search functionality (DuckDuckGo, Google)            |
| **`session.py`**   | Manages conversation sessions (create, save, load, export) |
| **`local_retriever.py`** | Builds/searches FAISS indexes for local text retrieval |

---

## License
This software is released under a dual licensing model:

Non-Commercial Use:
For personal, academic, or non-profit purposes, the software is available under the MIT License. You are free to use, modify, distribute, and integrate the software into your projects, provided you include the original copyright notice and license text.

Commercial Use:
Any use of this software that generates profit is considered commercial use and is not covered under the MIT License. If you intend to use this software in a profit-making venture, you must obtain a separate commercial license. This license will require you to pay a royalty to the author, unless your project is governed by its own independent agreement.

By using this software, you agree that non-commercial projects will follow the terms of the MIT License, while any commercial application requires a separate licensing agreement. For inquiries regarding commercial licensing or to negotiate royalty terms, please contact: [your email/contact].

---

### Final Notes

- **Customization**: Feel free to rename or rearrange folders/scripts to better suit your workflow.
- **Dependencies**: If you need additional libraries (like `torch` or `transformers` for advanced model usage), install them accordingly.
- **Support**: For issues, consult logs/debug info from the GUIs or backend modules.  

# Uninstall existing packages
pip uninstall torch torchvision torchaudio auto-gptq

# Install PyTorch with CUDA (adjust version as needed)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install transformers and other dependencies
pip install transformers datasets peft
# utils/file_utils.py
import os
import tempfile

def atomic_write(path: str, data: str, mode: str = "w", encoding: str = "utf-8"):
    """
    Atomically write `data` to `path`: writes to a temp file then os.replace().
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    fd, tmp = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

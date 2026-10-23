"""Root entry point wrapper for translate_corpus.py."""

import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
script_path = backend_dir / "scripts" / "translate_corpus.py"

if __name__ == "__main__":
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"
    py_exec = str(venv_python) if venv_python.exists() else sys.executable
    cmd = [py_exec, str(script_path)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd, cwd=str(backend_dir)))

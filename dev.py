"""Use the project venv for local preview when present."""
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
python=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
os.execv(str(python) if python.exists() else sys.executable,
         [str(python) if python.exists() else sys.executable,'-m','carecontext.cli','serve','--host','0.0.0.0','--port',os.getenv('PORT','8000')])

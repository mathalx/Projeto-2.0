"""Ponto de entrada na raiz do projeto.

Permite executar o aplicativo com:

    python -m streamlit run main.py

A implementação permanece em ``src/main.py``.
"""

import sys
from pathlib import Path

# Mantém o wrapper compatível quando executado por um caminho absoluto de
# outro diretório; a lógica de inicialização continua apenas em ``src.main``.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.main import main

if __name__ == "__main__":
    main()

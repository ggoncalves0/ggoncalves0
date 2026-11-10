"""Testes dos scripts que geram as imagens do README.

Para rodar, na raiz do repositório:

    python -m unittest
"""

import sys
from pathlib import Path

# Os scripts ficam em scripts/ e importam uns aos outros pelo nome ("from comum import ...").
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

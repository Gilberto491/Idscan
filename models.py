from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

@dataclass
class Finding:
    projeto: str
    arquivo: str
    linha: int
    campo: str
    tabela_classe: str
    tipagem: str
    status: str
    regra: str
    trecho: str

@dataclass
class Config:
    paths: Dict[str, str]
    scan: Dict[str, Any]
    types: Dict[str, Any]
    rules: Dict[str, Any]
    csv: Dict[str, Any]

    base_dir: Path

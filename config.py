import yaml
import os
from pathlib import Path
from .models import Config

_DEFAULT = {
    "paths": {
        "includes": "./configs/includes.txt",
        "excludes": "./configs/excludes.txt",
    },
    "scan": {
        "file_exts": [".java"],
        "exclude_dirs": [".git", "target", "build", "out", ".idea", ".settings", ".vscode"],
        "only_main_java": True,
        "include_tests": False,
        "near_window": 3,
        "expand_snake_to_camel": True,
    },
    "types": {
        "accepted_field_types": ["String"],
        "accepted_param_types": ["String"],
    },
    "rules": {
        "field_decl": True,
        "param_decl": True,
        "digits_annotation": True,
        "cnpj_annotation": True,
        "pattern_digits_only": True,
        "strip_nondigits": True,
        "column_precision_numeric": True,
        "column_length_14_fixed": True,
        "column_length_info_if_less_than": 20,
        "column_length_ok_if_at_least": 20,
    },
    "csv": {
        "delimiter": ";",
        "columns": {
            "Arquivo": True, "Linha": True, "Campo": True, "TabelaClasse": True,
            "Tipagem": True, "Status": True, "Regra": True, "Trecho": True
        },
        "relative_paths": True,
        "dedupe": True,
        "output": "./relatorio_cnpj.csv",
    },
    "project": {
        "base_dir": "."
    },
}

def _sanitize_win_slashes(s: str) -> str:
    return (
        s.replace('\t', '\\t')
         .replace('\n', '\\n')
         .replace('\r', '\\r')
    )

def _norm_base_dir(base_dir_str: str, config_path: Path) -> Path:
    s = os.path.expandvars(os.path.expanduser(base_dir_str))
    s = _sanitize_win_slashes(s)
    p = Path(s)
    if not p.is_absolute():
        p = (config_path.parent / p)
    return p.resolve()

def load_config(config_path, base_dir: str | None = None) -> Config:
    cfg_path = Path(config_path).resolve()
    data = _DEFAULT.copy()
    with cfg_path.open("r", encoding="utf-8") as f:
        y = yaml.safe_load(f) or {}

    for k, v in y.items():
        if isinstance(v, dict) and k in data and isinstance(data[k], dict):
            data[k] = {**data[k], **v}
        else:
            data[k] = v

    bd_str = base_dir or data.get("project", {}).get("base_dir", ".")
    bd = _norm_base_dir(bd_str, cfg_path)

    return Config (
        paths=data["paths"],
        scan=data["scan"],
        types=data["types"],
        rules=data["rules"],
        csv=data["csv"],
        base_dir=bd,
    )

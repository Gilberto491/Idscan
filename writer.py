import csv
from pathlib import Path
from typing import List
from .models import Finding, Config

def dedupe(rows: List[Finding], base_dir: Path) -> List[Finding]:
    seen = set(); out=[]
    for r in rows:
        rel = r.arquivo
        try:
            rel = str(Path(r.arquivo).resolve().relative_to(base_dir)).replace("\\","/")
        except Exception:
            rel = r.arquivo.replace("\\","/")
        fp = (rel, r.linha, r.campo.lower(), r.regra.lower(), r.tipagem.lower())
        if fp in seen: 
            continue
        seen.add(fp); out.append(r)
    return out

def write_csv(rows: List[Finding], cfg: Config):
    out_path = Path(cfg.csv["output"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols_cfg = cfg.csv["columns"]
    order = [k for k, enabled in cols_cfg.items() if enabled]

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=cfg.csv.get("delimiter",";"))
        w.writerow(order)
        for r in rows:
            arquivo = r.arquivo
            if cfg.csv.get("relative_paths", True):
                try:
                    arquivo = str(Path(r.arquivo).resolve().relative_to(cfg.base_dir)).replace("\\","/")
                except Exception:
                    arquivo = r.arquivo.replace("\\","/")

            row_map = {
                "Arquivo": arquivo,
                "Linha": r.linha,
                "Campo": r.campo,
                "TabelaClasse": r.tabela_classe,
                "Tipagem": r.tipagem,
                "Status": r.status,
                "Regra": r.regra,
                "Trecho": r.trecho,
            }
            w.writerow([row_map.get(k,"") for k in order])
    return out_path

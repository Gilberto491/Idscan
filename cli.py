from pathlib import Path
from .config import load_config
from .scan import walk_and_scan
from .writer import write_csv, dedupe

PKG_DIR     = Path(__file__).resolve().parent   
CONFIG_PATH = (PKG_DIR / "configs" / "config.yaml").resolve()

def main():
    cfg = load_config(str(CONFIG_PATH))

    config_root  = CONFIG_PATH.parent

    def norm_list_path(p_str: str) -> Path:
        p = Path(p_str)
        if p.is_absolute():
            return p
        return (config_root / p).resolve()

    cfg.paths["includes"] = str(norm_list_path(cfg.paths["includes"]))
    cfg.paths["excludes"] = str(norm_list_path(cfg.paths["excludes"]))

    # --- força saída do CSV para idscan/reports ---
    reports_dir = PKG_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    cfg.csv["output"] = str((reports_dir / Path(cfg.csv["output"]).name).resolve())

    print(f"[i] Varredura em: {cfg.base_dir}")

    rows, files_scanned = walk_and_scan(cfg.base_dir, cfg)

    if cfg.csv.get("dedupe", True):
        rows = dedupe(rows, cfg.base_dir)

    out_path = write_csv(rows, cfg)
    total  = len(rows)
    issues = sum(1 for r in rows if r.status == "ISSUE")
    oks    = sum(1 for r in rows if r.status == "OK")
    infos  = sum(1 for r in rows if r.status == "INFO")

    print(f"[i] Arquivos analisados: {files_scanned}")
    print(f"[✓] Terminado. Linhas: {total} | ISSUE: {issues} | OK: {oks} | INFO: {infos}")
    print(f"[→] CSV gerado: {Path(out_path).resolve()}")

if __name__ == "__main__":
    main()

from pathlib import Path
from typing import List, Tuple
import re
from .models import Finding, Config
from .patterns import compile_patterns, near_target_identifier, has_exclude

def _project_name(fpath: Path, base: Path) -> str:
    try:
        rel = fpath.resolve().relative_to(base)
        return rel.parts[0] if rel.parts else base.name
    except Exception:
        return base.name

def _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN):
    cls, table, seen_entity = None, None, False
    for i in range(idx, -1, -1):
        line = lines[i]
        if table is None:
            mtab = TABLE_ANN.search(line)
            if mtab: table = mtab.group("table")
        if not seen_entity and ENTITY_ANN.search(line):
            seen_entity = True
        if cls is None:
            mcls = CLASS_DECL.search(line)
            if mcls:
                cls = mcls.group("cls")
                if seen_entity or table: break
    return cls or "", table or ""

def analyze_file(fpath: Path, cfg: Config, pats) -> List[Finding]:
    try:
        text = fpath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    lines = text.splitlines()
    proj = _project_name(fpath, cfg.base_dir)

    F = []
    win = int(cfg.scan.get("near_window", 3))

    FIELD_DECL  = pats["FIELD_DECL"]
    PARAM_DECL  = pats["PARAM_DECL"]
    LOCAL_DECL  = pats["LOCAL_DECL"]
    CLASS_DECL  = pats["CLASS_DECL"]
    TABLE_ANN   = pats["TABLE_ANN"]
    ENTITY_ANN  = pats["ENTITY_ANN"]
    COLUMN_ANN  = pats["COLUMN_ANN"]
    PRECISION   = pats["PRECISION"]
    LENGTH      = pats["LENGTH"]
    ANN_CNPJ    = pats["ANN_CNPJ"]
    ANN_DIGITS  = pats["ANN_DIGITS"]
    ANN_PATTERN = pats["ANN_PATTERN"]
    REPL_NONDIG = pats["REPL_NONDIG"]
    ID_PATTERN  = pats["ID_PATTERN"]
    EXC_PATTERN = pats["EXCLUDE_PATTERN"]

    def _ok_type(tp: str, is_param=False) -> bool:
        accepted = cfg.types["accepted_param_types" if is_param else "accepted_field_types"]
        return tp in accepted
    
    def is_excluded_name(name: str) -> bool:
        return bool(EXC_PATTERN and EXC_PATTERN.search(name or ""))
    
    def has_include(pattern, text: str) -> bool:
        return bool(pattern and pattern.search(text or ""))

    def allowed_context(lines, idx) -> bool:
        return has_include(ID_PATTERN, lines[idx]) or near_target_identifier(lines, idx, win, ID_PATTERN)

    # validações globais (próximas de alvo)
    for idx, line in enumerate(lines):

        if cfg.rules.get("annotation") and ANN_CNPJ.search(line):
            cls, table = _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN)
            F.append(Finding(proj, str(fpath), idx+1, "", table or cls or "", "", "ISSUE", "hibernate_br_cnpj", line.strip()[:300]))

        if LOCAL_DECL:
            for lm in LOCAL_DECL.finditer(line):
                if not allowed_context(lines, idx):
                    continue
                tp   = lm.group("type")
                name = lm.group("name")
                if is_excluded_name(name):
                    continue
                cls, table = _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN)
                status = "OK" if _ok_type(tp, is_param=True) else "ISSUE"
                regra  = "local_string" if status == "OK" else "local_numeric"
                F.append(Finding(proj, str(fpath), idx+1, name, table or cls or "", tp, status, regra, line.strip()[:300]))

        if COLUMN_ANN.search(line) and near_target_identifier(lines, idx, win, ID_PATTERN, EXC_PATTERN):
            args = COLUMN_ANN.search(line).group("args")
            cls, table = _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN)
            status = None; regra=None; tip="@Column"
            if cfg.rules.get("column_precision_numeric"):
                if PRECISION.search(args):
                    status, regra = "ISSUE", "column_precision_numeric"
            if cfg.rules.get("column_length_14_fixed") or cfg.rules.get("column_length_ok_if_at_least"):
                mlen = LENGTH.search(args)
                if mlen:
                    length = int(mlen.group(1))
                    if cfg.rules.get("column_length_14_fixed") and length == 14:
                        status, regra = "ISSUE", "column_length_14_fixed"
                    else:
                        ok_at = int(cfg.rules.get("column_length_ok_if_at_least", 0))
                        info_lt = int(cfg.rules.get("column_length_info_if_less_than", 0))
                        if length >= ok_at:
                            status, regra = "OK", f"column_length_{length}"
                        elif length < info_lt and length != 14:
                            status, regra = "INFO", f"column_length_{length}"
            if status:
                F.append(Finding(proj, str(fpath), idx+1, "", table or cls, tip, status, regra, line.strip()[:300]))

    # campos e params (filtrados por includes/excludes)
    for idx, line in enumerate(lines):
        mf = FIELD_DECL.search(line)
        if mf:
            tp   = mf.group("type")
            name = mf.group("name")
            if is_excluded_name(name):
                pass
            else:
                cls, table = _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN)
                status = "OK" if _ok_type(tp, is_param=False) else "ISSUE"
                regra  = "field_string" if status == "OK" else "field_numeric"
                F.append(Finding(proj, str(fpath), idx+1, name, table or cls or "", tp, status, regra, line.strip()[:300]))

        for pm in PARAM_DECL.finditer(line):
            tp = pm.group("type"); name = pm.group("name")
            if is_excluded_name(name):
                continue
            cls, table = _find_enclosing(lines, idx, CLASS_DECL, TABLE_ANN, ENTITY_ANN)
            status = "OK" if _ok_type(tp, is_param=True) else "ISSUE"
            regra  = "param_string" if status=="OK" else "param_numeric"
            F.append(Finding(proj, str(fpath), idx+1, name, cls, tp, status, regra, line.strip()[:300]))
    return F

def walk_and_scan(base_dir: Path, cfg: Config) -> Tuple[List[Finding], int]:
    pats = compile_patterns(cfg)
    rows: List[Finding] = []
    files_scanned = 0
    exts = cfg.scan.get("file_exts", [])

    for f in base_dir.rglob("*"):
        if any(part in set(map(str, cfg.scan["exclude_dirs"])) for part in f.parts):
            continue
        if f.is_file() and (not exts or f.suffix in exts):
            parts = set(p.lower() for p in f.parts)
            if cfg.scan.get("only_main_java", True) and not {"src","main","java"}.issubset(parts): 
                continue
            files_scanned += 1
            rows.extend(analyze_file(f, cfg, pats))
    return rows, files_scanned

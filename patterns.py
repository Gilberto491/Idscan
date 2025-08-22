from pathlib import Path 
import re
from typing import List
from .loader import load_tokens, expand_snake_to_camel

def compile_patterns(cfg):
    inc_path = Path(cfg.paths["includes"])
    exc_path = Path(cfg.paths["excludes"])

    includes = load_tokens(inc_path)
    excludes = load_tokens(exc_path)

    if cfg.scan.get("expand_snake_to_camel", True):
        includes = expand_snake_to_camel(includes)
        excludes = expand_snake_to_camel(excludes)

    if cfg.scan.get("verbose", False):
        print(f"[i] Includes carregados: {len(includes)} de {inc_path}")
        print(f"[i] Excludes carregados: {len(excludes)} de {exc_path}")

    ident_esc = [re.escape(x) for x in includes]
    excl_esc  = [re.escape(x) for x in excludes]

    re_ident_group = "(" + "|".join(ident_esc) + ")" if ident_esc else "(?!)"
    ID_PATTERN      = re.compile("(" + "|".join(ident_esc) + ")", re.I) if ident_esc else None
    EXCLUDE_PATTERN = re.compile("(" + "|".join(excl_esc) + ")", re.I) if excl_esc else None

    TYPES = cfg.types.get("allowed_java", ["Long","Integer","BigInteger","String"])
    TYPES_ALT = "|".join(map(re.escape, TYPES))

    FIELD_DECL = re.compile(
        rf"\b(private|protected|public)\s+(?:static\s+|final\s+)*"
        rf"(?P<type>{TYPES_ALT})(?:\s*<[^>]+>)?(?:\[\])*"  
        rf"\s+(?P<name>[A-Za-z0-9_]*{re_ident_group}[A-Za-z0-9_]*)"
        rf"\s*(?:=|;)",                                   
        re.I,
    )
    PARAM_DECL = re.compile(
        rf"\b(?P<type>{TYPES_ALT})\s+(?P<name>[A-Za-z0-9_]*{re_ident_group}[A-Za-z0-9_]*)\b",
        re.I,
    )
    LOCAL_PATTERN = re.compile(
        r'\b(?:String|Integer|Long|Double|BigDecimal|Date|boolean|int|float|char)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    )
    LOCAL_DECL = re.compile(
        rf"""
        ^\s*                                         

        (?!.*\b(private|protected|public)\b)          
        (?!\s*\bclass\b)(?!\s*\binterface\b)(?!\s*\benum\b) 

        (?P<type>{TYPES_ALT})                         
            (?:\s*<[^>;]+>)?                          
            (?:\s*\[\s*\])*                           

        \s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)           
        (?!\s*\()                                     
        \s*(=|;)\s*                                   
        """,
        re.I | re.X,
    )


    CLASS_DECL   = re.compile(r"\bclass\s+(?P<cls>[A-Za-z_]\w*)")
    ENTITY_ANN   = re.compile(r"@Entity\b")
    TABLE_ANN    = re.compile(r'@Table\s*\(\s*name\s*=\s*"(?P<table>[^"]+)"')
    COLUMN_ANN   = re.compile(r"@Column\s*\((?P<args>[^)]*)\)")
    PRECISION    = re.compile(r"\bprecision\s*=\s*(\d+)", re.I)
    LENGTH       = re.compile(r"\blength\s*=\s*(\d+)", re.I)
    ANN_CNPJ     = re.compile(r"@(?:org\.hibernate\.validator\.constraints\.br\.)?CNPJ\b")
    ANN_DIGITS   = re.compile(r"@Digits\s*\(", re.I)
    ANN_PATTERN  = re.compile(r'@Pattern\s*\(\s*regexp\s*=\s*(?P<rx>[^),]+)')
    REPL_NONDIG  = re.compile(r'\.replaceAll\(\s*"\\\\D"\s*,\s*""\s*\)')

    return {
        "ID_PATTERN": ID_PATTERN,
        "EXCLUDE_PATTERN": EXCLUDE_PATTERN,
        "FIELD_DECL": FIELD_DECL,
        "PARAM_DECL": PARAM_DECL,
        "LOCAL_DECL": LOCAL_DECL,
        "LOCAL_PATTERN": LOCAL_PATTERN,
        "CLASS_DECL": CLASS_DECL,
        "ENTITY_ANN": ENTITY_ANN,
        "TABLE_ANN": TABLE_ANN,
        "COLUMN_ANN": COLUMN_ANN,
        "PRECISION": PRECISION,
        "LENGTH": LENGTH,
        "ANN_CNPJ": ANN_CNPJ,
        "ANN_DIGITS": ANN_DIGITS,
        "ANN_PATTERN": ANN_PATTERN,
        "REPL_NONDIG": REPL_NONDIG,
    }

def has_include(ID_PATTERN, text: str) -> bool:
    return bool(ID_PATTERN and ID_PATTERN.search(text or ""))

def has_exclude(EXCLUDE_PATTERN, text: str) -> bool:
    return bool(EXCLUDE_PATTERN and EXCLUDE_PATTERN.search(text or ""))

def near_target_identifier(lines: List[str], idx: int, window: int, ID_PATTERN, EXCLUDE_PATTERN=None) -> bool:
    for off in range(-window, window+1):
        j = idx + off
        if 0 <= j < len(lines) and has_include(ID_PATTERN, lines[j]):
            if EXCLUDE_PATTERN and has_exclude(EXCLUDE_PATTERN, lines[j]):
                continue
            return True
    return False

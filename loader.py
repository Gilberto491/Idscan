from pathlib import Path
from typing import List

def _read_text_any(path: Path) -> str:
    for enc in ("utf-8-sig","utf-8","latin-1","utf-16","utf-16-le","utf-16-be"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")

def load_tokens(path: Path) -> List[str]:
    if not path.exists(): return []
    raw = _read_text_any(path)
    out, seen = [], set()
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";") or s.startswith("//"): continue
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        key = s.lower()
        if key not in seen:
            seen.add(key); out.append(s)
    return out

def expand_snake_to_camel(tokens):
    out, seen = [], set()
    for t in tokens:
        cand = [t]
        if "_" in t:
            parts = [p for p in t.split("_") if p]
            if parts:
                camel = parts[0] + "".join(p[0].upper() + p[1:] for p in parts[1:])
                cand.append(camel)
        for c in cand:
            k = c.lower()
            if k not in seen:
                seen.add(k); out.append(c)
    return out

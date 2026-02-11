# -*- coding: utf-8 -*-
import os, re, json, csv, argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Iterable, Optional

# RUTAS POR DEFECTO
# RUTAS (ANONIMIZADAS)
DEFAULT_INPUT     = os.getenv("DEFAULT_INPUT", "./Para_corregir_SQL")
DEFAULT_CANON_DIR = os.getenv("DEFAULT_CANON_DIR", "./Consignas_SQL")
DEFAULT_OUTPUT    = os.getenv("DEFAULT_OUTPUT", "./Depuracion_SQL")

_re_ws = re.compile(r"\s+")

def norm_space(s: str) -> str:
    return _re_ws.sub(" ", (s or "").strip())

def is_crosstab(sql: str) -> bool:
    s = (sql or "").upper()
    return "TRANSFORM" in s and "PIVOT" in s

def _agg_func(sql: str) -> str:
    m = re.search(r"\bTRANSFORM\s+(\w+)\s*\(", sql, re.I)
    return (m.group(1).upper() if m else "")

def _pivot_expr(sql: str) -> str:
    m = re.search(r"\bPIVOT\s+(.+?)(?:;|$)", sql, re.I | re.S)
    return norm_space(m.group(1)) if m else ""

def _tables_in_from(sql: str) -> List[str]:
    tables = set()
    for m in re.finditer(r"\bFROM\b\s+(.+?)(?:\bWHERE\b|\bGROUP\b|\bPIVOT\b|;|$)", sql, re.I | re.S):
        from_part = m.group(1)
        parts = re.split(r"\bJOIN\b|,", from_part, flags=re.I)
        for p in parts:
            t = re.split(r"\bon\b|\bas\b|\s", p.strip(), flags=re.I)[0]
            if t and not t.startswith("("):
                tables.add(t.strip("[]"))
    return sorted(tables)

def parse_crosstab_fingerprint(sql: str) -> Dict[str, Any]:
    return {"agg": _agg_func(sql), "pivot": _pivot_expr(sql), "tables": _tables_in_from(sql)}

def _collect_items(obj) -> Iterable[Dict[str, Any]]:
    if obj is None:
        return []
    if isinstance(obj, dict) and "items" in obj and isinstance(obj["items"], list):
        for it in obj["items"]:
            name = str(it.get("name", "")); sql  = str(it.get("sql", ""))
            if sql.strip():
                yield {"name": name, "sql": sql}
        return
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict) and "sql" in it:
                yield {"name": str(it.get("name","")), "sql": str(it.get("sql",""))}
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.strip():
                yield {"name": str(k), "sql": v}
            elif isinstance(v, dict) and "sql" in v:
                yield {"name": str(k), "sql": str(v.get("sql",""))}

def load_items_from_json(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return list(_collect_items(data))

def consigna_from_query_name(qname: str) -> str:
    m = re.match(r"^\s*Consulta\s*(\d+)", str(qname), re.I)
    if not m:
        return ""
    return f"Consigna_{int(m.group(1))}"

def load_canonic_fp(canonic_json: Path) -> Dict[str, Dict[str, Any]]:
    mapping = {}
    items = load_items_from_json(canonic_json)
    for it in items:
        name = it.get("name",""); sql  = it.get("sql","")
        if not is_crosstab(sql):
            continue
        if re.search(r"Consulta\s*[2-5]\s*b", name or "", re.I):
            cons = consigna_from_query_name(name)
            if cons:
                mapping[cons] = parse_crosstab_fingerprint(sql)
    if not mapping:
        for it in items:
            name = it.get("name",""); sql  = it.get("sql","")
            if is_crosstab(sql):
                cons = consigna_from_query_name(name)
                if cons and cons not in mapping:
                    mapping[cons] = parse_crosstab_fingerprint(sql)
    return mapping

def jaccard(a, b) -> float:
    A, B = set(a), set(b)
    if not A and not B:
        return 1.0
    inter = len(A & B); uni = len(A | B)
    return inter / uni if uni else 0.0

def score_similarity(stu_fp, can_fp):
    w_tables, w_agg, w_pivot = 0.45, 0.25, 0.30
    s_tables = jaccard(stu_fp.get("tables", []), can_fp.get("tables", []))
    s_agg    = 1.0 if (stu_fp.get("agg","").upper() == can_fp.get("agg","").upper() and stu_fp.get("agg","")!="") else 0.0
    s_pivot  = 1.0 if (norm_space(stu_fp.get("pivot","")) == norm_space(can_fp.get("pivot","")) and stu_fp.get("pivot","")!="") else 0.0
    total = round(100*(w_tables*s_tables + w_agg*s_agg + w_pivot*s_pivot), 1)
    dbg = {"tables_student": stu_fp.get("tables", []),
           "tables_canonic": can_fp.get("tables", []),
           "agg_student": stu_fp.get("agg",""),
           "agg_canonic": can_fp.get("agg",""),
           "pivot_student": stu_fp.get("pivot",""),
           "pivot_canonic": can_fp.get("pivot","")}
    return total, dbg

def auto_find_canonico(canon_dir: Path) -> Optional[Path]:
    if not canon_dir.is_dir():
        return None
    pat_cons  = re.compile(r"consignas", re.I)
    pat_canon = re.compile(r"can[oó]nico", re.I)
    pat_tema  = re.compile(r"tema", re.I)
    candidates = []
    for p in canon_dir.glob("*.json"):
        name = p.name; score = 0
        if pat_cons.search(name):  score += 2
        if pat_canon.search(name): score += 2
        if pat_tema.search(name):  score += 1
        if score > 0:
            candidates.append((score, p.stat().st_mtime, p))
    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return candidates[0][2]

def compare_folder(input_folder: Path, canonic_fp, out_folder: Path):
    out_folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for root, _, files in os.walk(input_folder):
        root_path = Path(root)
        try:
            rel = root_path.relative_to(input_folder)
            alumno = rel.parts[0] if rel.parts else root_path.name
        except Exception:
            alumno = root_path.name
        alumno_rows = []
        for fn in files:
            if not fn.lower().endswith(".json"):
                continue
            json_path = root_path / fn
            items = load_items_from_json(json_path)
            for it in items:
                name = str(it.get("name","")); sql  = str(it.get("sql",""))
                if not is_crosstab(sql):
                    continue
                stu_fp = parse_crosstab_fingerprint(sql)
                best = {"consigna":"-", "score":0.0, "dbg":{}}
                for cons, fp in canonic_fp.items():
                    score, dbg = score_similarity(stu_fp, fp)
                    if score > best["score"]:
                        best = {"consigna": cons, "score": score, "dbg": dbg}
                row = {"alumno": alumno,
                       "file": json_path.name,
                       "query_name": name,
                       "consigna_asignada": best["consigna"],
                       "similitud_%": best["score"],
                       "detalle_tablas": f"{best['dbg'].get('tables_student', [])} vs {best['dbg'].get('tables_canonic', [])}",
                       "detalle_agg": f"{best['dbg'].get('agg_student','')}/{best['dbg'].get('agg_canonic','')}",
                       "detalle_pivot": f"{best['dbg'].get('pivot_student','')}/{best['dbg'].get('pivot_canonic','')}",}
                alumno_rows.append(row); rows.append(row)
        if alumno_rows:
            part_csv = out_folder / f"{alumno}_matching_crosstab.csv"
            with part_csv.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(alumno_rows[0].keys()))
                w.writeheader()
                for r in alumno_rows:
                    w.writerow(r)
    cons_csv = out_folder / "_consolidado_matching_crosstab.csv"
    with cons_csv.open("w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
    print(f"✅ Matching finalizado. Total de filas comparadas: {len(rows)}")
    print(f"➡️  Consolidado: {cons_csv}")
    print(f"➡️  Carpeta destino: {out_folder}")

def main():
    ap = argparse.ArgumentParser(description="Comparación de CROSSTAB de alumnos vs canónico (similitud estructural).")
    ap.add_argument("--input", default=DEFAULT_INPUT, help="Carpeta raíz con subcarpetas por alumno (contienen consultas.json).")
    ap.add_argument("--canonico", help="Ruta al JSON canónico (si se omite, se busca automáticamente en --canon_dir).")
    ap.add_argument("--canon_dir", default=DEFAULT_CANON_DIR, help="Carpeta donde buscar el canónico automáticamente.")
    ap.add_argument("--out", default=DEFAULT_OUTPUT, help="Carpeta de salida para CSVs.")
    args = ap.parse_args()

    input_folder = Path(args.input)
    out_folder   = Path(args.out)

    if not input_folder.exists():
        raise SystemExit(f"[Error] Carpeta de origen no existe: {input_folder}")
    out_folder.mkdir(parents=True, exist_ok=True)

    if args.canonico:
        canonic_path = Path(args.canonico)
        print(f"[INFO] Usando canónico explícito: {canonic_path}")
    else:
        search_dir = Path(args.canon_dir) if args.canon_dir else (input_folder.parent / "Consignas_SQL")
        canonic_path = auto_find_canonico(search_dir)
        print(f"[INFO] Buscando canónico automáticamente en: {search_dir}")
        if canonic_path:
            print(f"[OK] Canónico detectado: {canonic_path}")

    if not canonic_path or not canonic_path.is_file():
        raise SystemExit(f"[Error] No se encontró el JSON canónico. Revisá --canonico o --canon_dir. Buscado: {canonic_path}")

    can_fp = load_canonic_fp(canonic_path)
    if not can_fp:
        raise SystemExit("[Error] No se pudieron obtener fingerprints canónicos (revisá el JSON canónico).")

    compare_folder(input_folder, can_fp, out_folder)

if __name__ == "__main__":
    main()

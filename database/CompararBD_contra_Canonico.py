# CompararBD_contra_Canonico.py
# --------------------------------
# Compara los .json de alumnos contra el canónico del Tema B,
# ignorando mayúsculas, tildes y espacios en los nombres.
# Graba resumen_similitud.csv en la carpeta de salida indicada.

import os
import json
import csv
import unicodedata

# ==== RUTAS FIJAS (según lo que indicaste) ====
# ==== RUTAS (ANONIMIZADAS) ====
# Configurables por variables de entorno o editar aquí
CARPETA_ORIGEN_JSON = os.getenv("CARPETA_ORIGEN_JSON", "./Para_corregir_BD")
CARPETA_CANONICO    = os.getenv("CARPETA_CANONICO", ".")
NOMBRE_CANONICO     = "Canónico_2c2025_TemaB_schema.json"
CARPETA_SALIDA      = os.getenv("CARPETA_SALIDA", "./Grado_Similitud")
NOMBRE_SALIDA_CSV   = "resumen_similitud.csv"

# ==== Normalización de nombres (ignora mayúsculas/tildes/espacios) ====
def norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # quita tildes
    s = s.lower().replace(" ", "_").replace("-", "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")

# ==== Cargar esquema desde JSON ====
def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tablas
    tabs = {norm(t["table"]) for t in data.get("tables", [])}

    # Campos y PKs
    fields = {}
    pks = {}
    for fdef in data.get("fields", []):
        t = norm(fdef["table"])
        fld = norm(fdef["field"])
        fields.setdefault(t, set()).add(fld)
        if fdef.get("pk"):
            pks.setdefault(t, set()).add(fld)

    # Relaciones
    rels = {}
    for r in data.get("relations", []):
        parent = norm(r["parent_table"])
        child = norm(r["child_table"])
        key = (child, parent)
        pairs = [(norm(p["child_field"]), norm(p["parent_field"])) for p in r.get("fields", [])]
        rels.setdefault(key, []).append({
            "pairs": pairs,
            "enforced": bool(r.get("enforced", False)),
            "uc": bool(r.get("update_cascade", False)),
            "dc": bool(r.get("delete_cascade", False)),
        })

    return {"tabs": tabs, "fields": fields, "pks": pks, "rels": rels}

# ==== Cálculo de similitud ====
def score_student(canon, stud):
    # 1) Tablas (30 %)
    required = canon["tabs"]
    present  = stud["tabs"]
    s_tabs = len(required & present) / len(required) if required else 1.0

    # 2) Campos (30 %)
    num = den = 0
    for t in required:
        c_fields = canon["fields"].get(t, set())
        s_fields = stud["fields"].get(t, set())
        den += len(c_fields)
        num += len(c_fields & s_fields)
    s_fields = (num / den) if den else 1.0

    # 3) PKs (20 %)
    num = den = 0
    for t in required:
        c_pks = canon["pks"].get(t, set())
        s_pks = stud["pks"].get(t, set())
        den += len(c_pks)
        num += len(c_pks & s_pks)
    s_pks = (num / den) if den else 1.0

    # 4) Relaciones (20 %)
    acc = 0.0
    den = 0
    for key_c, rel_list_c in canon["rels"].items():
        for rel_c in rel_list_c:
            den += 1
            best = 0.0
            cand_list = stud["rels"].get(key_c, [])
            for rel_s in cand_list:
                set_c = set(rel_c["pairs"])
                set_s = set(rel_s["pairs"])
                if set_c:
                    pair_score = len(set_c & set_s) / len(set_c)
                else:
                    pair_score = 1.0
                # pequeñas penalizaciones si no coinciden atributos de relación
                if rel_c["enforced"] != rel_s["enforced"]:
                    pair_score *= 0.90
                if rel_c["uc"] != rel_s["uc"]:
                    pair_score *= 0.95
                if rel_c["dc"] != rel_s["dc"]:
                    pair_score *= 0.95
                if pair_score > best:
                    best = pair_score
            acc += best
    s_rels = acc / den if den else 1.0

    total = (0.30 * s_tabs + 0.30 * s_fields + 0.20 * s_pks + 0.20 * s_rels) * 100
    return round(100 * s_tabs, 1), round(100 * s_fields, 1), round(100 * s_pks, 1), round(100 * s_rels, 1), round(total, 1)

# ==== Main ====
def main():
    # asegurar carpeta de salida
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # cargar canónico
    canon_path = os.path.join(CARPETA_CANONICO, NOMBRE_CANONICO)
    if not os.path.isfile(canon_path):
        raise FileNotFoundError(f"No se encontró el canónico: {canon_path}")
    canon = load_schema(canon_path)

    csv_out = os.path.join(CARPETA_SALIDA, NOMBRE_SALIDA_CSV)

    with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "%Tablas", "%Campos", "%PKs", "%Relaciones", "%Total"])

        for fn in sorted(os.listdir(CARPETA_ORIGEN_JSON)):
            if not fn.lower().endswith(".json"):
                continue
            stud_path = os.path.join(CARPETA_ORIGEN_JSON, fn)
            # por las dudas, saltar el canónico si alguien lo copia ahí
            if os.path.abspath(stud_path) == os.path.abspath(canon_path):
                continue
            try:
                stud = load_schema(stud_path)
                s_tabs, s_fields, s_pks, s_rels, total = score_student(canon, stud)
                w.writerow([fn, s_tabs, s_fields, s_pks, s_rels, total])
            except Exception as e:
                w.writerow([fn, "ERROR", "ERROR", "ERROR", "ERROR", str(e)])

    print("✅ Listo. Archivo generado en:")
    print(csv_out)

if __name__ == "__main__":
    main()

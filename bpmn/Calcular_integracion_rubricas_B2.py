import os
import csv

# ============================================================
# CONFIGURACIÓN DE RUTAS Y ARCHIVOS
# ============================================================

BASE_DIR = os.getenv("RUBRICA_BASE_DIR", "./Rubrica_Tecnica")
TEC_CSV = os.path.join(BASE_DIR, "Evaluacion_BPMN_Tecnica_B2.csv")
ADM_CSV = os.path.join(BASE_DIR, "Evaluacion_BPMN_Administrativa_B2.csv")

OUT_CSV = os.path.join(BASE_DIR, "Notas_BPMN_B2.csv")


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def leer_csv_a_dict(path, clave_col):
    """
    Lee un CSV y devuelve un diccionario:
    { valor_clave: fila_completa(dict) }
    """
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[clave_col]
            data[key] = row
    return data


def to_float(value, default=0.0):
    """
    Convierte un string a float.
    Si falla, devuelve default.
    """
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    if not os.path.isfile(TEC_CSV):
        print(f"No se encontró archivo técnico: {TEC_CSV}")
        return
    if not os.path.isfile(ADM_CSV):
        print(f"No se encontró archivo administrativo: {ADM_CSV}")
        return

    # Leemos ambos CSV a diccionarios indexados por 'archivo'
    tec = leer_csv_a_dict(TEC_CSV, "archivo")
    adm = leer_csv_a_dict(ADM_CSV, "archivo")

    # Unimos las claves (nombres de archivo)
    todos_archivos = sorted(set(tec.keys()) | set(adm.keys()))

    resultados = []

    for arch in todos_archivos:
        fila_tec = tec.get(arch, {})
        fila_adm = adm.get(arch, {})

        # Columnas esperadas de entrada:
        # - puntaje_tecnico_pct
        # - puntaje_administrativo_pct
        nota_tec = to_float(fila_tec.get("puntaje_tecnico_pct", 0.0))
        nota_adm = to_float(fila_adm.get("puntaje_administrativo_pct", 0.0))

        icg = round(0.55 * nota_tec + 0.45 * nota_adm, 2)

        resultados.append({
            "archivo": arch,
            "nota_tecnica_pct": nota_tec,
            "nota_administrativa_pct": nota_adm,
            "ICG_pct": icg,
        })

        print(f"{arch}: Técnica={nota_tec}  Adm={nota_adm}  ICG={icg}")

    # Guardamos archivo final
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "archivo",
            "nota_tecnica_pct",
            "nota_administrativa_pct",
            "ICG_pct",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in resultados:
            writer.writerow(row)

    print(f"\nArchivo generado: {OUT_CSV}")


if __name__ == "__main__":
    main()

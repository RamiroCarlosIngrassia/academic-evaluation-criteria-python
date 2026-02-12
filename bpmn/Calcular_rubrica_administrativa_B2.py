import os
import csv

# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = os.getenv("RUBRICA_BASE_DIR", "./Rubrica_Tecnica")
INV_DIR = os.path.join(BASE_DIR, "Inventarios")

# Nombre del inventario canónico (no se usa directamente, pero lo dejamos por consistencia)
CANON_FILENAME = "Inventario_Tema_B2.txt"

# Archivo de salida con la evaluación administrativa
OUT_CSV = os.path.join(BASE_DIR, "Evaluacion_BPMN_Administrativa_B2.csv")


# ============================================================
# LECTURA DE INVENTARIOS
# ============================================================

def cargar_inventario_filas(path_txt):
    """
    Lee un archivo de inventario con formato:
    tipo;subtipo;nombre_visible;cantidad

    Devuelve una lista de filas:
    [
        {"tipo": ..., "subtipo": ..., "nombre": ..., "cantidad": int},
        ...
    ]
    """
    filas = []
    with open(path_txt, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)  # salteamos encabezado

        for row in reader:
            if len(row) < 4:
                continue
            tipo, subtipo, nombre, cantidad_str = row
            cantidad_str = cantidad_str.strip()
            if not cantidad_str:
                continue
            try:
                cantidad = int(cantidad_str)
            except ValueError:
                continue

            filas.append({
                "tipo": tipo.strip(),
                "subtipo": subtipo.strip(),
                "nombre": nombre.strip(),
                "cantidad": cantidad
            })
    return filas


# ============================================================
# FUNCIONES DE PUNTAJE – RÚBRICA ADMINISTRATIVA (Tema B)
# ============================================================

def puntaje_arca(filas):
    """
    1) VALIDACIÓN CONTRA ARCA – 40%

    100% → aparece al menos una tarea que contenga “ARCA” Y algún verbo de validación/comparación.
    70%  → aparece interacción con ARCA pero no se distingue si compara/valida (ej. Enviar RE a ARCA).
    40%  → aparece “RE” pero NO ARCA explícito (ej. “Generar RE”).
    0%   → no hay referencia alguna a ARCA ni RE.
    """

    nombres_actividad = []
    for fila in filas:
        if fila["tipo"] == "Actividad":
            nombres_actividad.append(fila["nombre"])

    nombres_lower = [n.lower() for n in nombres_actividad]

    # ARCA + verbos de validación
    verbos_validacion = ["compar", "verific", "consult"]
    has_arca_validacion = False
    has_arca = False

    for n in nombres_lower:
        if "arca" in n:
            has_arca = True
            if any(v in n for v in verbos_validacion):
                has_arca_validacion = True

    # "RE" sin ARCA (ej. "Generar RE")
    has_re_sin_arca = False
    for n in nombres_lower:
        if "arca" in n:
            continue
        padded = " " + n + " "
        if " re " in padded:
            has_re_sin_arca = True
            break

    if has_arca_validacion:
        return 100.0
    if has_arca:
        return 70.0
    if has_re_sin_arca:
        return 40.0
    return 0.0


def puntaje_control_fisico(filas):
    """
    2) CONTROL DE EXISTENCIA FÍSICA – 25%

    100% → existe TaskManual/TaskUser y su nombre menciona lote/existencia/reubicación/movimiento/control físico.
    70%  → existe TaskManual/TaskUser, pero el nombre no es claro.
    40%  → hay nombres como “chofer/camión” que sugieren intervención física.
    0%   → ninguna tarea manual/usuario.
    """

    manual_user = [fila for fila in filas
                   if fila["tipo"] == "Actividad"
                   and fila["subtipo"] in ("TaskManual", "TaskUser")]

    if not manual_user:
        return 0.0

    nombres_lower = [f["nombre"].lower() for f in manual_user]

    # Palabras fuertes para 100%
    claves_fuertes = [
        "existenc",   # existencia
        "lote",
        "reubic",     # reubicar/reubicación
        "movim",      # movimiento/movimientos
        "control físico",
        "control fisico"
    ]
    # Palabras para 40%
    claves_chofer = ["chofer", "camion", "camión"]

    for n in nombres_lower:
        if any(c in n for c in claves_fuertes):
            return 100.0

    for n in nombres_lower:
        if any(c in n for c in claves_chofer):
            return 40.0

    # Si hay manual/user pero sin palabras claras
    return 70.0


def puntaje_control_automatico(filas):
    """
    3) CONTROL AUTOMÁTICO – RFID – 25%

    100% → tiene 2 Signal y al menos 1 Inclusiva.
    70%  → tiene solo los 2 Signal o solo la Inclusiva.
    40%  → tiene 1 Signal o una Inclusiva aislada.
    0%   → no modela señales ni inclusivas.
    """

    num_signal = 0
    num_inclusive = 0

    for fila in filas:
        if fila["tipo"] == "Evento" and fila["subtipo"].startswith("IntermediateEvent/Signal"):
            num_signal += fila["cantidad"]
        elif fila["tipo"] == "Compuerta" and fila["subtipo"] == "Inclusive":
            num_inclusive += fila["cantidad"]

    if num_signal >= 2 and num_inclusive >= 1:
        return 100.0
    if (num_signal >= 2 and num_inclusive == 0) or (num_inclusive >= 1 and num_signal == 0):
        return 70.0
    if num_signal == 1 or num_inclusive == 1:
        return 40.0
    return 0.0


def puntaje_sgbd(filas):
    """
    4) ROL DEL SGBD (estado documental) – 10%

    100% → aparece explícitamente “Cambiar Estado Remito” y al menos 1 Data Store.
    70%  → aparece solo “Cambiar Estado Remito” sin data stores.
    40%  → aparece “Cambiar Estado Factura”.
    0%   → no aparece ningún indicio de estado ni persistencia.
    """

    nombres_actividad = []
    total_datastores = 0

    for fila in filas:
        if fila["tipo"] == "Actividad":
            nombres_actividad.append(fila["nombre"])
        elif fila["tipo"] == "DataStore":
            total_datastores += fila["cantidad"]

    nombres_lower = [n.lower() for n in nombres_actividad]

    has_cambiar_estado_remito = any("cambiar estado" in n and "remito" in n
                                    for n in nombres_lower)
    has_cambiar_estado_factura = any("cambiar estado" in n and "factura" in n
                                     for n in nombres_lower)

    if has_cambiar_estado_remito and total_datastores > 0:
        return 100.0
    if has_cambiar_estado_remito:
        return 70.0
    if has_cambiar_estado_factura:
        return 40.0
    return 0.0


def puntaje_administrativo_total(p_arca, p_fisico, p_auto, p_sgbd):
    """
    Puntaje Administrativo =
        0.40 × Validación ARCA +
        0.25 × Control físico +
        0.25 × Control automático +
        0.10 × Rol SGBD
    """
    return round(
        0.40 * p_arca +
        0.25 * p_fisico +
        0.25 * p_auto +
        0.10 * p_sgbd,
        2
    )


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

def main():
    if not os.path.isdir(INV_DIR):
        print(f"No existe la carpeta de inventarios: {INV_DIR}")
        return

    resultados = []

    for filename in os.listdir(INV_DIR):
        if not filename.lower().endswith(".txt"):
            continue
        if filename == CANON_FILENAME:
            continue  # saltamos el canónico

        path = os.path.join(INV_DIR, filename)
        filas = cargar_inventario_filas(path)

        p_arca = puntaje_arca(filas)
        p_fisico = puntaje_control_fisico(filas)
        p_auto = puntaje_control_automatico(filas)
        p_sgbd = puntaje_sgbd(filas)
        p_total = puntaje_administrativo_total(p_arca, p_fisico, p_auto, p_sgbd)

        resultados.append({
            "archivo": filename,
            "arca_pct": p_arca,
            "control_fisico_pct": p_fisico,
            "control_automatico_pct": p_auto,
            "sgbd_pct": p_sgbd,
            "puntaje_administrativo_pct": p_total,
        })

        print(f"[OK] {filename} -> Administrativo = {p_total}%")

    if not resultados:
        print("No se encontraron inventarios de alumnos para procesar.")
        return

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "archivo",
                "arca_pct",
                "control_fisico_pct",
                "control_automatico_pct",
                "sgbd_pct",
                "puntaje_administrativo_pct",
            ]
        )
        writer.writeheader()
        for row in resultados:
            writer.writerow(row)

    print(f"\nEvaluación administrativa guardada en: {OUT_CSV}")


if __name__ == "__main__":
    main()

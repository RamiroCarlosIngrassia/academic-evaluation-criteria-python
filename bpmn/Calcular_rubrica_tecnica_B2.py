import os
import csv
from collections import defaultdict

# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = os.getenv("RUBRICA_BASE_DIR", "./Rubrica_Tecnica")
INV_DIR = os.path.join(BASE_DIR, "Inventarios")

# Nombre EXACTO del inventario canónico dentro de INV_DIR
CANON_FILENAME = "Inventario_Tema_B2.txt"

# Archivo de salida con la evaluación técnica
OUT_CSV = os.path.join(BASE_DIR, "Evaluacion_BPMN_Tecnica_B2.csv")


# ============================================================
# LECTURA DE INVENTARIOS
# ============================================================

def cargar_inventario(path_txt):
    """
    Lee un archivo de inventario con formato:
    tipo;subtipo;nombre_visible;cantidad

    Devuelve un diccionario:
    {
        "Evento":    {"StartEvent/Conditional": 1, "IntermediateEvent/Signal": 2, ...},
        "Compuerta": {"Exclusive": 3, "Inclusive": 2, "Parallel": 2},
        "Actividad": {"TaskService": 10, "TaskUser": 8, "TaskManual": 1, ...},
        "DataStore": {"DataStore": 4}
    }
    """
    inv = defaultdict(lambda: defaultdict(int))

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

            tipo = tipo.strip()
            subtipo = subtipo.strip()
            inv[tipo][subtipo] += cantidad

    return inv


# ============================================================
# FUNCIONES DE PUNTAJE (TEMA B2)
# ============================================================

def puntaje_eventos(inv_est, inv_canon):
    """
    Calcula el % de similitud para EVENTOS según las reglas del Tema B2.

    Regla clave B2:
    - El inicio esperado es StartEvent/Conditional.
    - Se mantienen las reglas de señales RFID y fines del esquema original.
    """

    eventos_est = inv_est.get("Evento", {})
    eventos_can = inv_canon.get("Evento", {})

    # --- Inicio ---
    total_start = sum(c for s, c in eventos_est.items() if s.startswith("StartEvent"))
    has_start_parallel = any(s.startswith("StartEvent/Parallel") for s in eventos_est.keys())
    has_start_cond = eventos_est.get("StartEvent/Conditional", 0) > 0

    if total_start == 0:
        score_inicio = 0  # Sin evento de inicio
    elif has_start_parallel:
        score_inicio = 100  # Inicio múltiple paralelo
    elif has_start_cond:
        score_inicio = 70   # Inicio condicional (esperado en B2)
    else:
        score_inicio = 50   # Otros inicios simples

    # --- Intermedios (señales RFID) ---
    señales_est = eventos_est.get("IntermediateEvent/Signal", 0)

    if señales_est == 0:
        score_inter = 0         # sin señales
    elif señales_est == 1:
        score_inter = 50        # solo 1 señal
    elif señales_est == 2:
        score_inter = 100       # mínimo 2 señales
    else:  # > 2
        score_inter = 70        # más de 2 señales

    # --- Fines ---
    fines_est = sum(c for s, c in eventos_est.items() if s.startswith("EndEvent"))
    fines_can = sum(c for s, c in eventos_can.items() if s.startswith("EndEvent"))

    if fines_est == 0:
        score_fin = 0           # sin evento de fin
    elif fines_est <= max(1, fines_can):
        score_fin = 60          # fines simples, cantidad razonable
    else:
        score_fin = 70          # más de lo necesario, pero aceptables

    # Promedio simple de los tres componentes
    score_total = round((score_inicio + score_inter + score_fin) / 3.0, 2)
    return score_total


def puntaje_compuertas(inv_est):
    """
    Calcula el % de similitud para COMPUERTAS según Tema B2.

    Cambios B2 (respecto B1):
    - Estructura correcta: Exclusive + Parallel + Inclusive (mínimo 2 de cada tipo).
    """

    gw = inv_est.get("Compuerta", {})
    excl = gw.get("Exclusive", 0)
    incl = gw.get("Inclusive", 0)
    par = gw.get("Parallel", 0)
    total = sum(gw.values())

    if total == 0:
        return 0.0  # sin compuertas

    # Estructura ideal: al menos 2 exclusivas, 2 inclusivas y 2 paralelas
    if excl >= 2 and incl >= 2 and par >= 2:
        return 100.0

    # Estructura relativamente buena: hay de los tres tipos, pero no llegan a 2 cada uno
    if excl >= 1 and incl >= 1 and par >= 1:
        return 70.0

    # Paralelas donde debía haber inclusivas (hay paralelas pero casi nada de inclusivas)
    if par > 0 and incl == 0:
        return 20.0

    # Algunas compuertas, pero mal proporcionadas o incompletas
    if total < 2:
        return 20.0

    return 40.0  # caso intermedio genérico


def puntaje_tareas(inv_est):
    """
    Calcula el % de similitud para TAREAS:

    - Importa la proporción entre:
        * TaskService (automatización)
        * TaskUser (verificación)
        * TaskManual (movimientos físicos)
    """

    tareas = inv_est.get("Actividad", {})
    total = sum(tareas.values())

    if total == 0:
        return 0.0

    service = tareas.get("TaskService", 0)
    user = tareas.get("TaskUser", 0)
    manual = tareas.get("TaskManual", 0)

    categorias_no_cero = sum(1 for x in (service, user, manual) if x > 0)

    # Diversidad mínima de tipos
    if categorias_no_cero == 3:
        base = 100.0
    elif categorias_no_cero == 2:
        base = 60.0
    elif categorias_no_cero == 1:
        base = 20.0
    else:
        base = 0.0

    # Penalización si hay muy pocas o demasiadas tareas
    # (la canónica tiene ~22 tareas)
    if total < 10:
        base *= 0.7
    elif total > 40:
        base *= 0.7

    return round(base, 2)


def puntaje_datastores(inv_est):
    """
    Calcula el % de similitud para DATA STORES:

    - 2 a 4 depósitos → 100%
    - 0 o 1 → 20%
    - 6 o más → 40%
    - Casos intermedios → 70%
    """

    ds = inv_est.get("DataStore", {})
    total = sum(ds.values())

    if 2 <= total <= 4:
        return 100.0
    if total == 0 or total == 1:
        return 20.0
    if total >= 6:
        return 40.0

    # Caso intermedio, ej. 5 depósitos
    return 70.0


def puntaje_tecnico_total(score_ev, score_gw, score_ta, score_ds):
    """
    Fórmula general de la rúbrica técnica:

    Puntaje Técnico =
        0.20 × Eventos +
        0.45 × Compuertas +
        0.25 × Tareas +
        0.10 × Data Stores
    """
    return round(
        0.20 * score_ev +
        0.45 * score_gw +
        0.25 * score_ta +
        0.10 * score_ds,
        2
    )


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

def main():
    # Cargar inventario canónico
    canon_path = os.path.join(INV_DIR, CANON_FILENAME)
    if not os.path.isfile(canon_path):
        print(f"No se encontró el inventario canónico: {canon_path}")
        return

    inv_canon = cargar_inventario(canon_path)

    resultados = []

    for filename in os.listdir(INV_DIR):
        if not filename.lower().endswith(".txt"):
            continue
        if filename == CANON_FILENAME:
            continue  # salteamos el canónico

        path = os.path.join(INV_DIR, filename)
        inv_est = cargar_inventario(path)

        score_ev = puntaje_eventos(inv_est, inv_canon)
        score_gw = puntaje_compuertas(inv_est)
        score_ta = puntaje_tareas(inv_est)
        score_ds = puntaje_datastores(inv_est)
        score_total = puntaje_tecnico_total(score_ev, score_gw, score_ds, score_ta)  # OJO al orden si lo cambiás

        resultados.append({
            "archivo": filename,
            "eventos_pct": score_ev,
            "compuertas_pct": score_gw,
            "tareas_pct": score_ta,
            "data_stores_pct": score_ds,
            "puntaje_tecnico_pct": score_total,
        })

        print(f"[OK] {filename} -> Técnico = {score_total}%")

    # Escribir CSV de salida
    if resultados:
        with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "archivo",
                    "eventos_pct",
                    "compuertas_pct",
                    "tareas_pct",
                    "data_stores_pct",
                    "puntaje_tecnico_pct",
                ]
            )
            writer.writeheader()
            for row in resultados:
                writer.writerow(row)

        print(f"\nEvaluación técnica guardada en: {OUT_CSV}")
    else:
        print("No se encontraron inventarios de alumnos para procesar.")


if __name__ == "__main__":
    main()

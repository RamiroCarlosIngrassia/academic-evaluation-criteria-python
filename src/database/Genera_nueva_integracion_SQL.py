import os
import re
import pandas as pd

# === RUTAS (ajustar si es necesario) ===
# RUTAS (ANONIMIZADAS)
RUTA_DEVOLUCIONES_BD = os.getenv("RUTA_DEVOLUCIONES_BD", "./Devoluciones_BD")
RUTA_SALIDA = os.getenv("RUTA_SALIDA", "./Devolucion_Integral_2")
RUTA_EXCEL_SQL = os.getenv("RUTA_EXCEL_SQL", "./Resultados_SQL_TemaB.xlsx")

# Crear carpeta de salida si no existe
os.makedirs(RUTA_SALIDA, exist_ok=True)

# === 1) Leer Excel con resultados SQL ===
df = pd.read_excel(RUTA_EXCEL_SQL)

# Normalizar apellidos como clave
df["Apellido_Inferido_norm"] = df["Apellido_Inferido"].astype(str).str.strip().str.lower()

# Pasar a diccionario para acceso rápido
sql_por_apellido = {}
for _, row in df.iterrows():
    apellido_norm = row["Apellido_Inferido_norm"]
    sql_por_apellido[apellido_norm] = {
        "Sim_Consigna1": row["Sim_Consigna1"],
        "Sim_Consigna2": row["Sim_Consigna2"],
        "Sim_Consigna3": row["Sim_Consigna3"],
        "Promedio_Sim_SQL": row["Promedio_Sim_SQL"],
    }

# === Función para extraer ICG del texto ===
def extraer_icg(texto: str) -> float | None:
    """
    Busca números con % y devuelve el ÚLTIMO como ICG.
    Soporta formatos:
    - 14,26 %
    - 31,4 %
    - ... = 56,84 % → ...
    """
    matches = re.findall(r"(\d+(?:,\d+)?)\s*%", texto)
    if not matches:
        return None
    icg_str = matches[-1]  # último porcentaje encontrado
    return float(icg_str.replace(",", "."))

# === 2) Recorrer .md de Devoluciones_BD ===
for nombre in os.listdir(RUTA_DEVOLUCIONES_BD):
    if not nombre.lower().endswith(".md"):
        continue
    if "devolucion_bd_" not in nombre.lower():
        continue

    ruta_md = os.path.join(RUTA_DEVOLUCIONES_BD, nombre)

    # Extraer apellido del nombre de archivo
    # Formato esperado: Devolucion_BD_Apellido.md
    base = os.path.splitext(nombre)[0]
    apellido = base.split("Devolucion_BD_")[-1]

    apellido_norm = apellido.strip().lower()

    if apellido_norm not in sql_por_apellido:
        print(f"[AVISO] No hay datos SQL para: {apellido} (archivo {nombre})")
        continue

    # Leer contenido del .md
    with open(ruta_md, "r", encoding="utf-8") as f:
        contenido = f.read()

    # 4) Extraer ICG del texto
    icg = extraer_icg(contenido)
    if icg is None:
        print(f"[AVISO] No se pudo encontrar ICG en el archivo: {nombre}")
        continue

    # 2) Obtener valores SQL desde el Excel
    datos_sql = sql_por_apellido[apellido_norm]
    sim1 = datos_sql["Sim_Consigna1"]
    sim2 = datos_sql["Sim_Consigna2"]
    sim3 = datos_sql["Sim_Consigna3"]
    prom_sql = datos_sql["Promedio_Sim_SQL"]

    # 5) Calcular nueva nota (promedio entre ICG y Promedio_Sim_SQL)
    nota_1era = (icg + prom_sql) / 2.0

    # Formatear con coma como separador decimal
    def f(x):
        return f"{x:.2f}".replace(".", ",")

    bloque_sql = (
        "\n\n"
        "------------------------------------------------------------\n"
        "RESULTADOS DE SQL (integrados automáticamente)\n\n"
        f"Sim_Consigna1: {f(sim1)} %\n"
        f"Sim_Consigna2: {f(sim2)} %\n"
        f"Sim_Consigna3: {f(sim3)} %\n"
        f"Promedio_Sim_SQL: {f(prom_sql)} %\n\n"
        f"Nota_1era_Etapa_de_la_Instancia_Evaluativa: {f(nota_1era)} %\n"
        "------------------------------------------------------------\n"
    )

    # 3) Guardar en nuevo archivo .txt: [Apellido]_integrado
    nombre_salida = f"{apellido}_integrado.txt"
    ruta_salida = os.path.join(RUTA_SALIDA, nombre_salida)

    with open(ruta_salida, "w", encoding="utf-8") as f_out:
        f_out.write(contenido)
        f_out.write(bloque_sql)

    print(f"[OK] Generado: {ruta_salida}")

print("Proceso terminado.")

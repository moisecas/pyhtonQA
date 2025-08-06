#!/usr/bin/env python3
# compare_two_excels_with_html_report.py

import os
import re
import pandas as pd
from datetime import datetime

# ————— Configuración —————
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\PlayerBalanceReport-VERONICARIQUELME.xlsx"
EXCEL_UI_PATH     = r"C:\Users\moise\Downloads\uiundiabalancejugadorpro.xlsx"

# Columnas exactas compartidas por ambos archivos
COLUMNS = [
    "Fecha",
    "Proveedor",
    "Tipo",
    "Monto",
    "Balance",
    "Jugada",
    "Ronda",
    "Observaciones",
]

# Lo mismo pero en minúsculas para mapeo interno y búsqueda de encabezados
COLUMNS_LOWER = [c.lower() for c in COLUMNS]

HTML_REPORT_PATH = "diferencias_comparacion.html"


# ————— Funciones de normalización —————

def normalize_fecha(valor) -> str:
    """
    - Si 'valor' es pd.Timestamp o datetime: 
        • Si incluye hora != 00:00:00, devuelve "YYYY-MM-DD HH:MM:SS".
        • Si solo fecha, devuelve "YYYY-MM-DD".
    - Si es int/float, lo convierte a str.
    - Si es str, intenta parsear formatos con hora primero, luego sin hora.
    - Si no encaja, devuelve v.strip().
    """
    if isinstance(valor, (pd.Timestamp, datetime)):
        if valor.hour != 0 or valor.minute != 0 or valor.second != 0:
            return valor.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return valor.strftime("%Y-%m-%d")

    if isinstance(valor, (int, float)):
        return str(valor)

    v = str(valor).strip()
    if not v:
        return ""

    # Intentar formatos con hora
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(v, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    # Intentar formatos solo fecha
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(v, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            pass

    return v


def normalize_numero(valor) -> float:
    """
    - Si 'valor' es int/float, lo convierte a float(int(valor)) para truncar.
    - Si es str, elimina sufijos de moneda y espacios, detecta
      puntos de miles y comas decimales, convierte a float y trunca
      parte decimal.
    - Si no puede convertir, retorna NaN.
    """
    # 1) Si ya es int/float
    if isinstance(valor, (int, float)):
        try:
            return float(int(valor))
        except:
            return float("nan")

    texto = str(valor).strip()
    if not texto:
        return float("nan")

    # 2) Quitar posible sufijo de moneda ("CLP") y espacios (incluyendo no-break)
    texto = re.sub(r"\s*CLP\s*$", "", texto)
    texto = texto.replace(" ", "").replace("\u00A0", "")

    # 3) Capturar signo al inicio
    sign = 1
    if texto.startswith("-"):
        sign = -1
        texto = texto[1:]
    elif texto.startswith("+"):
        texto = texto[1:]

    # 4) Patrón de miles con posible coma decimal: "1.234.567" o "1.234.567,89"
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", texto):
        if "," in texto:
            partes = texto.split(",")
            entero = partes[0].replace(".", "")
            # Truncamos decimales
            try:
                return float(sign * int(entero))
            except:
                return float("nan")
        else:
            solo_digitos = texto.replace(".", "")
            try:
                return float(sign * int(solo_digitos))
            except:
                return float("nan")

    # 5) Si no encaja en patrón anterior, manejamos coma/punto decimal simple
    s = re.sub(r"[^\d,.\-]", "", texto)
    if "," in s and "." in s:
        # Determinar si coma es decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        partes = s.split(".")
        if len(partes) > 2:
            num_entero = "".join(partes[:-1])
            s = num_entero + "." + partes[-1]
        # si len(partes)==2 queda entero.decimal

    try:
        val = float(s)
        return float(sign * int(val))
    except:
        return float("nan")


def normalize_texto(valor: str) -> str:
    """
    Trim + pasar a minúsculas.
    """
    return str(valor).strip().lower()


# Mapeo de funciones de normalización por nombre de columna en minúsculas
NORMALIZERS_LOWER = {
    "fecha": normalize_fecha,
    "proveedor": normalize_texto,
    "tipo": normalize_texto,
    "monto": normalize_numero,
    "balance": normalize_numero,
    "jugada": normalize_numero,
    "ronda": normalize_numero,
    "observaciones": normalize_texto,
}


# ————— Funciones para cargar DataFrame desde Excel —————

def load_excel_dynamic(excel_path: str, columns_expected_lower: list) -> pd.DataFrame:
    """
    Lee un Excel sin header fijo, busca la fila con todos los encabezados
    en columns_expected_lower (en minúsculas) y la usa como header. Luego,
    filtra únicamente esas columnas y las renombra a minúsculas.
    """
    if not os.path.exists(excel_path):
        print(f"❌ No existe el archivo: {excel_path}")
        return pd.DataFrame()

    # 1) Leer sin header para ubicar fila de encabezado (todo como texto)
    df_raw = pd.read_excel(excel_path, header=None, dtype=str)
    df_raw = df_raw.fillna("").astype(str).applymap(lambda x: x.strip())

    # 2) Buscar la fila que contenga todos los encabezados esperados (en minúsculas)
    header_idx = None
    for idx, row in df_raw.iterrows():
        valores_lower = [celda.strip().lower() for celda in row.tolist()]
        if all(col in valores_lower for col in columns_expected_lower):
            header_idx = idx
            break

    if header_idx is None:
        print(f"❌ No encontré fila de encabezado en '{os.path.basename(excel_path)}' que contenga {columns_expected_lower}")
        return pd.DataFrame()

    # 3) Volver a leer usando header_idx como header, sin forzar dtype
    df = pd.read_excel(excel_path, header=header_idx)
    df.columns = [str(col).strip() for col in df.columns]

    # 4) Mapear cada encabezado real (original) a su versión en minúsculas
    cols_lower_actuales = [str(col).strip().lower() for col in df.columns]
    mapa_real = {lower: real for real, lower in zip(df.columns, cols_lower_actuales)}

    # 5) Verificar que todas las columnas esperadas existan
    missing = [col for col in columns_expected_lower if col not in mapa_real]
    if missing:
        print(f"❌ En '{os.path.basename(excel_path)}' faltan columnas: {missing}")
        return pd.DataFrame()

    # 6) Seleccionar columnas en el orden de columns_expected_lower
    columnas_reales_en_orden = [mapa_real[col_low] for col_low in columns_expected_lower]
    df_filtrado = df[columnas_reales_en_orden].copy().fillna("")

    # 7) Renombrar columnas a minúsculas para coincidir con NORMALIZERS_LOWER
    df_filtrado.columns = columns_expected_lower
    return df_filtrado.reset_index(drop=True)


# ————— Comparación con normalización —————

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, columns_lower: list):
    """
    Compara df1 vs df2 en las mismas columnas (ya en minúsculas). Aplica
    normalización (texto limpio / número truncado) a cada celda, y retorna
    una lista de diferencias (fila, columna_lower, raw_exportado, raw_ui) y los
    conteos de filas de cada DataFrame.
    """
    n1 = len(df1)
    n2 = len(df2)
    diffs = []
    min_filas = min(n1, n2)

    for idx in range(min_filas):
        for col_low in columns_lower:
            raw1 = df1.at[idx, col_low]
            raw2 = df2.at[idx, col_low]
            norm_fn = NORMALIZERS_LOWER.get(col_low, lambda x: x.strip())

            val1 = norm_fn(raw1)
            val2 = norm_fn(raw2)

            # 1) Si ambos valores normalizados son float, compararlos numéricamente:
            if isinstance(val1, float) and isinstance(val2, float):
                if (pd.isna(val1) and pd.isna(val2)) or abs(val1 - val2) < 1e-6:
                    continue
                else:
                    diffs.append((idx + 1, col_low, raw1, raw2))
            else:
                # 2) Si alguno no es float, comparar como cadenas limpias:
                if str(val1) != str(val2):
                    diffs.append((idx + 1, col_low, raw1, raw2))

    return diffs, n1, n2


# ————— Generador de informes HTML —————

def generate_html_report(diffs: list, n_export: int, n_ui: int, columns_lower: list, output_path: str):
    """
    Genera un HTML que muestra las diferencias. Para 'Monto' y 'Balance',
    imprime el valor truncado (entero) en lugar de raw; para los demás campos,
    muestra el raw normalizado (texto/fecha).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_diffs = len(diffs)

    def to_title(col_low: str) -> str:
        return " ".join(palabra.capitalize() for palabra in col_low.split())

    html_rows = ""
    for fila, col_low, raw1, raw2 in diffs:
        if col_low in ("monto", "balance"):
            # Truncamos y mostramos como entero
            trunc1 = normalize_numero(raw1)
            trunc2 = normalize_numero(raw2)
            disp1 = str(int(trunc1)) if not pd.isna(trunc1) else ""
            disp2 = str(int(trunc2)) if not pd.isna(trunc2) else ""
        else:
            # Texto o fecha: mostrar el raw normalizado
            norm_fn = NORMALIZERS_LOWER.get(col_low, lambda x: x.strip())
            disp1 = norm_fn(raw1)
            disp2 = norm_fn(raw2)

        html_rows += f"""
      <tr>
        <td style="text-align:center">{fila}</td>
        <td>{to_title(col_low)}</td>
        <td>{disp1}</td>
        <td>{disp2}</td>
      </tr>"""

    if total_diffs == 0:
        contenido_diffs = """
      <tr>
        <td colspan="4" style="text-align:center">No se encontraron diferencias.</td>
      </tr>"""
    else:
        contenido_diffs = html_rows

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de Comparación de Excel</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; }}
    th {{ background: #f4f4f4; }}
    h1 {{ margin-bottom: 0; }}
    .summary {{ margin-top: 10px; }}
    .no-diffs {{ color: green; }}
    .has-diffs {{ color: red; }}
  </style>
</head>
<body>
  <h1>Reporte de Comparación de Excel</h1>
  <p>Fecha de generación: {timestamp}</p>
  <div class="summary">
    <p><strong>Filas en Excel exportado:</strong> {n_export}</p>
    <p><strong>Filas en Excel UI manual:</strong> {n_ui}</p>
    <p><strong>Total diferencias encontradas:</strong> 
      <span class="{'' if total_diffs else 'no-diffs'}{'has-diffs' if total_diffs else ''}">{total_diffs}</span>
    </p>
  </div>
  <table>
    <thead>
      <tr>
        <th>Fila</th>
        <th>Columna</th>
        <th>Valor Excel Exportado</th>
        <th>Valor Excel UI</th>
      </tr>
    </thead>
    <tbody>
    {contenido_diffs}
    </tbody>
  </table>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Reporte HTML generado: {output_path}")


# ————— Flujo principal —————

def main():
    # 1) Cargar Excel exportado
    print("Cargando Excel1 (exportado)…")
    df_export = load_excel_dynamic(EXCEL_EXPORT_PATH, COLUMNS_LOWER)
    if df_export.empty:
        print("❌ No se pudo cargar Excel1. Abortando.")
        return
    print(f"  → {len(df_export)} filas cargadas de: {EXCEL_EXPORT_PATH}")

    # 2) Cargar Excel UI manual
    print("\nCargando Excel2 (UI manual)…")
    df_ui = load_excel_dynamic(EXCEL_UI_PATH, COLUMNS_LOWER)
    if df_ui.empty:
        print("❌ No se pudo cargar Excel2. Abortando.")
        return
    print(f"  → {len(df_ui)} filas cargadas de: {EXCEL_UI_PATH}")

    # 3) Comparar y obtener diferencias
    print("\nComparando ambos DataFrames…")
    diffs, n_export, n_ui = compare_dataframes(df_export, df_ui, COLUMNS_LOWER)
    print(f"  → Total diferencias encontradas: {len(diffs)}")

    # 4) Generar reporte HTML
    generate_html_report(diffs, n_export, n_ui, COLUMNS_LOWER, HTML_REPORT_PATH)


if __name__ == "__main__":
    main()

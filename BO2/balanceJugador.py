#!/usr/bin/env python3
# compare_two_excels_with_html_report.py

import os
import re
import pandas as pd
from datetime import datetime

# ————— Configuración —————
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\PlayerBalanceReport-ALBIVERDEPARCERITO1866.xlsx"
EXCEL_UI_PATH     = r"C:\Users\moise\Downloads\balancejugadormanual.xlsx"

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

HTML_REPORT_PATH = "diferencias_comparacion.html"

# ————— Funciones de normalización —————

def normalize_fecha(valor: str) -> str:
    """
    Intenta parsear la fecha en formatos comunes y devuelve "YYYY-MM-DD".
    Si no logra parsear, retorna texto stripped.
    """
    v = str(valor).strip()
    if not v:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(v, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            pass
    try:
        ts = pd.to_datetime(v, dayfirst=True, errors="coerce")
        if not pd.isna(ts):
            return ts.strftime("%Y-%m-%d")
    except:
        pass
    return v


def normalize_numero(valor: str) -> float:
    """
    Elimina símbolos no numéricos, detecta separadores de miles y decimales,
    retorna float. Si no puede convertir, retorna NaN.
    """
    v = str(valor).strip()
    if not v:
        return float("nan")
    s = re.sub(r"[^\d,.\-]", "", v)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return float("nan")


def normalize_texto(valor: str) -> str:
    """
    Trim y pasar a minúsculas para comparar texto.
    """
    return str(valor).strip().lower()


NORMALIZERS = {
    "Fecha": normalize_fecha,
    "Proveedor": normalize_texto,
    "Tipo": normalize_texto,
    "Monto": normalize_numero,
    "Balance": normalize_numero,
    "Jugada": normalize_numero,
    "Ronda": normalize_numero,
    "Observaciones": normalize_texto,
}


# ————— Funciones para cargar DataFrame desde Excel —————

def load_excel_dynamic(excel_path: str, columns_expected: list) -> pd.DataFrame:
    """
    Lee un archivo Excel sin encabezado fijo. Busca la fila donde aparezcan
    todas las columnas_expected y la utiliza como header.
    Luego retorna un DataFrame con solo esas columnas en el orden deseado.
    """
    if not os.path.exists(excel_path):
        print(f"❌ No existe el archivo: {excel_path}")
        return pd.DataFrame()

    df_raw = pd.read_excel(excel_path, header=None, dtype=str)
    df_raw = df_raw.fillna("").astype(str).applymap(lambda x: x.strip())

    header_idx = None
    for idx, row in df_raw.iterrows():
        valores_row = [cell.strip() for cell in row.tolist()]
        if all(col in valores_row for col in columns_expected):
            header_idx = idx
            break

    if header_idx is None:
        print(f"❌ No encontré fila de encabezado en {excel_path} que contenga todas las columnas: {columns_expected}")
        return pd.DataFrame()

    df = pd.read_excel(excel_path, header=header_idx, dtype=str)
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in columns_expected if col not in df.columns]
    if missing:
        print(f"❌ Tras asignar encabezados en {excel_path}, faltan columnas: {missing}")
        return pd.DataFrame()

    df = df[columns_expected].copy().fillna("").astype(str).applymap(lambda x: x.strip())
    return df.reset_index(drop=True)


# ————— Comparación con normalización —————

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, columns: list):
    """
    Compara df1 vs df2 en las mismas columnas y filas en orden.
    Aplica normalización a cada valor antes de comparar.
    Retorna una lista de tuplas (fila, columna, valor1, valor2).
    """
    n1 = len(df1)
    n2 = len(df2)
    diffs = []

    min_filas = min(n1, n2)
    for idx in range(min_filas):
        for col in columns:
            raw1 = df1.at[idx, col]
            raw2 = df2.at[idx, col]

            norm_fn = NORMALIZERS.get(col, lambda x: x.strip())
            val1 = norm_fn(str(raw1))
            val2 = norm_fn(str(raw2))

            if isinstance(val1, float) and isinstance(val2, float):
                if pd.isna(val1) and pd.isna(val2):
                    continue
                if abs(val1 - val2) < 0.0001:
                    continue
                else:
                    diffs.append((idx + 1, col, raw1, raw2))
            else:
                if val1 != val2:
                    diffs.append((idx + 1, col, raw1, raw2))

    return diffs, n1, n2


def generate_html_report(diffs: list, n_export: int, n_ui: int, columns: list, output_path: str):
    """
    Genera un archivo HTML en 'output_path' con la lista de diferencias.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_diffs = len(diffs)

    html_rows = ""
    for fila, col, v1, v2 in diffs:
        html_rows += f"""
      <tr>
        <td style="text-align:center">{fila}</td>
        <td>{col}</td>
        <td>{v1}</td>
        <td>{v2}</td>
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
    p {{ margin-top: 4px; margin-bottom: 4px; }}
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
    <p><strong>Total diferencias encontradas:</strong> <span class="{'' if total_diffs else 'no-diffs'}{'has-diffs' if total_diffs else ''}">{total_diffs}</span></p>
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
    # 1) Cargar ambos DataFrames
    print("Cargando Excel1 (exportado)...")
    df_export = load_excel_dynamic(EXCEL_EXPORT_PATH, COLUMNS)
    if df_export.empty:
        print("❌ No se pudo cargar Excel1. Abortando.")
        return
    print(f"  → {len(df_export)} filas cargadas de: {EXCEL_EXPORT_PATH}")

    print("\nCargando Excel2 (UI manual)...")
    df_ui = load_excel_dynamic(EXCEL_UI_PATH, COLUMNS)
    if df_ui.empty:
        print("❌ No se pudo cargar Excel2. Abortando.")
        return
    print(f"  → {len(df_ui)} filas cargadas de: {EXCEL_UI_PATH}")

    # 2) Comparar y obtener diferencias
    print("\nComparando ambos DataFrames...")
    diffs, n_export, n_ui = compare_dataframes(df_export, df_ui, COLUMNS)
    print(f"  → Total diferencias encontradas: {len(diffs)}")

    # 3) Generar reporte HTML
    generate_html_report(diffs, n_export, n_ui, COLUMNS, HTML_REPORT_PATH)


if __name__ == "__main__":
    main()

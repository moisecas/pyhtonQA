#!/usr/bin/env python3
# compare_blacklist_excels.py

import os
import re
import unicodedata
import pandas as pd
from datetime import datetime

# ————— Configuración —————
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\blacklist 23-07-2025 (8).xlsx" # Archivo exportado del back-office
EXCEL_UI_PATH     = r"C:\Users\moise\Downloads\blacklistuiactivos.xlsx"     # Archivo UI contra el que comparas
HTML_REPORT_PATH  = "diferencias_blacklist.html"

# Columnas EXACTAS del reporte de lista negra,
# para mostrar en el HTML (con mayúsculas y tildes)
COLUMNS_EXPECTED = [
    "Id",
    "Tipo",
    "Valor",
    "Razón",
    "Tiempo de Bloqueo",
    "Estado",
    "Usuario",
    "Fecha",
    "Fecha de Actualización",
]

def canonical(col: str) -> str:
    """Quita tildes, espacios y pasa a minúsculas."""
    s = unicodedata.normalize("NFD", str(col))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.strip().lower()

# Columnas canónicas (sin tildes, minúsculas) para indexar DataFrames
COLUMNS_CANON = [canonical(c) for c in COLUMNS_EXPECTED]

# ————— Normalizadores —————

def normalize_fecha(v) -> str:
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%Y-%m-%d %H:%M:%S") if (v.hour or v.minute or v.second) else v.strftime("%Y-%m-%d")
    s = str(v).strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M:%S","%d-%m-%Y %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except:
            pass
    return s

def normalize_numero(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(" ", "").replace("\u00A0", "")
    t = re.sub(r"[^\d,.\-]", "", t)
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except:
        return float("nan")

def normalize_texto(v) -> str:
    return str(v).strip().lower()

NORMALIZERS = {
    "id": normalize_texto,
    "tipo": normalize_texto,
    "valor": normalize_numero,
    "razon": normalize_texto,
    "tiempo de bloqueo": normalize_numero,
    "estado": normalize_texto,
    "usuario": normalize_texto,
    "fecha": normalize_fecha,
    "fecha de actualizacion": normalize_fecha,
}

# ————— Carga dinámica con fallback —————

def load_excel(path: str, canon_cols: list) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"❌ No existe el archivo: {path}")
        return pd.DataFrame()

    raw = pd.read_excel(path, header=None, dtype=str) \
            .fillna("") \
            .astype(str) \
            .applymap(str.strip)
    header_idx = None
    for i, row in raw.iterrows():
        lows = [canonical(c) for c in row.tolist()]
        if all(c in lows for c in canon_cols):
            header_idx = i
            break

    if header_idx is None:
        print("⚠️ No encontré fila de encabezado, usando fila 0.")
        header_idx = 0

    df = pd.read_excel(path, header=header_idx)
    df.columns = [str(c).strip() for c in df.columns]
    lows = [canonical(c) for c in df.columns]
    mapping = {low: real for real, low in zip(df.columns, lows)}

    missing = [c for c in canon_cols if c not in mapping]
    if missing:
        print(f"❌ Faltan columnas en {os.path.basename(path)}: {missing}")
        return pd.DataFrame()

    reales = [mapping[c] for c in canon_cols]
    df2 = df[reales].copy().fillna("")
    df2.columns = canon_cols
    return df2.reset_index(drop=True)

# ————— Comparación —————

def compare_dfs(d1: pd.DataFrame, d2: pd.DataFrame, canon_cols: list):
    n1, n2 = len(d1), len(d2)
    diffs = []
    for i in range(min(n1, n2)):
        for canon in canon_cols:
            r1, r2 = d1.at[i, canon], d2.at[i, canon]
            v1 = NORMALIZERS[canon](r1)
            v2 = NORMALIZERS[canon](r2)
            # números
            if isinstance(v1, float) and isinstance(v2, float):
                if not ((pd.isna(v1) and pd.isna(v2)) or abs(v1 - v2) < 1e-6):
                    diffs.append((i+1, canon, r1, r2))
            else:
                if str(v1) != str(v2):
                    diffs.append((i+1, canon, r1, r2))
    return diffs, n1, n2

# ————— Generación de reporte HTML —————

def make_html(diffs, n1, n2, display_cols, out):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(diffs)
    rows = ""
    for fila, canon, v_exp, v_ui in diffs:
        # Encuentra índice de la columna para mostrar el nombre original
        idx = COLUMNS_CANON.index(canon)
        col_name = display_cols[idx]
        # Normaliza para mostrar
        val1 = NORMALIZERS[canon](v_exp)
        val2 = NORMALIZERS[canon](v_ui)
        rows += f"<tr><td align='center'>{fila}</td><td>{col_name}</td><td>{val1}</td><td>{val2}</td></tr>\n"

    if not rows:
        rows = "<tr><td colspan='4' align='center'>No hay diferencias.</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Diferencias Blacklist</title>
<style>body{{font-family:sans-serif;padding:20px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:6px}}th{{background:#eee}}</style>
</head><body>
<h1>Comparación Blacklist</h1>
<p>Generado: {now}</p>
<p><b>Filas exp:</b> {n1} — <b>Filas UI:</b> {n2} — <b>Difs:</b> 
<span style="color:{'red' if total else 'green'}">{total}</span></p>
<table>
<thead><tr><th>Fila</th><th>Columna</th><th>Exportado</th><th>UI</th></tr></thead>
<tbody>
{rows}
</tbody></table></body></html>"""

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Reporte generado:", out)

# ————— Main —————

def main():
    print("Cargando exportado…")
    df1 = load_excel(EXCEL_EXPORT_PATH, COLUMNS_CANON)
    if df1.empty:
        return

    print("Cargando UI…")
    df2 = load_excel(EXCEL_UI_PATH, COLUMNS_CANON)
    if df2.empty:
        return

    print("Comparando…")
    # Aquí pasamos las columnas canónicas
    diffs, n1, n2 = compare_dfs(df1, df2, COLUMNS_CANON)
    print(f"Diferencias encontradas: {len(diffs)}")

    # Para el HTML usamos los nombres originales
    make_html(diffs, n1, n2, COLUMNS_EXPECTED, HTML_REPORT_PATH)

if __name__ == "__main__":
    main()

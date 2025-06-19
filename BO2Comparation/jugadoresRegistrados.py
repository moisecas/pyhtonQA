#!/usr/bin/env python3
# compare_dom_report_excels.py

import os
import re
import pandas as pd
from datetime import datetime

# ————— Configuración —————
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\registered_players 18-06-2025 (4).xlsx"
EXCEL_UI_PATH     = r"C:\Users\moise\Downloads\un mes jugadores.xlsx"

# Columnas EXACTAS tal cual aparecen en los encabezados de tu Excel
COLUMNS = [
    "Fecha",
    "Id",
    "Usuario",
    "Skin",
    "Nombre",
    "Apellido",
    "Nro. Documento",
    "Correo",
    "Teléfono",
    "Ip",
    "Estado",
    "Carga",
    "Observación",
    "Afiliado",
    "Reenviar Sms"
]

# Para el código las tratamos en minúsculas
COLUMNS_LOWER = [c.strip().lower() for c in COLUMNS]

HTML_REPORT_PATH = "diferencias_dom_report.html"


# ————— Normalizadores —————

def normalize_fecha(v) -> str:
    if isinstance(v, (pd.Timestamp, datetime)):
        if v.hour or v.minute or v.second:
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    if not s:
        return ""
    for fmt in ("%d/%m/%Y %H:%M:%S","%Y-%m-%d %H:%M:%S"):
        try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except: pass
    for fmt in ("%d/%m/%Y","%Y-%m-%d"):
        try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except: pass
    return s

def normalize_numero(v) -> float:
    if isinstance(v, (int, float)):
        return float(int(v))
    t = str(v).strip()
    if not t:
        return float("nan")
    # Quitar separadores y moneda
    t = re.sub(r"[^\d,\-\.]", "", t)
    # Unificar decimal coma/punto
    if "," in t and t.count(",") == 1 and "." in t and t.find(",") > t.find("."):
        t = t.replace(".", "").replace(",", ".")
    elif "," in t and "." not in t:
        t = t.replace(",", ".")
    try:
        return float(int(float(t)))
    except:
        return float("nan")

def normalize_texto(v) -> str:
    return str(v).strip().lower()


# Mapeo columna → normalizador
NORMALIZERS = {
    "fecha": normalize_fecha,
    "id": normalize_texto,
    "usuario": normalize_texto,
    "skin": normalize_texto,
    "nombre": normalize_texto,
    "apellido": normalize_texto,
    "nro. documento": normalize_texto,
    "correo": normalize_texto,
    "teléfono": normalize_texto,
    "ip": normalize_texto,
    "estado": normalize_texto,
    "carga": normalize_numero,
    "observación": normalize_texto,
    "afiliado": normalize_texto,
    "reenviar sms": normalize_texto,
}


# ————— Carga dinámica de Excel —————

def load_excel_dynamic(path: str, cols_lower: list) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"❌ No existe: {path}")
        return pd.DataFrame()
    df_raw = pd.read_excel(path, header=None, dtype=str).fillna("").astype(str).applymap(str.strip)
    header_idx = None
    for i, row in df_raw.iterrows():
        lowers = [c.lower() for c in row.tolist()]
        if all(col in lowers for col in cols_lower):
            header_idx = i
            break
    if header_idx is None:
        print(f"⚠️ Encabezado no encontrado, usando fila 0 en {os.path.basename(path)}")
        header_idx = 0
    df = pd.read_excel(path, header=header_idx)
    df.columns = [c.strip() for c in df.columns]
    actual_lowers = [c.lower() for c in df.columns]
    mapping = {low: real for real, low in zip(df.columns, actual_lowers)}
    missing = [col for col in cols_lower if col not in mapping]
    if missing:
        print(f"❌ Faltan columnas en {os.path.basename(path)}: {missing}")
        return pd.DataFrame()
    reales = [mapping[col] for col in cols_lower]
    df2 = df[reales].copy().fillna("")
    df2.columns = cols_lower
    return df2.reset_index(drop=True)


# ————— Comparación —————

def compare_dataframes(df1, df2, cols_lower):
    n1, n2 = len(df1), len(df2)
    diffs = []
    for i in range(min(n1, n2)):
        for c in cols_lower:
            r1, r2 = df1.at[i, c], df2.at[i, c]
            fn = NORMALIZERS.get(c, normalize_texto)
            v1, v2 = fn(r1), fn(r2)
            if isinstance(v1, float) and isinstance(v2, float):
                if not ((pd.isna(v1) and pd.isna(v2)) or abs(v1 - v2) < 1e-6):
                    diffs.append((i+1, c, r1, r2))
            else:
                if str(v1) != str(v2):
                    diffs.append((i+1, c, r1, r2))
    return diffs, n1, n2


# ————— Reporte HTML —————

def generate_html_report(diffs, n1, n2, cols_lower, out):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(diffs)
    def title(c): return " ".join(w.capitalize() for w in c.split())
    rows = ""
    for f, col, r1, r2 in diffs:
        if col == "carga":
            d1 = str(int(normalize_numero(r1))) if not pd.isna(normalize_numero(r1)) else ""
            d2 = str(int(normalize_numero(r2))) if not pd.isna(normalize_numero(r2)) else ""
        else:
            d1 = str(NORMALIZERS[col](r1))
            d2 = str(NORMALIZERS[col](r2))
        rows += f"""
      <tr>
        <td align="center">{f}</td>
        <td>{title(col)}</td>
        <td>{d1}</td>
        <td>{d2}</td>
      </tr>"""
    if total == 0:
        rows = '<tr><td colspan="4" align="center">No se encontraron diferencias.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Comparación DOM Report</title>
<style>body{{font-family:sans-serif;padding:20px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px}}th{{background:#f4f4f4}}</style>
</head><body>
<h1>Comparación de Reporte DOM</h1>
<p>Generado: {t}</p>
<p><b>Filas exportado:</b> {n1} — <b>Filas UI:</b> {n2} — <b>Difs:</b> {total}</p>
<table><thead><tr><th>Fila</th><th>Columna</th><th>Exportado</th><th>UI</th></tr></thead><tbody>
{rows}
</tbody></table></body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Reporte HTML generado:", out)


# ————— Main —————

def main():
    print("Cargando exportado…")
    df1 = load_excel_dynamic(EXCEL_EXPORT_PATH, COLUMNS_LOWER)
    if df1.empty: return
    print("Cargando UI manual…")
    df2 = load_excel_dynamic(EXCEL_UI_PATH, COLUMNS_LOWER)
    if df2.empty: return
    print("Comparando…")
    diffs, n1, n2 = compare_dataframes(df1, df2, COLUMNS_LOWER)
    print(f"Diferencias encontradas: {len(diffs)}")
    generate_html_report(diffs, n1, n2, COLUMNS_LOWER, HTML_REPORT_PATH)

if __name__ == "__main__":
    main()

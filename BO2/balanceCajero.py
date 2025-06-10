#!/usr/bin/env python3
# compare_two_excels_with_html_report.py

import os
import re
import unicodedata
import pandas as pd
from datetime import datetime

# ————— Configuración —————
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\balance_skin (45).xlsx"
EXCEL_UI_PATH     = r"C:\Users\moise\Downloads\balanceSkin (1).xlsx"

# Columnas exactas del nuevo reporte, en minúsculas y sin tildes
COLUMNS_EXPECTED = [
    "fecha",
    "usuario",
    "monto",
    "balance",
    "transacción",
    "tipo de movimiento",
    "tipo de bono",
    "nro. documento",
    "cajero",
    "observaciones",
]

def canonical(col: str) -> str:
    s = unicodedata.normalize("NFD", str(col))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # quita tildes
    return s.strip().lower()

COLUMNS_CANON = [canonical(c) for c in COLUMNS_EXPECTED]
HTML_REPORT_PATH = "diferencias_comparacion.html"

# ————— Normalizadores —————

def normalize_fecha(v) -> str:
    if isinstance(v, (pd.Timestamp, datetime)):
        if v.hour or v.minute or v.second:
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M:%S","%d-%m-%Y %H:%M:%S"):
        try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except: pass
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y"):
        try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except: pass
    return s

def normalize_numero(v) -> float:
    # trunca decimales
    if isinstance(v, (int, float)):
        try: return float(int(v))
        except: return float("nan")
    t = str(v).strip()
    if not t: return float("nan")
    t = re.sub(r"\s*CLP\s*$","",t).replace(" ","").replace("\u00A0","")
    sign = -1 if t.startswith("-") else 1
    t = t.lstrip("+-")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):
        entero = t.split(",")[0].replace(".","")
        try: return float(sign*int(entero))
        except: return float("nan")
    s = re.sub(r"[^\d,.\-]","",t)
    if "," in s and "." in s:
        if s.rfind(",")>s.rfind("."):
            s = s.replace(".", "").replace(",",".")
        else:
            s = s.replace(",","")
    elif "," in s:
        s = s.replace(".", "").replace(",",".")
    else:
        parts = s.split(".")
        if len(parts)>2:
            s = "".join(parts[:-1])+"."+parts[-1]
    try:
        n = float(s)
        return float(int(n))*sign
    except:
        return float("nan")

def normalize_texto(v) -> str:
    return str(v).strip().lower()

NORMALIZERS = {
    "fecha": normalize_fecha,
    "usuario": normalize_texto,
    "monto": normalize_numero,
    "balance": normalize_numero,
    "transaccion": normalize_texto,        # clave canónica sin tilde
    "tipo de movimiento": normalize_texto,
    "tipo de bono": normalize_texto,
    "nro. documento": normalize_texto,
    "cajero": normalize_texto,
    "observaciones": normalize_texto,
}


# ————— Carga dinámica con fallback —————

def load_excel(path: str, canon_cols: list) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"❌ No existe el archivo: {path}")
        return pd.DataFrame()

    raw = pd.read_excel(path, header=None, dtype=str).fillna("").astype(str).applymap(str.strip)
    header_idx = None
    for i, row in raw.iterrows():
        lows = [canonical(c) for c in row.tolist()]
        if all(c in lows for c in canon_cols):
            header_idx = i
            break
    if header_idx is None:
        print("⚠️ No encontré encabezado, uso fila 0.")
        header_idx = 0

    df = pd.read_excel(path, header=header_idx)
    df.columns = [str(c).strip() for c in df.columns]
    lows = [canonical(c) for c in df.columns]
    mapping = {low: real for real, low in zip(df.columns, lows)}

    miss = [c for c in canon_cols if c not in mapping]
    if miss:
        print(f"❌ Faltan columnas en {os.path.basename(path)}: {miss}")
        return pd.DataFrame()

    reales = [mapping[c] for c in canon_cols]
    df2 = df[reales].copy().fillna("")
    df2.columns = canon_cols
    return df2.reset_index(drop=True)

# ————— Comparación —————

def compare_dfs(d1: pd.DataFrame, d2: pd.DataFrame, cols: list):
    n1, n2 = len(d1), len(d2)
    diffs = []
    for i in range(min(n1, n2)):
        for c in cols:
            r1, r2 = d1.at[i, c], d2.at[i, c]
            fn = NORMALIZERS[c]
            v1, v2 = fn(r1), fn(r2)
            if isinstance(v1, float) and isinstance(v2, float):
                if not ((pd.isna(v1) and pd.isna(v2)) or abs(v1-v2)<1e-6):
                    diffs.append((i+1, c, r1, r2))
            else:
                if str(v1)!=str(v2):
                    diffs.append((i+1, c, r1, r2))
    return diffs, n1, n2

# ————— Generación HTML —————

def make_html(diffs, n1, n2, cols, out):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tot = len(diffs)
    def title(c): return " ".join(w.capitalize() for w in c.split())
    rows = ""
    for f,c,v1,v2 in diffs:
        if c in ("monto","balance"):
            x1, x2 = normalize_numero(v1), normalize_numero(v2)
            d1 = str(int(x1)) if not pd.isna(x1) else ""
            d2 = str(int(x2)) if not pd.isna(x2) else ""
        else:
            d1, d2 = NORMALIZERS[c](v1), NORMALIZERS[c](v2)
        rows += f"<tr><td align=center>{f}</td><td>{title(c)}</td><td>{d1}</td><td>{d2}</td></tr>\n"
    if tot==0:
        rows = "<tr><td colspan=4 align=center>No hay diferencias.</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Comparación Excel</title>
<style>body{{font-family:sans-serif;padding:20px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:6px}}th{{background:#eee}}</style>
</head><body>
<h1>Comparación de Excel</h1>
<p>Generado: {t}</p>
<p><b>Filas exp:</b> {n1} — <b>Filas UI:</b> {n2} — <b>Difs:</b>
 <span style="color:{'red' if tot else 'green'}">{tot}</span></p>
<table><thead><tr><th>Fila</th><th>Columna</th><th>Exportado</th><th>UI</th></tr></thead><tbody>
{rows}
</tbody></table></body></html>"""
    with open(out,"w",encoding="utf-8") as f:
        f.write(html)
    print("✅ Reporte generado:", out)

# ————— Main —————

def main():
    print("Cargando exportado…")
    df1 = load_excel(EXCEL_EXPORT_PATH, COLUMNS_CANON)
    if df1.empty: return
    print("Cargando UI…")
    df2 = load_excel(EXCEL_UI_PATH, COLUMNS_CANON)
    if df2.empty: return
    print("Comparando…")
    diffs, n1, n2 = compare_dfs(df1, df2, COLUMNS_CANON)
    print(f"Diferencias encontradas: {len(diffs)}")
    make_html(diffs, n1, n2, COLUMNS_CANON, HTML_REPORT_PATH)

if __name__=="__main__":
    main()

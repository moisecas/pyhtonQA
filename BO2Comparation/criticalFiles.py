#!/usr/bin/env python3
# compare_repo_paquetes.py — Compara reportes con columnas:
# Proyecto | Versión | Última actualización | Archivo | Ruta | Hash

import os
import re
import math
import pandas as pd
from datetime import datetime

# ========= Config =========
EXCEL_EXPORT_PATH = r"C:\Users\moise\Downloads\critical-files (15).xlsx"  # <- BO2
EXCEL_UI_PATH     = r"c:\Users\moise\Downloads\criticalui.xlsx"         # <- UI
HTML_REPORT_PATH  = "diferencias_comparacion_repo.html"

COLUMNS = [
    "Proyecto",
    "Versión",
    "Última actualización",
    "Archivo",
    "Ruta",
    "Hash",
]
COLUMNS_LOWER = [c.lower() for c in COLUMNS]

# ========= Normalizadores =========
def normalize_fecha(valor) -> str:
    if isinstance(valor, (pd.Timestamp, datetime)):
        # Si tiene hora distinta de 00:00:00, incluimos hora
        if getattr(valor, "hour", 0) or getattr(valor, "minute", 0) or getattr(valor, "second", 0):
            return valor.strftime("%Y-%m-%d %H:%M:%S")
        return valor.strftime("%Y-%m-%d")

    s = str(valor).strip()
    if not s:
        return ""

    # Formatos comunes con hora
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    # Solo fecha
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass

    return s  # tal cual si no pudimos parsear

def normalize_texto(valor) -> str:
    return str(valor).strip().lower()

_semver_re = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")
def normalize_version(valor):
    """
    Normaliza versión a tupla de números (mayor, menor, parche).
    'v1.2.3-beta' -> (1,2,3). Si falta, se asume 0.
    Para comparar devolvemos la tupla; para mostrar, devolvemos string limpio.
    """
    s = str(valor).strip().lower()
    if not s:
        return (0,0,0)
    m = _semver_re.match(s)
    if not m:
        return (0,0,0) if s in ("", "nan", "none") else (s,)  # mantiene no parsables como string
    parts = [int(p) if p is not None else 0 for p in m.groups()]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def normalize_path(valor) -> str:
    """
    Unifica separadores, quita doble slash, barra final y lowercase.
    """
    s = str(valor).strip()
    if not s:
        return ""
    s = s.replace("\\", "/")
    s = re.sub(r"/+", "/", s)
    if s.endswith("/") and s != "/":
        s = s[:-1]
    return s.lower()

def normalize_hash(valor) -> str:
    """
    Quita espacios y prefijo 0x, deja solo [0-9a-f] en lowercase.
    """
    s = str(valor).strip().lower().replace(" ", "")
    if s.startswith("0x"):
        s = s[2:]
    s = re.sub(r"[^0-9a-f]", "", s)
    return s

NORMALIZERS_LOWER = {
    "proyecto": normalize_texto,
    "versión": normalize_version,
    "última actualización": normalize_fecha,
    "archivo": normalize_texto,
    "ruta": normalize_path,
    "hash": normalize_hash,
}

# ========= Carga dinámica de Excel =========
def load_excel_dynamic(excel_path: str, columns_expected_lower: list) -> pd.DataFrame:
    if not os.path.exists(excel_path):
        print(f"❌ No existe el archivo: {excel_path}")
        return pd.DataFrame()

    df_raw = pd.read_excel(excel_path, header=None, dtype=str)
    df_raw = df_raw.fillna("").astype(str).applymap(lambda x: x.strip())

    header_idx = None
    for idx, row in df_raw.iterrows():
        vals = [cell.strip().lower() for cell in row.tolist()]
        if all(col in vals for col in columns_expected_lower):
            header_idx = idx
            break

    if header_idx is None:
        print(f"❌ No encontré encabezado en '{os.path.basename(excel_path)}' con {columns_expected_lower}")
        return pd.DataFrame()

    df = pd.read_excel(excel_path, header=header_idx)
    df.columns = [str(c).strip() for c in df.columns]

    cols_lower_actuales = [c.lower() for c in df.columns]
    mapa_real = {low: real for real, low in zip(df.columns, cols_lower_actuales)}

    missing = [c for c in columns_expected_lower if c not in mapa_real]
    if missing:
        print(f"❌ En '{os.path.basename(excel_path)}' faltan columnas: {missing}")
        return pd.DataFrame()

    ordered_real = [mapa_real[c] for c in columns_expected_lower]
    out = df[ordered_real].copy().fillna("")
    out.columns = columns_expected_lower
    return out.reset_index(drop=True)

# ========= Clave y comparación =========
KEY_COLS = ["proyecto", "archivo", "ruta"]  # clave lógica del ítem

def make_key(row) -> tuple:
    return (
        NORMALIZERS_LOWER["proyecto"](row["proyecto"]),
        NORMALIZERS_LOWER["archivo"](row["archivo"]),
        NORMALIZERS_LOWER["ruta"](row["ruta"]),
    )

def normalize_cell(col_low: str, val):
    fn = NORMALIZERS_LOWER.get(col_low, normalize_texto)
    return fn(val)

def compare_sets(df_export: pd.DataFrame, df_ui: pd.DataFrame, columns_lower: list):
    # Mapear por clave
    map_export = {make_key(r): r for _, r in df_export.iterrows()}
    map_ui     = {make_key(r): r for _, r in df_ui.iterrows()}

    keys_exp = set(map_export.keys())
    keys_ui  = set(map_ui.keys())

    only_in_export = sorted(list(keys_exp - keys_ui))
    only_in_ui     = sorted(list(keys_ui - keys_exp))
    common_keys    = sorted(list(keys_exp & keys_ui))

    diffs = []  # (key_tuple, col_low, val_exp_disp, val_ui_disp)
    for k in common_keys:
        row_e = map_export[k]
        row_u = map_ui[k]
        for col_low in columns_lower:
            # Mostrar “Versión” como string legible, pero comparar tuplas
            val_e_norm = normalize_cell(col_low, row_e[col_low])
            val_u_norm = normalize_cell(col_low, row_u[col_low])

            equal = False
            if isinstance(val_e_norm, tuple) and isinstance(val_u_norm, tuple):
                equal = (val_e_norm == val_u_norm)
                # display amigable
                val_e_disp = ".".join(map(str, val_e_norm[:3])) if all(isinstance(x,int) for x in val_e_norm[:3]) else str(val_e_norm)
                val_u_disp = ".".join(map(str, val_u_norm[:3])) if all(isinstance(x,int) for x in val_u_norm[:3]) else str(val_u_norm)
            else:
                equal = (str(val_e_norm) == str(val_u_norm))
                val_e_disp = str(val_e_norm)
                val_u_disp = str(val_u_norm)

            if not equal:
                diffs.append((k, col_low, val_e_disp, val_u_disp))

    return only_in_export, only_in_ui, diffs

# ========= HTML =========
def key_to_text(key_tuple: tuple) -> str:
    proyecto, archivo, ruta = key_tuple
    return f"{proyecto} | {archivo} | {ruta}"

def generate_html_report_repo(only_export, only_ui, diffs, out_path: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def rows_missing(keys):
        if not keys:
            return '<tr><td colspan="1" style="text-align:center">—</td></tr>'
        return "\n".join(f"<tr><td>{key_to_text(k)}</td></tr>" for k in keys)

    def to_title(col_low: str) -> str:
        return " ".join(p.capitalize() for p in col_low.split())

    def rows_diffs(diffs):
        if not diffs:
            return '<tr><td colspan="4" style="text-align:center">—</td></tr>'
        out = []
        for k, col_low, ve, vu in diffs:
            out.append(f"""
            <tr>
              <td>{key_to_text(k)}</td>
              <td>{to_title(col_low)}</td>
              <td>{ve}</td>
              <td>{vu}</td>
            </tr>""")
        return "\n".join(out)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Comparación de Paquetes/Builds</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }}
    h1 {{ margin: 0 0 8px 0; }}
    .section {{ margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 14px; }}
    th {{ background: #f5f7fb; text-align: left; }}
    .muted {{ color: #666; }}
  </style>
</head>
<body>
  <h1>Comparación de reportes</h1>
  <div class="muted">Generado: {ts}</div>

  <div class="section">
    <h2>Faltan en UI</h2>
    <table>
      <thead><tr><th>Clave (proyecto | archivo | ruta)</th></tr></thead>
      <tbody>
        {rows_missing(only_export)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Faltan en Exportado</h2>
    <table>
      <thead><tr><th>Clave (proyecto | archivo | ruta)</th></tr></thead>
      <tbody>
        {rows_missing(only_ui)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Diferencias en filas comunes</h2>
    <table>
      <thead>
        <tr>
          <th>Clave</th>
          <th>Columna</th>
          <th>Exportado</th>
          <th>UI</th>
        </tr>
      </thead>
      <tbody>
        {rows_diffs(diffs)}
      </tbody>
    </table>
  </div>
</body>
</html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Reporte HTML generado: {out_path}")
    print(f"   • Faltan en UI: {len(only_export)}")
    print(f"   • Faltan en Exportado: {len(only_ui)}")
    print(f"   • Diferencias: {len(diffs)}")

# ========= Main =========
def main():
    print("Cargando Exportado…")
    df_exp = load_excel_dynamic(EXCEL_EXPORT_PATH, COLUMNS_LOWER)
    if df_exp.empty:
        print("❌ Exportado vacío / encabezados no encontrados.")
        return
    print(f"  → {len(df_exp)} filas.")

    print("Cargando UI…")
    df_ui = load_excel_dynamic(EXCEL_UI_PATH, COLUMNS_LOWER)
    if df_ui.empty:
        print("❌ UI vacío / encabezados no encontrados.")
        return
    print(f"  → {len(df_ui)} filas.")

    only_exp, only_ui, diffs = compare_sets(df_exp, df_ui, COLUMNS_LOWER)
    generate_html_report_repo(only_exp, only_ui, diffs, HTML_REPORT_PATH)

if __name__ == "__main__":
    main()

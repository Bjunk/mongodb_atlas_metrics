# analizar_atlas_zip.py
import zipfile, sys, io
import pandas as pd
import numpy as np
from pathlib import Path

zip_path = sys.argv[1] if len(sys.argv) > 1 else "atlas_metrics_20251018_120859.zip"

with zipfile.ZipFile(zip_path, 'r') as z:
    # Detecta carpeta raíz
    root = None
    for n in z.namelist():
        if n.endswith(".csv"):
            root = "/".join(n.split("/")[:-1])
            break
    if root is None:
        print("No se encontraron CSVs en el ZIP"); sys.exit(1)

    # Carga todos los CSV
    frames = []
    for n in z.namelist():
        if n.endswith(".csv") and n.startswith(root):
            with z.open(n) as f:
                try:
                    df = pd.read_csv(f)
                    df["__file"] = Path(n).name
                    frames.append(df)
                except Exception:
                    pass

df = pd.concat(frames, ignore_index=True)
# Normaliza columnas esperadas
cols = {c.lower(): c for c in df.columns}
name_col = cols.get("name") or cols.get("metric") or "NAME"
value_col = cols.get("value") or "VALUE"
host_col = cols.get("host") or cols.get("hostname") or "__file"
time_col = cols.get("timestamp") or cols.get("time") or cols.get("date") or None

# Limpia y tipa
df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
if time_col:
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

# Agrega
def p95(x): return np.nanpercentile(x, 95) if np.isfinite(x).any() else np.nan
def p99(x): return np.nanpercentile(x, 99) if np.isfinite(x).any() else np.nan

agg = df.groupby([host_col, name_col])[value_col].agg(
    count="count", mean="mean", p95=p95, p99=p99, max="max"
).reset_index().sort_values([name_col, host_col])

# Exporta
out_dir = Path("atlas_analysis_out"); out_dir.mkdir(exist_ok=True)
agg.to_csv(out_dir / "metric_summary_by_host.csv", index=False)

# Resumen por métrica (todos los hosts)
agg2 = df.groupby([name_col])[value_col].agg(mean="mean", p95=p95, p99=p99, max="max", count="count").reset_index()
agg2.to_csv(out_dir / "metric_summary_all_hosts.csv", index=False)

print("Listo. Archivos:")
print(out_dir / "metric_summary_by_host.csv")
print(out_dir / "metric_summary_all_hosts.csv")

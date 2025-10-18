#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
import os

def load_metrics(input_dir):
    """
    Carga los CSVs exportados por universal_atlas_metrics.sh
    """
    all_path = os.path.join(input_dir, "metric_summary_all_hosts.csv")
    hosts_path = os.path.join(input_dir, "metric_summary_by_host.csv")

    if not os.path.exists(all_path) or not os.path.exists(hosts_path):
        raise FileNotFoundError("❌ No se encontraron los archivos esperados en el directorio de métricas.")

    df_all = pd.read_csv(all_path)
    df_hosts = pd.read_csv(hosts_path)

    return df_all, df_hosts


def summarize_metric(df, keyword):
    subset = df[df["metric"].str.contains(keyword, case=False, na=False)]
    if subset.empty:
        return None
    return subset[["metric", "mean", "p95", "p99", "max"]].sort_values("p95", ascending=False).head(5)


def analyze(df_all):
    print("\n📊 === Análisis de Métricas Atlas ===")

    top = df_all.sort_values("p95", ascending=False).head(10)
    print("\n🏆 Top 10 métricas por p95:")
    print(top[["metric", "mean", "p95", "max"]])

    sections = {
        "CPU": ["CPU", "PROCESS_CPU", "NORMALIZED_CPU"],
        "Memoria": ["MEMORY", "RESIDENT", "VIRTUAL"],
        "Cache": ["CACHE", "DIRTY", "FILL_RATIO"],
        "IOPS": ["IOPS", "DISK"],
        "Latencia": ["LATENCY"]
    }

    insights = {}

    for name, patterns in sections.items():
        subset = pd.concat(
            [df_all[df_all["metric"].str.contains(p, case=False, na=False)] for p in patterns],
            axis=0
        ).drop_duplicates(subset=["metric"])
        if not subset.empty:
            insights[name] = subset.sort_values("p95", ascending=False).head(5)
            print(f"\n🔹 {name}:")
            print(insights[name][["metric", "mean", "p95", "max"]])
        else:
            print(f"\n⚠️ No se encontraron métricas para {name}.")

    return insights


def generate_recommendation(insights):
    """
    Usa heurísticas basadas en las métricas para determinar si escalar a M40 o mejorar IOPS.
    """
    cpu = insights.get("CPU", pd.DataFrame())
    mem = insights.get("Memoria", pd.DataFrame())
    cache = insights.get("Cache", pd.DataFrame())

    cpu_p95 = cpu["p95"].mean() if not cpu.empty else 0
    mem_p95 = mem["p95"].mean() if not mem.empty else 0
    cache_p95 = cache["p95"].mean() if not cache.empty else 0

    print("\n🧠 === Evaluación del Dimensionamiento ===")

    if cpu_p95 < 60 and mem_p95 > 80:
        print("🔸 Estás limitado por **memoria**, no por CPU. Recomendado: M40 Low-CPU (2 vCPU / 16 GB RAM).")
    elif cpu_p95 > 80:
        print("🔸 CPU alta. Considera optimizar queries o subir a M40 completo (4 vCPU / 16 GB RAM).")
    elif cache_p95 > 90:
        print("🔸 Cache saturada: más RAM beneficiaría el rendimiento.")
    else:
        print("✅ Tu cluster está bien dimensionado. Mantén M30 y monitorea crecimiento.")

    print("\n📈 Recomendación general:")
    print("- Monitorea CACHE_USED_BYTES y PROCESS_NORMALIZED_CPU_USER.")
    print("- Si CACHE_USED_BYTES supera el 85% sostenido, sube a M40 Low-CPU.")
    print("- Si CPU promedio >70%, considera M40 estándar o auto-scaling CPU.")


def main():
    parser = argparse.ArgumentParser(description="Analiza métricas de MongoDB Atlas y genera insights automáticos.")
    parser.add_argument("--input-dir", required=True, help="Directorio con los archivos de métricas CSV")
    args = parser.parse_args()

    df_all, df_hosts = load_metrics(args.input_dir)
    insights = analyze(df_all)
    generate_recommendation(insights)


if __name__ == "__main__":
    main()

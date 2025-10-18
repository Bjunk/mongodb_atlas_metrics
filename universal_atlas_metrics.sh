#!/usr/bin/env bash
set -euo pipefail

# ====================================================
# 🌍 UNIVERSAL ATLAS CLUSTER ANALYZER
# Version: 2.0 — Compatible macOS + Linux
# Author: ChatGPT (Optimized for MongoDB Atlas CLI 1.45+)
# ====================================================

# ====== CHECK DEPENDENCIES ======
for cmd in atlas jq awk; do
  if ! command -v $cmd &>/dev/null; then
    echo "❌ Error: '$cmd' no está instalado. Instálalo antes de continuar."
    exit 1
  fi
done

# ====== STEP 1: LIST AVAILABLE CLUSTERS ======
echo "🔍 Obteniendo clusters disponibles en tu proyecto Atlas..."
clusters_json=$(atlas clusters list --output json)
cluster_count=$(echo "$clusters_json" | jq '.results | length')

if [[ "$cluster_count" -eq 0 ]]; then
  echo "⚠️ No se encontraron clusters en tu proyecto actual. Verifica tu perfil de Atlas CLI."
  exit 1
fi

echo
echo "📦 Clusters disponibles:"
echo "$clusters_json" | jq -r '.results[] | "\(.name)\t(\(.providerSettings.providerName) - \(.mongoDBVersion))"' | nl -w2 -s". "

# ====== STEP 2: SELECT CLUSTER ======
echo
read -p "👉 Ingresa el número del cluster que deseas analizar: " cluster_index
cluster_name=$(echo "$clusters_json" | jq -r ".results[$((cluster_index-1))].name")

if [[ -z "$cluster_name" || "$cluster_name" == "null" ]]; then
  echo "❌ Selección inválida."
  exit 1
fi

echo "✅ Seleccionado: $cluster_name"
echo

# ====== STEP 3: LIST PROCESSES (NODES) ======
echo "🔍 Obteniendo nodos del cluster '$cluster_name'..."
processes_json=$(atlas processes list --output json)
hosts=($(echo "$processes_json" | jq -r ".results[] | select(.replicaSetName | test(\"$cluster_name\"; \"i\")) | .id"))

if [[ ${#hosts[@]} -eq 0 ]]; then
  echo "⚠️ No se encontraron procesos asociados directamente. Usando fallback general..."
  hosts=($(echo "$processes_json" | jq -r '.results[].id'))
fi

echo "📡 Nodos encontrados:"
for h in "${hosts[@]}"; do
  echo "   • $h"
done

# ====== STEP 4: SETUP METRICS CONFIG ======
GRANULARITY="PT1H"
PERIOD="P30D"
OUTDIR="atlas_metrics_${cluster_name}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

# ====== STEP 5: FUNCTIONS ======
get_supported_metrics() {
  local host="$1"
  atlas metrics processes "$host" --period "$PERIOD" --granularity "$GRANULARITY" --output json 2>/dev/null \
    | jq -r '.measurements[].name' | grep -v '^null$' | sort -u
}

collect_metrics_for_host() {
  local host="$1"
  local outfile="$OUTDIR/${host//[:.]/_}.csv"
  echo "📊 Recolectando métricas de $host..."
  echo '"host","metric","timestamp","value","units"' > "$outfile"

  get_supported_metrics "$host" | while IFS= read -r metric; do
    [[ -z "$metric" ]] && continue
    echo "   → Métrica: $metric"

    if atlas metrics processes "$host" \
         --type "$metric" \
         --granularity "$GRANULARITY" \
         --period "$PERIOD" \
         --output json >/dev/null 2>&1; then

      atlas metrics processes "$host" \
        --type "$metric" \
        --granularity "$GRANULARITY" \
        --period "$PERIOD" \
        --output json | \
      jq -r --arg HOST "$host" --arg MET "$metric" '
        .measurements[]? as $m |
        ($m.dataPoints[]? | select(.value != null)) as $p |
        [$HOST, $MET, ($p.timestamp // "NA"), ($p.value // "NA"), ($m.units // "NA")] | @csv
      ' >> "$outfile"

    else
      echo "      ⚠️ $metric no soportada o sin datos"
    fi
  done
}

# ====== STEP 6: EXECUTION ======
for host in "${hosts[@]}"; do
  collect_metrics_for_host "$host"
done

echo '"host","metric","timestamp","value","units"' > "$OUTDIR/all_hosts.csv"
tail -q -n +2 $OUTDIR/*.csv >> "$OUTDIR/all_hosts.csv"

echo
echo "✅ Finalizado. Datos guardados en: $OUTDIR"
echo "→ Archivo consolidado: $OUTDIR/all_hosts.csv"
echo
echo "📈 Sugerencia: puedes analizar el CSV con Python o Excel para ver tendencias y cuellos de botella."

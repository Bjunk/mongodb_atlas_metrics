# 🧠 Atlas Cluster Performance Analyzer

**A universal toolkit to collect and analyze performance metrics from MongoDB Atlas clusters.**  
This project helps you understand whether your cluster is correctly sized — identifying potential bottlenecks in **CPU, memory, cache, or disk I/O** — and provides smart recommendations to optimize cost and performance.

---

## 🚀 Overview

The toolkit consists of two components:

### 1. `universal_atlas_metrics.sh`
> **Purpose:** Collects detailed metrics from MongoDB Atlas using the official `atlas` CLI.

This script:
- Automatically discovers your available clusters.
- Lets you select which cluster to analyze.
- Retrieves 30-day historical metrics for all nodes in the cluster.
- Exports the data into CSV files for further analysis.

📦 **Output directory structure:**

atlas_metrics_YYYYMMDD_HHMMSS/
├── raw_metrics.csv
├── metric_summary_by_host.csv
└── metric_summary_all_hosts.csv

Each file contains normalized time-series metrics such as CPU utilization, cache usage, IOPS, memory consumption, and index sizes.

---

### 2. `analyze_metrics.py`
> **Purpose:** Processes the exported CSV metrics and generates an intelligent performance summary.

This script:
- Parses and aggregates key Atlas metrics using Pandas.
- Highlights top metrics by **p95**, **mean**, and **max** values.
- Detects patterns like:
  - High CPU utilization (compute-bound)
  - Cache pressure or memory saturation (memory-bound)
  - Excessive disk reads/writes (I/O-bound)
- Provides an **AI-style recommendation** on whether you should:
  - Keep your current instance size (e.g., `M30`)
  - Upgrade to a higher tier (e.g., `M40`, `M40 Low-CPU`, `M50`)
  - Improve query efficiency or indexes instead of scaling

---

## 🧩 Typical Workflow

1. **Authenticate** with your Atlas CLI profile:
   ```bash
   atlas auth login

2.	Collect metrics:
   bash universal_atlas_metrics.sh

3.	Run the analysis:
   python3 analyze_metrics.py --input-dir atlas_metrics_20251018_120814

4.	Review the insights:
The output will include:
	•	Top 10 metrics by percentile (p95)
	•	Sectioned summaries (CPU, Memory, Cache, Disk)
	•	A plain-English recommendation:
    🔸 Your workload is memory-bound.
    Recommended: M40 Low-CPU (2 vCPU / 16 GB RAM).

📊 Example Output
🏆 Top 10 metrics by p95:
metric                     mean         p95          max
DB_DATA_SIZE_TOTAL          5.12e+10     5.23e+10     5.30e+10
CACHE_USED_BYTES            1.11e+09     1.70e+09     1.71e+09
PROCESS_NORMALIZED_CPU_USER 1.45e+01     5.75e+01     9.89e+01

🧠 Cluster Sizing Evaluation:
🔸 Memory-bound workload detected.
🔹 Recommendation: M40 Low-CPU (2 vCPU / 16 GB RAM, 3000 IOPS).
✅ CPU and IOPS levels are healthy — no scaling needed there.

⚡ Benefits

Benefit
Description
Data-Driven Scaling
Avoid guessing when to upgrade or downgrade clusters — base decisions on real performance metrics.
Cost Optimization
Identify if you’re paying for unused CPU or if more RAM would yield a better ROI.
Preventive Diagnostics
Detect bottlenecks before they cause slow queries or outages.
Universal Compatibility
Works with any Atlas cluster (Replica Set or Sharded) via CLI API access.
Automation-Ready
Can be integrated into CI/CD or cron jobs for periodic performance reviews.

🧰 Requirements
	•	MongoDB Atlas CLI ≥ v1.45.0
	•	Python 3.8+
	•	Pandas and NumPy
	•	Atlas API Key or authenticated session (atlas auth login)

Install dependencies:
pip install pandas numpy

🧩 Example Use Case

Your M30 cluster shows stable CPU (15%) but occasional query slowdowns.

Running this toolkit reveals:
	•	Cache usage near 85% of available memory
	•	Low CPU utilization

✅ The analysis recommends moving to M40 Low-CPU — doubling RAM from 8 GB → 16 GB without paying for more CPU cores.

🧠 Key Insight

“Scaling MongoDB Atlas isn’t just about CPU —
it’s about understanding where your workload lives: in compute, memory, or I/O.
This toolkit gives you the data to make that call confidently.”

🪄 Data Flow Diagram
flowchart LR
    A[MongoDB Atlas Cluster] -->|atlas CLI| B[universal_atlas_metrics.sh]
    B -->|Exports CSVs| C[Metrics CSV Files]
    C -->|Analyzed with Pandas| D[analyze_metrics.py]
    D -->|Generates| E[Smart Recommendations]
    E -->|Output| F[Console / Markdown Report]

🧩 Future Enhancements
	•	Generate Markdown or HTML performance reports
	•	Integrate visualization (Matplotlib / Plotly)
	•	Slack / Email notification integration for automated health checks
	•	Add trend analysis for growing datasets

Developed by Pablo Aravena

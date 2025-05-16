import pandas as pd
import os

METRICS_LOG = 'usage_metrics_log.csv'
REPORT_FILE = 'historical_usage_report.txt'

if os.path.exists(METRICS_LOG):
    df = pd.read_csv(METRICS_LOG)
    with open(REPORT_FILE, 'w') as f:
        f.write('Historical Usage Report\n')
        f.write('='*30 + '\n')
        for metric in ['memory_mb', 'cpu_percent', 'disk_percent', 'bytes_sent', 'bytes_recv', 'gpu_load', 'gpu_mem']:
            if metric in df.columns:
                values = pd.to_numeric(df[metric], errors='coerce').dropna()
                if not values.empty:
                    f.write(f"{metric}:\n")
                    f.write(f"  Min: {values.min():.2f}\n")
                    f.write(f"  Max: {values.max():.2f}\n")
                    f.write(f"  Mean: {values.mean():.2f}\n")
                    f.write(f"  Std: {values.std():.2f}\n\n")
        f.write('Report generated from usage_metrics_log.csv\n')
    print(f"Historical usage report written to {REPORT_FILE}")
else:
    print(f"{METRICS_LOG} not found.") 
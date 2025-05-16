import pandas as pd
import os

METRICS_LOG = 'usage_metrics_log.csv'
ANOMALY_STD_THRESHOLD = 3
ANOMALY_SPIKE_THRESHOLD = 0.5  # 50% increase

if os.path.exists(METRICS_LOG):
    df = pd.read_csv(METRICS_LOG)
    for metric in ['memory_mb', 'cpu_percent', 'disk_percent']:
        if metric not in df.columns:
            continue
        values = df[metric].astype(float)
        mean = values.mean()
        std = values.std()
        anomalies = []
        for i, val in enumerate(values):
            # Stddev-based anomaly
            if abs(val - mean) > ANOMALY_STD_THRESHOLD * std:
                anomalies.append((i, val, 'stddev'))
            # Spike-based anomaly
            if i > 0 and (val - values[i-1]) > ANOMALY_SPIKE_THRESHOLD * values[i-1]:
                anomalies.append((i, val, 'spike'))
        if anomalies:
            print(f"Anomalies detected in {metric}:")
            for idx, val, typ in anomalies:
                print(f"  Row {idx}: {val} ({typ})")
        else:
            print(f"No anomalies detected in {metric}.")
else:
    print(f"{METRICS_LOG} not found.") 
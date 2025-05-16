import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from scipy.stats import linregress

LOG_FILE = 'usage_metrics_log.csv'
WINDOW_SIZE = 50  # Number of recent samples to analyze
SLOPE_THRESHOLD = 0.05  # MB per sample (tune as needed)


def analyze_memory_trend(log_file=LOG_FILE, window_size=WINDOW_SIZE, slope_threshold=SLOPE_THRESHOLD):
    if not os.path.exists(log_file):
        print(f"Log file {log_file} not found.")
        return
    df = pd.read_csv(log_file)
    if 'memory_mb' not in df.columns:
        print("No memory_mb column in log file.")
        return
    if len(df) < window_size:
        print(f"Not enough data points for trend analysis (need {window_size}, have {len(df)}).")
        return
    # Analyze the most recent window
    recent = df.tail(window_size)
    y = recent['memory_mb'].astype(float).values
    x = np.arange(len(y))
    # Linear regression (trend slope)
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    # Moving average and std
    moving_avg = np.mean(y)
    std = np.std(y)
    print(f"Memory trend analysis (last {window_size} samples):")
    print(f"  Slope: {slope:.4f} MB/sample")
    print(f"  Mean: {moving_avg:.2f} MB")
    print(f"  Min: {y.min():.2f} MB, Max: {y.max():.2f} MB")
    if slope > slope_threshold:
        print(f"WARNING: Upward memory trend detected! Slope={slope:.4f} MB/sample (possible leak or regression)")
    else:
        print("No significant upward memory trend detected.")
    # Anomaly detection: flag samples >3 std from mean
    anomalies = np.where(np.abs(y - moving_avg) > 3 * std)[0]
    if len(anomalies) > 0:
        print(f"ANOMALY: Sudden memory jump/drop detected at indices: {anomalies.tolist()} (values: {y[anomalies]})")

if __name__ == "__main__":
    analyze_memory_trend() 
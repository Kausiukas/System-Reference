import streamlit as st
import pandas as pd
import os
import json
from streamlit_autorefresh import st_autorefresh
import glob
import numpy as np
from gc_utils import manual_gc_and_log
from maintenance_utils import defragment_index, rebuild_cache, rotate_logs, auto_restart_if_needed, run_stress_test, generate_maintenance_report
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="System & App Metrics Dashboard", layout="wide")

st.title("System & Application Metrics Dashboard")

# Auto-refresh every 10 seconds
st_autorefresh(interval=10 * 1000)

# Load system metrics
sys_log = 'usage_metrics_log.csv'
if os.path.exists(sys_log):
    sys_df = pd.read_csv(sys_log)
    st.header("System Metrics")
    st.line_chart(sys_df.set_index('timestamp')[['memory_mb', 'cpu_percent', 'disk_percent']])
    st.line_chart(sys_df.set_index('timestamp')[['bytes_sent', 'bytes_recv']])
    if 'gpu_load' in sys_df.columns and 'gpu_mem' in sys_df.columns:
        st.line_chart(sys_df.set_index('timestamp')[['gpu_load', 'gpu_mem']])
    st.dataframe(sys_df.tail(10))
else:
    st.warning(f"{sys_log} not found.")

# Load app metrics
app_log = 'app_metrics_log.csv'
if os.path.exists(app_log):
    app_df = pd.read_csv(app_log)
    st.header("App Metrics")
    st.line_chart(app_df.set_index('timestamp')[['queries', 'cache_hits', 'cache_misses', 'errors']])
    st.dataframe(app_df.tail(10))
else:
    st.warning(f"{app_log} not found.")

# Load LLM and embedding metrics
metrics_file = 'metrics_history.json'
if os.path.exists(metrics_file):
    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)
    
    # --- ALERTS SECTION ---
    if 'alerts' in metrics_data and metrics_data['alerts']:
        st.header('Recent Alerts')
        alerts_df = pd.DataFrame(metrics_data['alerts'])
        alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
        alerts_df = alerts_df.sort_values('timestamp', ascending=False)
        st.dataframe(alerts_df[['timestamp', 'subject', 'body']].head(10), use_container_width=True)
    else:
        st.info('No recent alerts.')
    
    # --- PROFILING & PERFORMANCE METRICS SECTION ---
    st.header("Performance & Profiling Metrics")
    # Node execution times
    if 'node_executions' in metrics_data and metrics_data['node_executions']:
        node_df = pd.DataFrame(metrics_data['node_executions'])
        node_df['timestamp'] = pd.to_datetime(node_df['timestamp'])
        node_df = node_df.sort_values('timestamp', ascending=False)
        st.subheader("Slowest Nodes (last 20)")
        slowest = node_df.sort_values('duration', ascending=False).head(20)
        st.dataframe(slowest[['timestamp', 'node_name', 'duration', 'status', 'error']])
        st.line_chart(node_df.set_index('timestamp')['duration'])
    # LLM call summary
    if 'llm_calls' in metrics_data and metrics_data['llm_calls']:
        st.subheader("LLM Call Summary")
        llm_df = pd.DataFrame(metrics_data['llm_calls'])
        st.write(llm_df.describe(include='all'))
        # Token usage
        if 'total_tokens' in llm_df:
            st.metric("Avg Total Tokens", f"{llm_df['total_tokens'].mean():.1f}")
        if 'prompt_tokens' in llm_df:
            st.metric("Avg Prompt Tokens", f"{llm_df['prompt_tokens'].mean():.1f}")
        if 'completion_tokens' in llm_df:
            st.metric("Avg Completion Tokens", f"{llm_df['completion_tokens'].mean():.1f}")
    # Embedding call summary
    if 'embedding_calls' in metrics_data and metrics_data['embedding_calls']:
        st.subheader("Embedding Call Summary")
        emb_df = pd.DataFrame(metrics_data['embedding_calls'])
        st.write(emb_df.describe(include='all'))
    # Cache hit rates
    if 'cache_hit_rate' in metrics_data and metrics_data['cache_hit_rate']:
        st.subheader("Cache Hit Rates")
        cache_df = pd.DataFrame(metrics_data['cache_hit_rate'])
        st.dataframe(cache_df.tail(20))

    # LLM Calls
    if 'llm_calls' in metrics_data and metrics_data['llm_calls']:
        st.header("LLM Call Metrics")
        llm_df = pd.DataFrame(metrics_data['llm_calls'])
        llm_df['timestamp'] = pd.to_datetime(llm_df['timestamp'])
        
        # Latency over time
        st.subheader("Latency Over Time")
        st.line_chart(llm_df.set_index('timestamp')['latency'])
        
        # Success rate
        success_rate = llm_df['success'].mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Average latency
        avg_latency = llm_df['latency'].mean()
        st.metric("Average Latency", f"{avg_latency:.2f}s")

        # Throughput (calls per minute, last 10 minutes)
        now = llm_df['timestamp'].max()
        ten_min_ago = now - pd.Timedelta(minutes=10)
        recent_calls = llm_df[llm_df['timestamp'] >= ten_min_ago]
        throughput = len(recent_calls) / 10  # calls per minute
        st.metric("Throughput (calls/min, last 10 min)", f"{throughput:.2f}")
        
        # Input size distribution
        st.subheader("Input Size Distribution")
        st.bar_chart(llm_df['input_size'].value_counts())
        
        # Recent calls
        st.subheader("Recent LLM Calls")
        st.dataframe(llm_df.tail(10))
    
    # Embedding Calls
    if 'embedding_calls' in metrics_data and metrics_data['embedding_calls']:
        st.header("Embedding Call Metrics")
        emb_df = pd.DataFrame(metrics_data['embedding_calls'])
        emb_df['timestamp'] = pd.to_datetime(emb_df['timestamp'])
        
        # Latency over time
        st.subheader("Latency Over Time")
        st.line_chart(emb_df.set_index('timestamp')['latency'])
        
        # Success rate
        success_rate = emb_df['success'].mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Average latency
        avg_latency = emb_df['latency'].mean()
        st.metric("Average Latency", f"{avg_latency:.2f}s")
        
        # Input size distribution
        st.subheader("Input Size Distribution")
        st.bar_chart(emb_df['input_size'].value_counts())
        
        # Recent calls
        st.subheader("Recent Embedding Calls")
        st.dataframe(emb_df.tail(10))

    # Memory trend analysis
    st.header("Memory Usage Trend Analysis")
    if 'memory_usage' in metrics_data and metrics_data['memory_usage']:
        mem_df = pd.DataFrame(metrics_data['memory_usage'])
        mem_df['timestamp'] = pd.to_datetime(mem_df['timestamp'])
        mem_df = mem_df.sort_values('timestamp')
        st.line_chart(mem_df.set_index('timestamp')['value'])
        # Fit a simple trend line
        if len(mem_df) > 5:
            x = np.arange(len(mem_df))
            y = mem_df['value'].values
            coeffs = np.polyfit(x, y, 1)
            slope = coeffs[0]
            if slope > 0.01:  # Arbitrary threshold for upward trend
                st.warning(f"Memory usage is increasing (slope={slope:.2f} MB/step). Possible memory leak detected!")
            else:
                st.success(f"No significant memory increase detected (slope={slope:.2f} MB/step).")
    else:
        st.info("No memory usage data found.")

    # --- MEMORY STABILITY SECTION ---
    st.header("Memory Stability Checks")
    if 'memory_stability_checks' in metrics_data and metrics_data['memory_stability_checks']:
        checks = metrics_data['memory_stability_checks']
        latest = checks[-1]
        st.subheader(f"Last Check: {latest['timestamp']}")
        st.code(latest['output'])
        if 'WARNING' in latest['output']:
            st.error("Potential memory leak or regression detected!")
        else:
            st.success("No significant memory leak detected.")
        if len(checks) > 1:
            with st.expander("Show previous checks"):
                for check in reversed(checks[:-1]):
                    st.markdown(f"**{check['timestamp']}**")
                    st.code(check['output'])
    else:
        st.info("No memory stability checks found.")

    # --- MEMORY LEAK CHECKS SECTION ---
    st.header("Memory Leak Checks (tracemalloc)")
    if 'memory_leak_checks' in metrics_data and metrics_data['memory_leak_checks']:
        checks = metrics_data['memory_leak_checks']
        latest = checks[-1]
        st.subheader(f"Last Check: {latest['timestamp']}")
        st.code(latest['output'])
        if 'Total growth' in latest['output'] and any(float(s.split(': ')[-1].replace('KB','')) > 102400 for s in latest['output'].splitlines() if 'Total growth' in s):
            st.error("Potential memory leak detected!")
        else:
            st.success("No significant memory leak detected.")
        if len(checks) > 1:
            with st.expander("Show previous checks"):
                for check in reversed(checks[:-1]):
                    st.markdown(f"**{check['timestamp']}**")
                    st.code(check['output'])
    else:
        st.info("No memory leak checks found.")
else:
    st.warning(f"{metrics_file} not found.")

# Show profiling results
st.header("Profiling Results")
profile_dir = "profiles"
if os.path.exists(profile_dir):
    txt_files = sorted(glob.glob(os.path.join(profile_dir, "*.txt")), reverse=True)[:5]
    if txt_files:
        for txt_file in txt_files:
            with open(txt_file, "r") as f:
                content = f.read()
            st.subheader(f"Profiling: {os.path.basename(txt_file)}")
            with st.expander("Show profiling summary"):
                st.text(content)
    else:
        st.info("No profiling summaries found in profiles/ directory.")
else:
    st.info("profiles/ directory not found.")

# Manual GC trigger
st.header("Manual Garbage Collection")
if st.button("Run GC and Log Stats"):
    mem_before, mem_after, gc_counts, gc_stats = manual_gc_and_log()
    st.write(f"Memory before: {mem_before:.2f} MB")
    st.write(f"Memory after: {mem_after:.2f} MB")
    st.write(f"GC counts: {gc_counts}")
    if gc_stats:
        st.write(f"GC stats: {gc_stats}")

# Maintenance Actions
st.header("Maintenance Actions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Defragment Index"):
        result = defragment_index()
        st.success(f"Defragment index: {result}")
    if st.button("Rebuild Cache"):
        result = rebuild_cache()
        st.success(f"Rebuild cache: {result}")
with col2:
    if st.button("Rotate Logs"):
        result = rotate_logs()
        st.success(f"Rotate logs: {result}")
    if st.button("Auto-Restart If Needed"):
        result = auto_restart_if_needed()
        st.success(f"Auto-restart: {result}")
with col3:
    if st.button("Run Stress Test"):
        result = run_stress_test()
        st.success(f"Run stress test: {result}")
    if st.button("Generate Maintenance Report"):
        result = generate_maintenance_report()
        st.info(result)

# --- LOG AGGREGATION SECTION ---
st.header("Aggregated Logs (Centralized)")
agg_log_path = os.path.join("logs", "aggregated.log")
if os.path.exists(agg_log_path):
    with open(agg_log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    st.subheader(f"Last {min(200, len(lines))} Log Entries")
    # Search/filter box
    search_term = st.text_input("Filter logs by keyword", "")
    filtered = [line for line in lines if search_term.lower() in line.lower()]
    st.text("".join(filtered[-200:]))
    if st.button("Refresh Aggregated Logs"):
        st.experimental_rerun()
else:
    st.info("logs/aggregated.log not found. Run log_aggregator.py to generate it.")

# --- METRIC-LOG CORRELATION SECTION ---
st.header("Correlate System Metrics with App Logs")

# Time window selection
col1, col2 = st.columns(2)
def_time_end = datetime.now()
def_time_start = def_time_end - pd.Timedelta(hours=1)
time_start = col1.datetime_input("Start Time", def_time_start)
time_end = col2.datetime_input("End Time", def_time_end)

# Load system metrics for the window
if os.path.exists(sys_log):
    sys_df = pd.read_csv(sys_log)
    sys_df['timestamp'] = pd.to_datetime(sys_df['timestamp'])
    mask = (sys_df['timestamp'] >= time_start) & (sys_df['timestamp'] <= time_end)
    window_df = sys_df[mask]
    if not window_df.empty:
        st.subheader("System Metrics in Window")
        st.line_chart(window_df.set_index('timestamp')[['memory_mb', 'cpu_percent', 'disk_percent']])
        st.dataframe(window_df.tail(10))
    else:
        st.info("No system metrics in selected window.")
else:
    st.info(f"{sys_log} not found.")

# Load and filter logs for the window
if os.path.exists(agg_log_path):
    with open(agg_log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_lines = f.readlines()
    # Extract timestamp from each log line (format: [timestamp] [source] ...)
    def parse_log_time(line):
        try:
            ts = line.split(']')[0][1:]
            return pd.to_datetime(ts)
        except Exception:
            return None
    log_times = [parse_log_time(line) for line in log_lines]
    filtered_logs = [line for line, ts in zip(log_lines, log_times)
                     if ts is not None and time_start <= ts <= time_end]
    st.subheader(f"Log Entries in Window ({len(filtered_logs)})")
    st.text("".join(filtered_logs[-200:]))
else:
    st.info("logs/aggregated.log not found.")

def plot_memory_stability(self):
    """Plot memory stability metrics and trends."""
    try:
        # Get latest memory stability report
        latest_report = self.metrics_tracker.metrics_history.get('memory_stability_reports', [])[-1]
        if not latest_report:
            return
        
        # Create subplot for each window
        windows = latest_report['windows']
        fig, axes = plt.subplots(len(windows), 1, figsize=(12, 4*len(windows)))
        if len(windows) == 1:
            axes = [axes]
        
        for ax, (window_name, stats) in zip(axes, windows.items()):
            # Plot memory usage trend
            hours = int(window_name[:-1]) if window_name.endswith('h') else int(window_name[:-1]) * 24
            window_data = [
                m for m in self.metrics_tracker.metrics_history['memory_usage']
                if (datetime.now() - datetime.fromisoformat(m['timestamp'])).total_seconds() <= hours * 3600
            ]
            
            if window_data:
                times = [datetime.fromisoformat(m['timestamp']) for m in window_data]
                values = [m['value'] for m in window_data]
                
                ax.plot(times, values, 'b-', label='Memory Usage')
                
                # Plot trend line
                if len(values) > 1:
                    x = np.arange(len(values))
                    slope, intercept = np.polyfit(x, values, 1)
                    trend_line = slope * x + intercept
                    ax.plot(times, trend_line, 'r--', 
                           label=f'Trend ({slope:.2f} MB/sample)')
                
                # Plot anomalies if any
                if 'anomalies' in stats:
                    anomaly_times = [datetime.fromisoformat(ts) for ts in stats['anomalies']['timestamps']]
                    anomaly_values = [values[times.index(t)] for t in anomaly_times]
                    ax.scatter(anomaly_times, anomaly_values, color='red', 
                             label='Anomalies', zorder=5)
                
                ax.set_title(f'Memory Stability - {window_name} Window')
                ax.set_xlabel('Time')
                ax.set_ylabel('Memory Usage (MB)')
                ax.legend()
                ax.grid(True)
                
                # Add stability status
                status = stats.get('stability', 'unknown')
                ax.text(0.02, 0.98, f'Status: {status}',
                       transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error plotting memory stability: {str(e)}")
        return None

def update_dashboard(self):
    """Update all dashboard visualizations."""
    try:
        # Update memory usage plot
        self.memory_plot = self.plot_memory_usage()
        
        # Update memory stability plot
        self.stability_plot = self.plot_memory_stability()
        
        # Update other plots...
        
        logger.info("Dashboard updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        return False 
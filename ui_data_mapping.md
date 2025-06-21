# UI Data Mapping (ID: 1)

This document maps the UI components defined in `background_agents_dashboard_ui.md` to the specific source files and functions that provide their data.

---
## 1.1 Sidebar (Control Panel)

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.1.1 | Quick Status | `background_agents_dashboard.py` | `main_dashboard()` | A Streamlit `st.empty()` placeholder whose content (`st.success`, `st.warning`, `st.error`) is determined by the `AGENTS_AVAILABLE` boolean and the `st.session_state.system_initialized` flag. |
| 1.1.2.1 | LangSmith API Key | `background_agents_dashboard.py` | `st.text_input`, `os.getenv` | A Streamlit text input that displays the value of the `LANGCHAIN_API_KEY` environment variable. |
| 1.1.2.2 | Project Name | `background_agents_dashboard.py` | `st.text_input`, `os.getenv` | A Streamlit text input that displays the value of the `LANGCHAIN_PROJECT` environment variable. |
| 1.1.3.x | Auto Refresh | `background_agents_dashboard.py` | `st.checkbox`, `st.selectbox` | Standard Streamlit components. The refresh is triggered by `time.sleep()` and `st.rerun()` at the end of the script. |
| 1.1.4.1 | Demo Mode | `background_agents_dashboard.py` | `st.checkbox`, `st.session_state`| A Streamlit checkbox whose state is stored in `st.session_state.demo_mode`. This value is passed to the system during initialization. |
| 1.1.5.1 | Initialize/Stop Button | `background_agents_dashboard.py`| `st.button` | A Streamlit button that triggers either the `dashboard.initialize_system()` or `dashboard.cleanup()` methods depending on the system's state. |

---
## 1.2 Main Dashboard Area

### 1.2.1 Header

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.1.1 | Title | `background_agents_dashboard.py` | `st.title()` | A static title for the dashboard. |
| 1.2.1.2 | Status Banner | `background_agents_dashboard.py` | `st.info()` | A banner that shows a static "Agents are running" message with the current timestamp. |

### 1.2.2 Agent Status Section (Common Metrics)

These metrics are sourced from base properties and methods that are common to every agent.

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| (Agent Title) | Agent Name | `background_agents/coordination/base_agent.py` | `BaseAgent.agent_name` | The `agent_name` attribute is set in the `__init__` method of each specific agent class. |
| (Agent Metric) | State | `background_agents/coordination/shared_state.py` | `SharedState.get_active_agents()` -> `heartbeat_data['state']` | The agent's current `AgentState` is retrieved from the latest heartbeat data stored in the `SharedState`. |
| (Agent Metric) | Uptime | `background_agents/coordination/base_agent.py` | `BaseAgent.get_uptime()` | This method calculates the `timedelta` between the current time and the `_init_start_time` set when the agent was instantiated. |
| (Agent Metric) | Errors | `background_agents/coordination/base_agent.py` | `BaseAgent.errors` | A list attribute on the `BaseAgent` class that accumulates error dictionaries. The UI displays the `len()` of this list. |
| (Agent Metric) | Heartbeat | `background_agents/coordination/shared_state.py`| `SharedState.get_active_agents()` | The presence of a recent heartbeat record for an agent in the `SharedState` determines if the "✅" icon is shown. |

### 1.2.2 Agent Status Section (Specific Metrics)

These metrics are unique to each agent and are typically sourced from a `get_agent_metrics()` method or specific attributes on the agent's class.

| UI ID | Agent & Metric | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.2.1.3 | **LangSmith Bridge**<br/>*Traces Collected* | `background_agents/monitoring/langsmith_bridge.py` | `LangSmithBridgeAgent.traces_collected` | An integer attribute that is incremented within the `_process_cycle` method each time traces are successfully fetched from the LangSmith API. |
| 1.2.2.2.3 | **Profile Import Executor**<br/>*Profiles Created* | `background_agents/monitoring/profile_import_executor.py` | `ProfileImportExecutorAgent.profiles_created` | An attribute that is incremented inside the `_process_client` method upon the successful creation of a user profile. The `get_agent_metrics` method returns this value. |
| 1.2.2.2.4 | **Profile Import Executor**<br/>*Success Rate* | `background_agents/monitoring/profile_import_executor.py` | `ProfileImportExecutorAgent.get_agent_metrics()`| This method calculates the success rate on the fly by dividing `profiles_created` by the total number of attempts (`total_executions`). |
| 1.2.2.3.3 | **Self-Healing Autopatch**<br/>*Patches Applied*| `background_agents/monitoring/self_healing_agent.py` | `SelfHealingAutopatchAgent.patches_applied`| An attribute that is incremented within the `_run_patch` method whenever a database patch is applied successfully. |
| 1.2.2.4.3 | **Performance Monitor**<br/>*Optimizations Suggested*| `background_agents/monitoring/performance_monitor.py` | `PerformanceMonitorAgent.optimization_history` | A list of optimization records. The UI displays the `len()` of this list to show the total count of suggestions. |
| 1.2.2.4.4 | **Performance Monitor**<br/>*Anomalies Detected*| `background_agents/monitoring/performance_monitor.py` | `PerformanceMonitorAgent.anomaly_history` | A `deque` that stores detected anomaly events. The UI displays the `len()` of this history. |

### 1.2.3 System Information Expander

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.3 | Configuration | `background_agents_dashboard.py` | `dashboard.coordinator`, `dashboard.shared_state` | Data is sourced directly from the coordinator (e.g., `is_running`, `len(agents)`) and the shared state (`get_active_agents()`) within the dashboard's main rendering loop. |
| 1.2.3 | Environment | `background_agents_dashboard.py` | `os`, `sys` | Standard library modules are used to get the environment variables (`os.getenv`), platform (`sys.platform`), and Python version (`sys.version`). |
| 1.2.3 | System Stats | `background_agents_dashboard.py` | `psutil` | The `psutil` library is called directly to get the current system-wide CPU and memory usage percentages. | 
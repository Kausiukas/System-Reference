# UI Data Mapping (ID: 1)

This document maps the UI components defined in `background_agents_dashboard_ui.md` to their data sources. The new architecture centralizes all data fetching into a single function for simplicity and consistency.

**Primary Data Source Function**: `get_dashboard_data()` in `background_agents_dashboard.py`.

This function is the sole entry point for retrieving data for the UI. It connects to the `SharedState` in read-only mode and fetches all necessary information.

---
## 1.1 Sidebar (Control Panel)

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.1.1 | Info Message | `background_agents_dashboard.py` | `st.info()` | A static informational message. No external data is fetched. |
| 1.1.2.1 | LangSmith API Key | `background_agents_dashboard.py` | `os.getenv("LANGCHAIN_API_KEY")` | The value of the environment variable is read directly. This is for display only. |
| 1.1.2.2 | Project Name | `background_agents_dashboard.py` | `os.getenv("LANGCHAIN_PROJECT")` | The value of the environment variable is read directly. This is for display only. |
| 1.1.3.x | Auto Refresh | `background_agents_dashboard.py` | `st.checkbox`, `st.selectbox` | Standard Streamlit components that control the UI's refresh loop (`time.sleep` and `st.rerun`). |

---
## 1.2 Main Dashboard Area

### Data Flow for Main Area:
`main_dashboard()` -> `get_dashboard_data()` -> `SharedState` -> UI Components

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.2 | Status Banner | `background_agents_dashboard.py` | `datetime.now()` | A simple timestamp generated each time the dashboard refreshes. |
| 1.2.3 | Agent Status Section | `background_agents_dashboard.py` | `get_dashboard_data()` -> `shared_state.get_active_agents()` | The list of active agents is fetched from `SharedState`. The `render_agent_cards()` function iterates through this list to display a card for each agent. The `agent_name`, `state`, `uptime`, and `errors` are all pulled from the dictionary representing each agent in this list. |
| 1.2.4 | System Info: Total Agents | `background_agents_dashboard.py` | `get_dashboard_data()` -> `shared_state.get_all_known_agents()` | The total number of unique agents that have ever registered. This is calculated by getting the `len()` of the list returned by this function. |
| 1.2.4 | System Info: Active Agents | `background_agents_dashboard.py` | `get_dashboard_data()` -> `shared_state.get_active_agents()` | The number of currently active agents, calculated by `len()` of the list of active agents. |
| 1.2.4 | System Info: Environment | `background_agents_dashboard.py` | `os`, `sys` | Standard library modules are used to get the API key status, project name, platform, and Python version for display. |
| 1.2.4 | System Info: Dashboard Stats | `background_agents_dashboard.py` | `psutil` | The `psutil` library is called directly by the dashboard to get its own process's CPU and memory usage. This is a local stat and is not fetched from `SharedState`. | 
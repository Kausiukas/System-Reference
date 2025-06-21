# Background Agents Dashboard - UI Schema (ID: 1)

This document outlines the user interface components and layout for the `background_agents_dashboard.py` Streamlit application.

---

## 1.1 Sidebar (Control Panel)

The sidebar is organized into several sections.

### 1.1.1 Quick Status

- **Component**: `st.empty()` placeholder.
- **Description**: Displays the overall status of the agent system.

### 1.1.2 Configuration

- **1.1.2.1 LangSmith API Key**: `st.text_input` (type="password")
- **1.1.2.2 Project Name**: `st.text_input`

### 1.1.3 Auto Refresh

- **1.1.3.1 Enable auto-refresh**: `st.checkbox`
- **1.1.3.2 Refresh interval (s)**: `st.selectbox`

### 1.1.4 Demo Mode

- **1.1.4.1 Enable demo mode**: `st.checkbox`
  - **Behavior**: This control is disabled after the system has been initialized.

### 1.1.5 System Controls

- **1.1.5.1 Initialize/Stop Button**: `st.button`

---

## 1.2 Main Dashboard Area

### 1.2.1 Header

- **Title**: `st.title("🤖 Background Agents Monitor")`
- **Status Banner**: `st.info()`

### 1.2.2 Agent Status Section

This section dynamically creates a container for each registered agent.

#### 1.2.2.1 LangSmith Bridge Agent
- **Title**: `st.subheader("LangSmith Bridge Agent")`
- **Metrics**:
    - **State**: Current `AgentState` (e.g., "ACTIVE").
    - **Uptime**: `agent.get_uptime()`.
    - **Traces Collected**: A running count of traces successfully sent to LangSmith.
    - **Errors**: A count of communication or data processing errors.
    - **Heartbeat**: ✅ / ❌ icon.

#### 1.2.2.2 Profile Import Executor Agent
- **Title**: `st.subheader("Profile Import Executor Agent")`
- **Metrics**:
    - **State**: Current `AgentState`.
    - **Uptime**: `agent.get_uptime()`.
    - **Profiles Created**: A count of profiles successfully imported in the current session.
    - **Success Rate**: The percentage of successful imports.
    - **Errors**: A count of import failures.
    - **Heartbeat**: ✅ / ❌ icon.

#### 1.2.2.3 Self-Healing Autopatch Agent
- **Title**: `st.subheader("Self-Healing Autopatch Agent")`
- **Metrics**:
    - **State**: Current `AgentState`.
    - **Uptime**: `agent.get_uptime()`.
    - **Patches Applied**: A count of successful autopatches.
    - **Errors**: A count of patching failures.
    - **Heartbeat**: ✅ / ❌ icon.

#### 1.2.2.4 Performance Monitor Agent
- **Title**: `st.subheader("Performance Monitor Agent")`
- **Metrics**:
    - **State**: Current `AgentState`.
    - **Uptime**: `agent.get_uptime()`.
    - **Optimizations Suggested**: A count of performance optimizations identified.
    - **Anomalies Detected**: A count of detected performance anomalies.
    - **Heartbeat**: ✅ / ❌ icon.

### 1.2.3 System Information Expander

- **Component**: `st.expander("🔧 System Information")`
- **Content**: Organized into three columns:
    - **Configuration**: Coordinator status, total/active agents.
    - **Environment**: API key status, project name, OS, Python version.
    - **System Stats**: CPU and Memory usage.

---

## 2. UI Visualization

The following diagram illustrates the component hierarchy, including agent-specific details.

```mermaid
graph TD
    A1["<br/>🤖<br/>1. Dashboard UI<br/>"] --> B1["<br/>🔩<br/>1.1 Sidebar<br/>"];
    A1 --> C1["<br/>🖥️<br/>1.2 Main Area<br/>"];

    subgraph "1.1 Sidebar"
        B1 --> B1.1["1.1.1<br/>Quick Status"];
        B1 --> B1.2["1.1.2<br/>Configuration"];
        B1 --> B1.3["1.1.3<br/>Auto Refresh"];
        B1 --> B1.4["1.1.4<br/>Demo Mode"];
        B1 --> B1.5["1.1.5<br/>System Controls"];
    end

    subgraph "1.2 Main Area"
        C1 --> C1.1["1.2.1 Header"];
        C1 --> C1.2["1.2.2 ❤️<br/>Agent Status"];
        C1 --> C1.3["1.2.3 🔧<br/>System Info"];
    end

    subgraph "1.2.2 Agent Status"
        C1.2 --> D1["1.2.2.1<br/>LangSmith Bridge"];
        C1.2 --> D2["1.2.2.2<br/>Profile Import Executor"];
        C1.2 --> D3["1.2.2.3<br/>Self-Healing Autopatch"];
        C1.2 --> D4["1.2.2.4<br/>Performance Monitor"];
    end
    
    subgraph "1.2.2.1 Metrics"
        D1 --> E1["1.2.2.1.1<br/>State"];
        D1 --> E2["1.2.2.1.2<br/>Uptime"];
        D1 --> E3["1.2.2.1.3<br/>Traces"];
        D1 --> E4["1.2.2.1.4<br/>Errors"];
    end
    
    subgraph "1.2.2.2 Metrics"
        D2 --> F1["1.2.2.2.1<br/>State"];
        D2 --> F2["1.2.2.2.2<br/>Uptime"];
        D2 --> F3["1.2.2.2.3<br/>Profiles"];
        D2 --> F4["1.2.2.2.4<br/>Rate %"];
    end
``` 
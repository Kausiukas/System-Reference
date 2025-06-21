# Background Agents System

This project implements a sophisticated, multi-agent system designed for real-time data processing, monitoring, and optimization. The system is built with a clear separation of concerns, featuring background agents that perform specific tasks, a central coordinator for state management, and a web-based dashboard for monitoring.

## Core Concepts

-   **`SharedState`**: A central SQLite-based database (`shared_state.db`) that acts as the single source of truth for the entire system. It facilitates communication and state-sharing between all components in a concurrent-safe manner.

-   **`AgentCoordinator`**: The central nervous system. This component is responsible for registering agents, collecting heartbeats, and orchestrating system-wide tasks. It is the primary writer to the `shared_state.db`.

-   **Background Agents**: Specialized processes that perform discrete tasks. Examples include the `LangSmithBridgeAgent`, which pulls data from LangSmith, or a `PerformanceMonitorAgent`. Agents run independently and communicate their status back to the coordinator.

-   **Read-Only Monitor**: The system includes a Streamlit-based dashboard (`background_agents_dashboard.py`) that provides a real-time, read-only view into the system's state by connecting to the `shared_state.db`.

## System Architecture

The system follows a decoupled launcher/monitor architecture to ensure stability and prevent concurrency issues.

1.  **Launcher (`launch_background_agents.py`)**: This is the primary entry point for starting the entire agent system. It initializes the `SharedState` database, starts the `AgentCoordinator`, and launches all defined background agents. This process is designed to run persistently in a terminal.

2.  **Monitor (`background_agents_dashboard.py`)**: This is a separate Streamlit application that provides a UI for monitoring the system. It connects to the `shared_state.db` in a **read-only** mode, ensuring it cannot interfere with the live agent system.

This separation prevents the UI from causing database locks or accidentally restarting agents, which was a critical issue in previous versions.

## Getting Started

### 1. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Environment Configuration

Create a `.env` file in the root of the project and add the necessary environment variables. At a minimum, you will need the LangSmith API key for the bridge agent to function.

```
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="your_langsmith_project_name"
# Optional: Specify a custom path for the database
# SHARED_STATE_SQLITE="data/shared_state.db"
```

### 3. Running the System

To run the system, you will need **two separate terminals**.

**Terminal 1: Launch the Agent System**

In your first terminal, run the launcher script. This will start the coordinator and all background agents. Leave this terminal running.

```bash
python launch_background_agents.py
```

You should see log output indicating that the system has initialized, agents have been registered, and heartbeats are being sent.

**Terminal 2: Launch the Monitoring Dashboard**

In your second terminal, launch the Streamlit dashboard.

```bash
streamlit run background_agents_dashboard.py
```

This will open the monitoring dashboard in your web browser. The dashboard will connect to the `shared_state.db` and display the status of the agents running in your first terminal.

## Key Components

-   `src/`: Contains the core source code for agents, the coordinator, and other utilities. (Note: This is a placeholder; the actual structure is more complex).
-   `launch_background_agents.py`: The entry point for starting the agent system.
-   `background_agents_dashboard.py`: The Streamlit-based monitoring UI.
-   `shared_state.db`: The SQLite database for shared state. It will be created when you run the launcher for the first time.
-   `docs/`: Contains detailed documentation on various aspects of the system. (Note: This is a suggestion, you might need to create this folder).

## Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

MIT License
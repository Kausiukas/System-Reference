# PostgreSQL-Based UI Data Mapping

**Enterprise Dashboard Data Architecture**

This document maps the UI components defined in `background_agents_dashboard_ui.md` to their PostgreSQL-based data sources. The enterprise architecture centralizes all data fetching through PostgreSQL with advanced analytics and business intelligence.

**Primary Data Source Function**: `get_dashboard_data()` in `background_agents_dashboard.py` - connects to PostgreSQL-backed `SharedState` for comprehensive enterprise monitoring.

---

## 🎯 Enterprise Data Architecture

### PostgreSQL-Integrated Data Flow

```mermaid
graph TD
    subgraph "UI Components"
        SIDEBAR[Sidebar Control Panel]
        MAIN[Main Dashboard Area]
        AGENT_CARDS[Agent Status Cards]
        METRICS[System Metrics]
        ANALYTICS[Business Analytics]
    end
    
    subgraph "Data Layer"
        GDD[get_dashboard_data()]
        SS[SharedState]
        PA[PostgreSQLAdapter]
    end
    
    subgraph "PostgreSQL Database"
        AGENTS[agents table]
        HEARTBEATS[agent_heartbeats table]
        METRICS_TABLE[performance_metrics table]
        EVENTS[system_events table]
        ANALYTICS_TABLE[business_analytics table]
    end
    
    SIDEBAR --> GDD
    MAIN --> GDD
    AGENT_CARDS --> GDD
    METRICS --> GDD
    ANALYTICS --> GDD
    
    GDD --> SS
    SS --> PA
    PA --> AGENTS
    PA --> HEARTBEATS
    PA --> METRICS_TABLE
    PA --> EVENTS
    PA --> ANALYTICS_TABLE
```

---

## 1.1 Sidebar (Enterprise Control Panel)

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.1.1 | Enterprise Info Message | `background_agents_dashboard.py` | `st.info()` | Enterprise system overview with PostgreSQL backend status |
| 1.1.2.1 | LangSmith API Key | `background_agents_dashboard.py` | `os.getenv("LANGCHAIN_API_KEY")` | Enterprise LLM monitoring configuration (display only) |
| 1.1.2.2 | Project Name | `background_agents_dashboard.py` | `os.getenv("LANGCHAIN_PROJECT")` | Enterprise project identification (display only) |
| 1.1.2.3 | PostgreSQL Status | `background_agents_dashboard.py` | `shared_state.get_connection_status()` | Live PostgreSQL database connection health |
| 1.1.3.x | Auto Refresh Controls | `background_agents_dashboard.py` | `st.checkbox`, `st.selectbox` | Enterprise dashboard refresh controls with real-time updates |

---

## 1.2 Main Dashboard Area (Enterprise Monitoring)

### PostgreSQL-Based Data Flow for Main Area:
`main_dashboard()` → `get_dashboard_data()` → `SharedState` → `PostgreSQLAdapter` → PostgreSQL Database → Enterprise UI Components

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.1 | Enterprise System Banner | `background_agents_dashboard.py` | `datetime.now()`, `shared_state.get_system_health()` | Real-time system status with PostgreSQL health metrics |
| 1.2.2 | Business Intelligence Panel | `background_agents_dashboard.py` | `get_dashboard_data()` → `shared_state.get_business_metrics()` | Enterprise KPIs: cost savings, ROI, operational efficiency from PostgreSQL analytics |
| 1.2.3 | Agent Status Section | `background_agents_dashboard.py` | `get_dashboard_data()` → `shared_state.get_registered_agents()` | Complete agent ecosystem from PostgreSQL `agents` table with health scores, business impact, and performance analytics |
| 1.2.4 | Performance Analytics | `background_agents_dashboard.py` | `get_dashboard_data()` → `shared_state.get_performance_analytics()` | Advanced performance metrics from PostgreSQL `performance_metrics` table including trends, optimization opportunities |
| 1.2.5 | Cost Optimization Insights | `background_agents_dashboard.py` | `get_dashboard_data()` → `shared_state.get_cost_analytics()` | Real-time cost analysis and optimization recommendations from PostgreSQL business intelligence |

### Enterprise System Information

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.2.4.1 | Total Registered Agents | `background_agents_dashboard.py` | `shared_state.get_all_registered_agents()` | Complete count from PostgreSQL `agents` table |
| 1.2.4.2 | Active Agents | `background_agents_dashboard.py` | `shared_state.get_active_agents()` | Real-time active count from PostgreSQL with health validation |
| 1.2.4.3 | Enterprise Environment | `background_agents_dashboard.py` | `os`, `sys`, `shared_state.get_environment_info()` | Production environment details including PostgreSQL version, connection pool status |
| 1.2.4.4 | Database Performance | `background_agents_dashboard.py` | `shared_state.get_database_performance()` | PostgreSQL performance metrics: connection count, query performance, resource usage |
| 1.2.4.5 | Business Metrics | `background_agents_dashboard.py` | `shared_state.get_business_intelligence()` | Executive dashboard metrics: monthly savings, ROI, efficiency gains from PostgreSQL analytics |

---

## 1.3 Advanced Enterprise Features

### Real-Time Business Intelligence

| UI ID | UI Element | Source File | Source Object/Function | Data Description |
|---|---|---|---|---|
| 1.3.1 | Executive Summary | `background_agents_dashboard.py` | `shared_state.get_executive_summary()` | High-level business impact metrics from PostgreSQL business intelligence tables |
| 1.3.2 | Cost Impact Analysis | `background_agents_dashboard.py` | `shared_state.get_cost_impact_analysis()` | Real-time cost savings and optimization opportunities from PostgreSQL analytics |
| 1.3.3 | Performance Trends | `background_agents_dashboard.py` | `shared_state.get_performance_trends()` | Historical performance analysis from PostgreSQL time-series data |
| 1.3.4 | Health Score Analytics | `background_agents_dashboard.py` | `shared_state.get_health_analytics()` | Comprehensive system health scoring from PostgreSQL health monitoring |
| 1.3.5 | Recovery Statistics | `background_agents_dashboard.py` | `shared_state.get_recovery_statistics()` | Automated recovery success rates and business impact mitigation from PostgreSQL events |

### Enterprise Integration Data Sources

| Data Category | PostgreSQL Table | Primary Function | Update Frequency |
|---|---|---|---|
| Agent Registration | `agents` | `get_registered_agents()` | Real-time |
| Health Monitoring | `agent_heartbeats` | `get_agent_health_data()` | Every 30 seconds |
| Performance Metrics | `performance_metrics` | `get_performance_analytics()` | Every 60 seconds |
| Business Intelligence | `business_analytics` | `get_business_metrics()` | Every 5 minutes |
| System Events | `system_events` | `get_system_events()` | Real-time |
| Cost Analytics | `cost_analytics` | `get_cost_optimization_data()` | Every 15 minutes |

---

## 🔧 Enterprise Configuration

### PostgreSQL Connection Configuration

| Configuration Item | Source | Description |
|---|---|---|
| Database URL | `config_template.env` → `DATABASE_URL` | PostgreSQL connection string with enterprise features |
| Connection Pool | `postgresql_adapter.py` | High-performance connection pooling for enterprise scale |
| Health Monitoring | `monitoring.yml` | Real-time database health and performance monitoring |
| Business Intelligence | `shared_state.py` | Advanced analytics and reporting configuration |

### Data Refresh Strategy

| Component | Refresh Rate | Optimization Strategy |
|---|---|---|
| Agent Status Cards | 30 seconds | Real-time heartbeat validation |
| Performance Metrics | 60 seconds | Batch processing with caching |
| Business Analytics | 5 minutes | Aggregated calculations with PostgreSQL views |
| Executive Reports | 15 minutes | Complex analytics with materialized views |
| System Health | 10 seconds | Lightweight health checks with connection pooling |

This enterprise PostgreSQL-based UI data mapping provides comprehensive data architecture supporting real-time monitoring, advanced analytics, and business intelligence with quantifiable performance characteristics and scalability. 
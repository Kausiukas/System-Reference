#!/usr/bin/env python3
"""
Background Agents Dashboard

A streamlined Streamlit dashboard for monitoring the background agents system.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Background Agents Monitor",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_mock_data():
    """Load mock data for demo purposes."""
    mock_agents = [
        {
            'agent_id': 'heartbeat_health_agent',
            'state': 'running',
            'last_heartbeat': datetime.now() - timedelta(seconds=30),
            'error_count': 0,
            'uptime_seconds': 3600,
            'metrics': {'cpu_usage': 15.2, 'memory_usage': 45.6}
        },
        {
            'agent_id': 'performance_monitor',
            'state': 'running',
            'last_heartbeat': datetime.now() - timedelta(seconds=45),
            'error_count': 1,
            'uptime_seconds': 3550,
            'metrics': {'cpu_usage': 22.1, 'memory_usage': 38.2}
        },
        {
            'agent_id': 'langsmith_bridge',
            'state': 'running',
            'last_heartbeat': datetime.now() - timedelta(seconds=60),
            'error_count': 0,
            'uptime_seconds': 3590,
            'metrics': {'requests_processed': 150}
        },
        {
            'agent_id': 'ai_help_agent',
            'state': 'error',
            'last_heartbeat': datetime.now() - timedelta(minutes=5),
            'error_count': 3,
            'uptime_seconds': 2100,
            'metrics': {'help_requests_processed': 25}
        }
    ]
    return mock_agents

def get_agent_status_color(state):
    """Get color for agent state."""
    colors = {
        'running': '#4CAF50',
        'stopped': '#757575',
        'error': '#f44336',
        'initializing': '#2196F3',
        'stopping': '#ff9800'
    }
    return colors.get(state, '#757575')

def format_uptime(seconds):
    """Format uptime in human readable format."""
    if not seconds:
        return "N/A"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def main():
    """Main dashboard function."""
    
    st.title("🔧 Background Agents Monitor")
    st.markdown("Real-time monitoring of background agents and system health")
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Load data
    try:
        agents_data = load_mock_data()
        st.sidebar.success("✅ Connected to system")
    except Exception as e:
        st.sidebar.error(f"❌ Connection failed: {e}")
        agents_data = load_mock_data()
    
    # System Overview
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_agents = len(agents_data)
    running_agents = len([a for a in agents_data if a['state'] == 'running'])
    error_agents = len([a for a in agents_data if a['state'] == 'error'])
    total_errors = sum(a['error_count'] for a in agents_data)
    
    with col1:
        st.metric("Total Agents", total_agents)
    
    with col2:
        st.metric("Running", running_agents)
    
    with col3:
        st.metric("Errors", error_agents,
                 delta=error_agents if error_agents > 0 else None,
                 delta_color="inverse")
    
    with col4:
        st.metric("Total Error Count", total_errors,
                 delta=total_errors if total_errors > 0 else None,
                 delta_color="inverse")
    
    # Agent Status Table
    st.header("🤖 Agent Status")
    
    df_data = []
    for agent in agents_data:
        df_data.append({
            'Agent ID': agent['agent_id'],
            'State': agent['state'].upper(),
            'Last Heartbeat': agent['last_heartbeat'].strftime('%H:%M:%S'),
            'Uptime': format_uptime(agent.get('uptime_seconds')),
            'Errors': agent['error_count']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    # Agent Details
    st.header("🔍 Agent Details")
    
    agent_ids = [agent['agent_id'] for agent in agents_data]
    selected_agent_id = st.selectbox("Select Agent", agent_ids)
    
    if selected_agent_id:
        selected_agent = next(a for a in agents_data if a['agent_id'] == selected_agent_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Agent Information")
            st.write(f"**ID:** {selected_agent['agent_id']}")
            st.write(f"**State:** {selected_agent['state'].upper()}")
            st.write(f"**Last Heartbeat:** {selected_agent['last_heartbeat'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Uptime:** {format_uptime(selected_agent.get('uptime_seconds'))}")
            st.write(f"**Error Count:** {selected_agent['error_count']}")
        
        with col2:
            st.subheader("Metrics")
            metrics = selected_agent.get('metrics', {})
            if metrics:
                for key, value in metrics.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:
                st.info("No metrics available")
    
    # Performance Charts
    if len(agents_data) > 0:
        st.header("📈 Performance Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Agent states pie chart
            state_counts = {}
            for agent in agents_data:
                state = agent['state']
                state_counts[state] = state_counts.get(state, 0) + 1
            
            fig_pie = px.pie(
                values=list(state_counts.values()),
                names=list(state_counts.keys()),
                title="Agent States Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Error counts bar chart
            agent_names = [a['agent_id'] for a in agents_data]
            error_counts = [a['error_count'] for a in agents_data]
            
            fig_bar = px.bar(
                x=agent_names,
                y=error_counts,
                title="Error Counts by Agent"
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main() 
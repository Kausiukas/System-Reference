#!/usr/bin/env python3
"""
Background Agents Dashboard

Enterprise monitoring dashboard with comprehensive PostgreSQL integration,
real-time agent status, performance analytics, and business intelligence.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import json
from dotenv import load_dotenv

# Import coordination system
from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter, ConnectionConfig


class DashboardDataProvider:
    """Data provider for dashboard with PostgreSQL integration"""
    
    def __init__(self):
        self.shared_state = None
        self.postgresql_adapter = None
        self.connection_initialized = False
        
    async def initialize_connection(self):
        """Initialize database connection"""
        
        if self.connection_initialized:
            return
            
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            # Create connection configuration
            connection_config = ConnectionConfig(
                host=os.getenv('POSTGRESQL_HOST', 'localhost'),
                port=int(os.getenv('POSTGRESQL_PORT', '5432')),
                database=os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
                user=os.getenv('POSTGRESQL_USER', 'postgres'),
                password=os.getenv('POSTGRESQL_PASSWORD', ''),
                min_connections=5,
                max_connections=10
            )
            
            self.postgresql_adapter = PostgreSQLAdapter(connection_config)
            await self.postgresql_adapter.initialize()
            
            # Initialize shared state
            self.shared_state = SharedState(self.postgresql_adapter)
            await self.shared_state.initialize()
            
            self.connection_initialized = True
            
        except Exception as e:
            st.error(f"Failed to initialize database connection: {e}")
            raise
            
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        
        await self.initialize_connection()
        
        try:
            # Get system health
            health_data = await self.shared_state.get_system_health()
            
            # Get registered agents
            agents = await self.shared_state.get_registered_agents()
            
            # Get recent events
            recent_events = await self.shared_state.get_system_events(hours=1)
            
            # Get performance summary
            performance_summary = await self.shared_state.get_system_performance_summary()
            
            return {
                'health_data': health_data,
                'agents': agents,
                'recent_events': recent_events,
                'performance_summary': performance_summary
            }
            
        except Exception as e:
            st.error(f"Failed to get system overview: {e}")
            return {}
            
    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed information for specific agent"""
        
        await self.initialize_connection()
        
        try:
            # Get agent status
            agent_status = await self.shared_state.get_agent_status(agent_id)
            
            # Get recent heartbeats
            recent_heartbeats = await self.shared_state.get_recent_heartbeats(agent_id, minutes=60)
            
            # Get agent health data
            health_data = await self.shared_state.get_agent_health_data(agent_id, hours=24)
            
            # Get performance metrics
            performance_metrics = await self.shared_state.get_performance_metrics(agent_id=agent_id, hours=24)
            
            return {
                'agent_status': agent_status,
                'recent_heartbeats': recent_heartbeats,
                'health_data': health_data,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            st.error(f"Failed to get agent details for {agent_id}: {e}")
            return {}
            
    async def get_performance_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance analytics data"""
        
        await self.initialize_connection()
        
        try:
            # Get performance metrics
            performance_metrics = await self.shared_state.get_performance_metrics(hours=hours)
            
            # Get business metrics
            business_metrics = await self.shared_state.get_business_metrics(hours=hours)
            
            # Get system events for analysis
            system_events = await self.shared_state.get_system_events(hours=hours)
            
            return {
                'performance_metrics': performance_metrics,
                'business_metrics': business_metrics,
                'system_events': system_events
            }
            
        except Exception as e:
            st.error(f"Failed to get performance analytics: {e}")
            return {}


@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_system_overview_cached():
    """Cached system overview data"""
    try:
        data_provider = DashboardDataProvider()
        return asyncio.run(data_provider.get_system_overview())
    except Exception as e:
        st.error(f"Error getting system overview: {e}")
        return {}


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_performance_analytics_cached(hours: int = 24):
    """Cached performance analytics data"""
    try:
        data_provider = DashboardDataProvider()
        return asyncio.run(data_provider.get_performance_analytics(hours))
    except Exception as e:
        st.error(f"Error getting performance analytics: {e}")
        return {}


def create_system_health_card(health_data: Dict[str, Any]):
    """Create system health status card"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        health_score = health_data.get('overall_health_score', 0)
        health_color = "green" if health_score > 80 else "orange" if health_score > 60 else "red"
        
        st.metric(
            label="System Health",
            value=f"{health_score:.1f}/100",
            delta=None,
            help="Overall system health score based on agent status, errors, and performance"
        )
        st.markdown(f"<span style='color: {health_color}'>●</span> {health_data.get('system_status', 'Unknown').title()}", unsafe_allow_html=True)
        
    with col2:
        total_agents = health_data.get('total_agents', 0)
        active_agents = health_data.get('active_agents', 0)
        
        st.metric(
            label="Active Agents",
            value=f"{active_agents}/{total_agents}",
            delta=None,
            help="Number of currently active agents out of total registered agents"
        )
        
        agent_percentage = (active_agents / max(total_agents, 1)) * 100
        agent_color = "green" if agent_percentage > 80 else "orange" if agent_percentage > 50 else "red"
        st.markdown(f"<span style='color: {agent_color}'>●</span> {agent_percentage:.1f}% Active", unsafe_allow_html=True)
        
    with col3:
        recent_errors = health_data.get('recent_errors', 0)
        
        st.metric(
            label="Recent Errors",
            value=recent_errors,
            delta=None,
            help="Number of errors in the last hour"
        )
        
        error_color = "green" if recent_errors == 0 else "orange" if recent_errors < 5 else "red"
        error_status = "Normal" if recent_errors == 0 else "Some Issues" if recent_errors < 5 else "Critical"
        st.markdown(f"<span style='color: {error_color}'>●</span> {error_status}", unsafe_allow_html=True)
        
    with col4:
        db_health = health_data.get('database_health', {})
        db_status = db_health.get('status', 'unknown')
        
        st.metric(
            label="Database Status",
            value=db_status.title(),
            delta=None,
            help="PostgreSQL database connection and performance status"
        )
        
        db_color = "green" if db_status == 'healthy' else "red"
        response_time = db_health.get('response_time_seconds', 0)
        st.markdown(f"<span style='color: {db_color}'>●</span> {response_time:.3f}s response", unsafe_allow_html=True)


def create_agents_overview_table(agents: List[Dict[str, Any]]):
    """Create agents overview table"""
    
    if not agents:
        st.warning("No agents found in the system")
        return
        
    # Prepare data for table
    agent_data = []
    for agent in agents:
        agent_data.append({
            'Agent ID': agent.get('agent_id', 'Unknown'),
            'Name': agent.get('agent_name', 'Unknown'),
            'Type': agent.get('agent_type', 'Unknown'),
            'State': agent.get('state', 'Unknown'),
            'Last Seen': agent.get('last_seen', 'Never'),
            'Capabilities': ', '.join(agent.get('capabilities', []))
        })
        
    # Create DataFrame
    df = pd.DataFrame(agent_data)
    
    # Style the dataframe
    def style_state(val):
        color = {
            'active': 'background-color: #d4edda; color: #155724',
            'inactive': 'background-color: #f8d7da; color: #721c24',
            'error': 'background-color: #f5c6cb; color: #721c24',
            'maintenance': 'background-color: #fff3cd; color: #856404'
        }.get(val.lower(), '')
        return color
        
    styled_df = df.style.map(style_state, subset=['State'])
    
    st.dataframe(styled_df, use_container_width=True, height=300)


def create_performance_charts(performance_data: Dict[str, Any]):
    """Create performance monitoring charts"""
    
    performance_metrics = performance_data.get('performance_metrics', [])
    
    if not performance_metrics:
        st.warning("No performance metrics available")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(performance_metrics)
    
    if df.empty:
        st.warning("No performance data to display")
        return
        
    # Convert timestamp column
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # Create performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Processing Time Trends")
        
        processing_time_df = df[df['metric_name'] == 'processing_time'].copy()
        
        if not processing_time_df.empty:
            fig = px.line(
                processing_time_df,
                x='timestamp',
                y='metric_value',
                color='agent_id',
                title='Agent Processing Times',
                labels={'metric_value': 'Processing Time (seconds)', 'timestamp': 'Time'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No processing time data available")
            
    with col2:
        st.subheader("Error Rate Monitoring")
        
        error_rate_df = df[df['metric_name'] == 'error_count'].copy()
        
        if not error_rate_df.empty:
            # Aggregate error counts by hour
            error_rate_df['hour'] = error_rate_df['timestamp'].dt.floor('H')
            hourly_errors = error_rate_df.groupby('hour')['metric_value'].sum().reset_index()
            
            fig = px.bar(
                hourly_errors,
                x='hour',
                y='metric_value',
                title='Error Count by Hour',
                labels={'metric_value': 'Error Count', 'hour': 'Hour'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No error data available")


def create_business_intelligence_dashboard(performance_data: Dict[str, Any]):
    """Create business intelligence dashboard"""
    
    business_metrics = performance_data.get('business_metrics', [])
    
    if not business_metrics:
        st.warning("No business metrics available")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(business_metrics)
    
    if df.empty:
        st.warning("No business data to display")
        return
        
    # Convert timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # Business metrics overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Cost optimization metrics
        cost_metrics = df[df['metric_category'] == 'cost_optimization'] if 'metric_category' in df.columns else df[df.get('category', '') == 'cost_optimization']
        if not cost_metrics.empty:
            # Use metric_value column which exists in the actual database schema
            if 'metric_value' in df.columns:
                total_cost_impact = cost_metrics['metric_value'].sum()
            else:
                total_cost_impact = 0
        else:
            total_cost_impact = 0
        st.metric(
            label="Cost Impact",
            value=f"${total_cost_impact:,.2f}",
            help="Total cost impact from optimization efforts"
        )
            
    with col2:
        # Revenue impact metrics
        revenue_metrics = df[df['metric_category'] == 'revenue'] if 'metric_category' in df.columns else df[df.get('category', '') == 'revenue']
        if not revenue_metrics.empty:
            # Use metric_value column which exists in the actual database schema
            if 'metric_value' in df.columns:
                total_revenue_impact = revenue_metrics['metric_value'].sum()
            else:
                total_revenue_impact = 0
        else:
            total_revenue_impact = 0
        st.metric(
            label="Revenue Impact",
            value=f"${total_revenue_impact:,.2f}",
            help="Total revenue impact from system improvements"
        )
            
    with col3:
        # System efficiency
        efficiency_metrics = df[df['metric_name'] == 'efficiency_score']
        if not efficiency_metrics.empty:
            avg_efficiency = efficiency_metrics['metric_value'].mean()
            st.metric(
                label="System Efficiency",
                value=f"{avg_efficiency:.1f}%",
                help="Average system efficiency score"
            )
            
    # Business value trends
    st.subheader("Business Value Trends")
    
    # Group by category and date
    category_column = 'metric_category' if 'metric_category' in df.columns else 'category'
    if category_column in df.columns and 'metric_value' in df.columns:
        df['date'] = df['timestamp'].dt.date
        business_trends = df.groupby(['date', category_column])['metric_value'].sum().reset_index()
        
        if not business_trends.empty:
            fig = px.line(
                business_trends,
                x='date',
                y='metric_value',
                color=category_column,
                title='Business Metrics by Category',
                labels={'metric_value': 'Metric Value', 'date': 'Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def create_real_time_monitoring():
    """Create real-time monitoring section"""
    
    st.subheader("Real-time System Monitoring")
    
    # Create placeholder for real-time updates
    placeholder = st.empty()
    
    # Auto-refresh mechanism
    if st.button("🔄 Refresh Data", key="refresh_realtime"):
        st.rerun()
        
    with placeholder.container():
        # Get fresh data
        overview_data = get_system_overview_cached()
        
        if overview_data:
            # Real-time health indicators
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📊 Current Status")
                health_data = overview_data.get('health_data', {})
                health_score = health_data.get('overall_health_score', 0)
                
                # Create gauge chart for health score
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = health_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "System Health"},
                    delta = {'reference': 90},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown("### 🚀 Agent Activity")
                agents = overview_data.get('agents', [])
                active_count = len([a for a in agents if a.get('state') == 'active'])
                total_count = len(agents)
                
                # Create donut chart for agent status
                status_counts = {}
                for agent in agents:
                    state = agent.get('state', 'unknown')
                    status_counts[state] = status_counts.get(state, 0) + 1
                    
                if status_counts:
                    fig = px.pie(
                        values=list(status_counts.values()),
                        names=list(status_counts.keys()),
                        title="Agent Status Distribution",
                        hole=0.4
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
            with col3:
                st.markdown("### ⚠️ Recent Alerts")
                recent_events = overview_data.get('recent_events', [])
                error_events = [e for e in recent_events if e.get('severity') in ['ERROR', 'CRITICAL']]
                
                if error_events:
                    for event in error_events[:5]:  # Show last 5 errors
                        severity = event.get('severity', 'UNKNOWN')
                        event_type = event.get('event_type', 'Unknown')
                        timestamp = event.get('timestamp', 'Unknown')
                        
                        severity_color = {
                            'ERROR': '🔴',
                            'CRITICAL': '🔴',
                            'WARNING': '🟡',
                            'INFO': '🟢'
                        }.get(severity, '⚪')
                        
                        st.markdown(f"{severity_color} **{event_type}** - {timestamp}")
                else:
                    st.success("✅ No recent alerts")


def create_agent_detail_view():
    """Create detailed agent view"""
    
    st.subheader("Agent Details")
    
    # Get system overview for agent selection
    overview_data = get_system_overview_cached()
    agents = overview_data.get('agents', [])
    
    if not agents:
        st.warning("No agents available for detailed view")
        return
        
    # Agent selection
    agent_options = {agent['agent_id']: agent['agent_name'] for agent in agents}
    selected_agent_id = st.selectbox(
        "Select Agent for Details",
        options=list(agent_options.keys()),
        format_func=lambda x: f"{agent_options[x]} ({x})"
    )
    
    if selected_agent_id:
        # Get agent details
        try:
            data_provider = DashboardDataProvider()
            agent_details = asyncio.run(data_provider.get_agent_details(selected_agent_id))
            
            if agent_details:
                # Agent status overview
                agent_status = agent_details.get('agent_status', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Agent Information")
                    st.json(agent_status)
                    
                with col2:
                    st.markdown("#### Recent Activity")
                    
                    # Heartbeat trend
                    recent_heartbeats = agent_details.get('recent_heartbeats', [])
                    if recent_heartbeats:
                        heartbeat_times = [datetime.fromisoformat(hb.replace('Z', '+00:00')) for hb in recent_heartbeats]
                        
                        # Create heartbeat timeline
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=heartbeat_times,
                            y=[1] * len(heartbeat_times),
                            mode='markers',
                            marker=dict(size=10, color='green'),
                            name='Heartbeats',
                            text=[f"Heartbeat at {hb}" for hb in recent_heartbeats],
                            hovertemplate='%{text}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title="Recent Heartbeats",
                            xaxis_title="Time",
                            yaxis_title="",
                            yaxis=dict(showticklabels=False),
                            height=200
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No recent heartbeats found")
                        
                # Performance metrics for this agent
                performance_metrics = agent_details.get('performance_metrics', [])
                if performance_metrics:
                    st.markdown("#### Performance Metrics")
                    
                    df = pd.DataFrame(performance_metrics)
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        
                    # Group by metric name and create charts
                    metric_names = df['metric_name'].unique()
                    
                    for metric_name in metric_names[:3]:  # Show first 3 metrics
                        metric_data = df[df['metric_name'] == metric_name]
                        
                        fig = px.line(
                            metric_data,
                            x='timestamp',
                            y='metric_value',
                            title=f"{metric_name.replace('_', ' ').title()}",
                            labels={'metric_value': 'Value', 'timestamp': 'Time'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
        except Exception as e:
            st.error(f"Failed to load agent details: {e}")


def main():
    """Main dashboard application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Background Agents Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and header
    st.title("🤖 Background Agents Enterprise Dashboard")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a view",
        ["System Overview", "Real-time Monitoring", "Performance Analytics", "Business Intelligence", "Agent Details", "System Configuration"]
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
        
    # Main content based on selected page
    if page == "System Overview":
        st.header("📊 System Overview")
        
        overview_data = get_system_overview_cached()
        
        if overview_data:
            # System health cards
            health_data = overview_data.get('health_data', {})
            create_system_health_card(health_data)
            
            st.markdown("---")
            
            # Agents overview
            st.subheader("🤖 Agents Overview")
            agents = overview_data.get('agents', [])
            create_agents_overview_table(agents)
            
            st.markdown("---")
            
            # Recent system events
            st.subheader("📋 Recent System Events")
            recent_events = overview_data.get('recent_events', [])
            
            if recent_events:
                events_df = pd.DataFrame(recent_events)
                st.dataframe(events_df, use_container_width=True, height=300)
            else:
                st.info("No recent system events")
                
    elif page == "Real-time Monitoring":
        st.header("⚡ Real-time Monitoring")
        create_real_time_monitoring()
        
    elif page == "Performance Analytics":
        st.header("📈 Performance Analytics")
        
        # Time range selection
        time_range = st.selectbox(
            "Select time range",
            ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"],
            index=2
        )
        
        hours_map = {
            "Last 1 hour": 1,
            "Last 6 hours": 6,
            "Last 24 hours": 24,
            "Last 7 days": 168
        }
        
        hours = hours_map[time_range]
        performance_data = get_performance_analytics_cached(hours)
        
        if performance_data:
            create_performance_charts(performance_data)
        else:
            st.warning("No performance data available")
            
    elif page == "Business Intelligence":
        st.header("💼 Business Intelligence")
        
        performance_data = get_performance_analytics_cached(24)
        
        if performance_data:
            create_business_intelligence_dashboard(performance_data)
        else:
            st.warning("No business intelligence data available")
            
    elif page == "Agent Details":
        st.header("🔍 Agent Details")
        create_agent_detail_view()
        
    elif page == "System Configuration":
        st.header("⚙️ System Configuration")
        
        st.subheader("Database Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**PostgreSQL Settings**")
            st.code(f"""
Host: {os.getenv('POSTGRESQL_HOST', 'localhost')}
Port: {os.getenv('POSTGRESQL_PORT', '5432')}
Database: {os.getenv('POSTGRESQL_DATABASE', 'background_agents')}
Pool Size: {os.getenv('POSTGRESQL_POOL_SIZE', '10')}
            """)
            
        with col2:
            st.markdown("**Monitoring Settings**")
            st.code(f"""
Heartbeat Interval: {os.getenv('HEARTBEAT_INTERVAL', '60')}s
Performance Interval: {os.getenv('PERFORMANCE_INTERVAL', '120')}s
Health Check Timeout: {os.getenv('HEALTH_CHECK_TIMEOUT', '30')}s
Data Retention: {os.getenv('DATA_RETENTION_DAYS', '30')} days
            """)
            
        st.subheader("System Information")
        
        try:
            overview_data = get_system_overview_cached()
            if overview_data:
                health_data = overview_data.get('health_data', {})
                
                st.json({
                    "system_status": health_data.get('system_status'),
                    "overall_health_score": health_data.get('overall_health_score'),
                    "total_agents": health_data.get('total_agents'),
                    "active_agents": health_data.get('active_agents'),
                    "last_updated": health_data.get('last_updated')
                })
        except Exception as e:
            st.error(f"Failed to load system information: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Dashboard powered by **Background Agents Enterprise System** | "
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


if __name__ == "__main__":
    main() 
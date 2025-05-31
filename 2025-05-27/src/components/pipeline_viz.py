import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import altair as alt

def create_pipeline_chart(profiles: List[Dict[str, Any]]) -> None:
    """Create and display a sales pipeline visualization."""
    # Prepare data
    pipeline_data = []
    stages = ["lead", "qualified", "offered", "negotiating", "closed_won", "closed_lost"]
    stage_colors = {
        "lead": "#FFA07A",        # Light Salmon
        "qualified": "#98FB98",   # Pale Green
        "offered": "#87CEEB",     # Sky Blue
        "negotiating": "#DDA0DD", # Plum
        "closed_won": "#90EE90",  # Light Green
        "closed_lost": "#F08080"  # Light Coral
    }
    
    # Transform profiles into pipeline data
    for profile in profiles:
        pipeline_data.append({
            "client_id": profile["client_id"],
            "company_name": profile.get("company_name", "Unknown"),
            "stage": profile.get("sales_stage", "lead"),
            "last_updated": datetime.fromisoformat(profile.get("last_interaction", datetime.now().isoformat())),
            "value": float(profile.get("opportunity_value", 0)),
            "days_in_stage": (datetime.now() - datetime.fromisoformat(profile.get("last_interaction", datetime.now().isoformat()))).days
        })
    
    df = pd.DataFrame(pipeline_data)
    
    # Create main pipeline chart
    st.subheader("📊 Sales Pipeline Overview")
    
    # Stage distribution chart
    stage_counts = df["stage"].value_counts().reset_index()
    stage_counts.columns = ["stage", "count"]
    
    chart = alt.Chart(stage_counts).mark_bar().encode(
        x=alt.X("stage:N", sort=stages, title="Sales Stage"),
        y=alt.Y("count:Q", title="Number of Clients"),
        color=alt.Color("stage:N", scale=alt.Scale(domain=list(stage_colors.keys()), range=list(stage_colors.values()))),
        tooltip=["stage", "count"]
    ).properties(
        width=600,
        height=300,
        title="Distribution of Clients Across Sales Stages"
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Display detailed table
    st.subheader("📋 Pipeline Details")
    
    # Format data for display
    display_df = df[["company_name", "stage", "days_in_stage", "value"]].copy()
    display_df["value"] = display_df["value"].apply(lambda x: f"${x:,.2f}")
    display_df.columns = ["Company", "Stage", "Days in Stage", "Opportunity Value"]
    
    st.dataframe(
        display_df.style.background_gradient(subset=["Days in Stage"], cmap="YlOrRd"),
        use_container_width=True
    )
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_opportunities = len(df)
        st.metric("Total Opportunities", total_opportunities)
    
    with col2:
        total_value = df["value"].sum()
        st.metric("Total Pipeline Value", f"${total_value:,.2f}")
    
    with col3:
        avg_cycle = df["days_in_stage"].mean()
        st.metric("Avg Days in Stage", f"{avg_cycle:.1f}")
    
    # Stage transition analysis
    st.subheader("⏱️ Stage Duration Analysis")
    
    stage_duration = df.groupby("stage")["days_in_stage"].agg(["mean", "min", "max"]).round(1)
    stage_duration.columns = ["Average Days", "Minimum Days", "Maximum Days"]
    st.dataframe(stage_duration, use_container_width=True)

def create_email_html(email_content: str, client_profile: Dict[str, Any]) -> str:
    """Convert email content to HTML format with styling."""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 20px auto;
                padding: 20px;
            }}
            .header {{
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .footer {{
                border-top: 2px solid #eee;
                padding-top: 10px;
                margin-top: 20px;
                font-size: 0.9em;
                color: #666;
            }}
            .content {{
                padding: 20px 0;
            }}
            .metadata {{
                background: #f9f9f9;
                padding: 10px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Email Preview</h2>
            <p>Generated for: {client_profile.get("company_name", "Unknown Company")}</p>
        </div>
        
        <div class="content">
            {email_content.replace("\\n", "<br>")}
        </div>
        
        <div class="metadata">
            <p><strong>Client Information:</strong></p>
            <ul>
                <li>Company: {client_profile.get("company_name", "Unknown")}</li>
                <li>Stage: {client_profile.get("sales_stage", "Unknown")}</li>
                <li>Last Interaction: {client_profile.get("last_interaction", "N/A")}</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by Client Profile Builder</p>
            <p>Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </body>
    </html>
    """
    return html_template 
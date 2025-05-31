# streamlit_app.py

import streamlit as st
from langchain.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, END
from langsmith import Client as LangSmithClient
import uuid
import os
from dotenv import load_dotenv
from src.components.nodes import build_graph
from src.components.state import ClientState
from src.utils.helpers import ensure_directories, save_raw_content, load_client_profile
from src.components.pipeline_viz import create_pipeline_chart, create_email_html
from src.components.email_review import render_email_review_interface, EmailReviewSystem
import glob
import json
import base64
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize LangSmith
LANGSMITH_PROJECT = "client-profile-builder"
langsmith = LangSmithClient()

# Ensure required directories exist
ensure_directories()

# --- UI SETUP ---
st.set_page_config(page_title="Client Profile Builder", layout="wide")
st.title("🤖 Client Profile Builder (LangGraph + Streamlit + LangSmith)")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📝 Process Emails", "📊 Pipeline View", "🔍 Search Profiles", "✍️ Email Review"])

with tab1:
    # --- Mermaid Diagram Panel ---
    with st.expander("📊 Workflow Diagram (Mermaid)", expanded=True):
        st.markdown("""
    ```mermaid
    graph TD
        A[Export Emails] --> B[Preprocess + Chunk Content]
        B --> C[Search Long-Term Memory]
        C --> D[Summarize Client Status]
        D --> E[Update Client Profile State]
        E --> F[Sales Status Tracker]
        F --> G[Suggest Next Step]
        G --> H[Generate Email Content]
        H --> I[Save Output & Notify]
    ```
    """)

    # --- User Input ---
    st.header("📂 Upload Client Emails")
    uploaded_files = st.file_uploader(
        "Drop .msg, .txt or .pdf files",
        type=["msg", "txt", "pdf"],
        accept_multiple_files=True
    )

    # Client ID input
    client_id = st.text_input("Client ID (optional)", value="")

    st.header("🧠 Trigger Client Profile Builder")
    if st.button("Run Workflow") and uploaded_files:
        try:
            # Build the workflow graph
            workflow = build_graph()
            
            # Process each uploaded file
            for uploaded_file in uploaded_files:
                # Read file content
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                
                # Save raw content
                file_id = client_id or str(uuid.uuid4())
                save_raw_content(file_id, content, uploaded_file.type)
                
                # Initialize state
                initial_state = ClientState(
                    raw_content=content,
                    client_id=file_id
                )
                
                # Execute workflow
                run_id = str(uuid.uuid4())
                with st.spinner("Processing..."):
                    final_state = workflow.invoke(initial_state)
                
                # Store LangSmith URL
                st.session_state['run_url'] = f"https://smith.langchain.com/{os.getenv('LANGCHAIN_ORG_ID', '')}/projects/{LANGSMITH_PROJECT}/runs/{run_id}"
                
                # Display results
                st.success("✅ Run completed successfully!")
                st.write("🔗 LangSmith trace:", st.session_state['run_url'])
                
                # Display client profile
                st.subheader("📋 Generated Client Profile")
                profile_data = {
                    "client_id": final_state.client_id,
                    "company_name": final_state.company_name,
                    "contacts": final_state.contacts,
                    "needs": final_state.needs,
                    "sentiment": final_state.sentiment,
                    "sales_stage": final_state.sales_stage,
                    "next_steps": final_state.next_steps
                }
                st.json(profile_data)
                
                # Display generated email with HTML export
                if final_state.generated_email:
                    st.subheader("✉️ Generated Email Content")
                    
                    # Show email content
                    st.code(final_state.generated_email, language="markdown")
                    
                    # Save draft for review
                    review_system = EmailReviewSystem()
                    draft_id = review_system.save_draft(
                        final_state.generated_email,
                        load_client_profile(final_state.client_id),
                        {
                            "source_file": uploaded_file.name,
                            "processed_at": datetime.now().isoformat(),
                            "run_id": run_id
                        }
                    )
                    
                    st.info("📧 Email draft saved for review. Please check the 'Email Review' tab to review and approve.")
                    
                    # Generate HTML preview
                    html_content = create_email_html(
                        final_state.generated_email,
                        load_client_profile(final_state.client_id)
                    )
                    
                    # Create download button for HTML preview
                    b64 = base64.b64encode(html_content.encode()).decode()
                    filename = f"email_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">📥 Download Email Preview as HTML</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
    else:
        st.warning("⬆️ Upload at least one file and click 'Run Workflow'.")

with tab2:
    st.header("📈 Sales Pipeline Overview")
    
    # Load all client profiles
    profiles = []
    profile_files = glob.glob("data/profiles/*.json")
    
    for file_path in profile_files:
        try:
            with open(file_path, 'r') as f:
                profile = json.load(f)
                profiles.append(profile)
        except Exception as e:
            st.warning(f"Could not load profile from {file_path}: {str(e)}")
    
    if profiles:
        create_pipeline_chart(profiles)
    else:
        st.info("No client profiles found. Process some emails to see the pipeline visualization.")

with tab3:
    st.header("🔍 Search Client Profiles")
    
    # Search functionality
    search_term = st.text_input("Search by company name or client ID")
    
    if search_term:
        matching_profiles = []
        for profile in profiles:
            if (search_term.lower() in profile.get("company_name", "").lower() or
                search_term.lower() in profile.get("client_id", "").lower()):
                matching_profiles.append(profile)
        
        if matching_profiles:
            st.subheader(f"Found {len(matching_profiles)} matching profiles:")
            for profile in matching_profiles:
                with st.expander(f"📁 {profile.get('company_name', 'Unknown Company')}"):
                    st.json(profile)
        else:
            st.info("No matching profiles found.")

with tab4:
    render_email_review_interface()

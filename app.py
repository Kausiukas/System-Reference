import streamlit as st
import os
from pathlib import Path
import json
from typing import List, Tuple
import plotly.graph_objects as go
import numpy as np
import sys
import importlib.util
import time
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from metrics_tracker import get_metrics_tracker

load_dotenv()

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "D:/DATA/vectorstore")
LOCAL_VECTOR_DB_PATH = os.getenv("LOCAL_VECTOR_DB_PATH", "D:/GUI/vectorstore")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", str(DATA_DIR / "chat_history.json")))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def configure_logging():
    LOG_FILE = "app.log"
    root_logger = logging.getLogger()
    # Remove all handlers associated with the root logger object.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    logging.info("App startup initiated.")
    # Flush all handlers to ensure log file is written
    for handler in logging.getLogger().handlers:
        handler.flush()

# Call logging config at the top
configure_logging()

# Load db.py from DATA/utils
db_path = os.path.abspath('../DATA/utils/db.py')
spec = importlib.util.spec_from_file_location('db', db_path)
db = importlib.util.module_from_spec(spec)
sys.modules['db'] = db
spec.loader.exec_module(db)
get_main_vector_db = lambda: db.get_vector_db(VECTOR_DB_PATH, "documents")
get_local_vector_db = lambda: db.get_vector_db(LOCAL_VECTOR_DB_PATH, "documents")
search_documents = db.search_documents

# Constants
DATA_DIR = DATA_DIR
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = HISTORY_FILE
HEALTH_CHECK_INTERVAL = 30  # seconds

try:
    from llm import generate_answer
    OPENAI_ENABLED = True
except Exception:
    OPENAI_ENABLED = False

def check_vectorstore_health(vector_db, db_path):
    """Check if vectorstore connection is healthy by attempting a minimal handshake."""
    try:
        # Try a minimal operation: count or info or fetch a single doc by ID
        if hasattr(vector_db, "count"):
            count = vector_db.count()
            logging.info(f"Vectorstore at {db_path} responded to count: {count}")
        elif hasattr(vector_db, "info"):
            info = vector_db.info()
            logging.info(f"Vectorstore at {db_path} responded to info: {info}")
        else:
            # Fallback: try to fetch a single document with a minimal search
            results = vector_db.search("test", k=1, search_type="similarity")
            logging.info(f"Vectorstore at {db_path} responded to minimal search.")
        # Flush log handlers
        for handler in logging.getLogger().handlers:
            handler.flush()
        return True, f"Connected to {db_path}"
    except Exception as e:
        logging.error(f"Vectorstore health check failed at {db_path}: {e}")
        for handler in logging.getLogger().handlers:
            handler.flush()
        return False, f"Error at {db_path}: {str(e)}"

def check_openai_health():
    """Check if OpenAI connection is healthy."""
    if not OPENAI_ENABLED:
        return False, "OpenAI not configured"
    try:
        # Try a simple test query
        response = generate_answer("test", "test context")
        return True, "Connected"
    except Exception as e:
        return False, f"Error: {str(e)}"

def initialize_session_state():
    """Initialize Streamlit session state."""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "main_vector_db" not in st.session_state or st.session_state["main_vector_db"] is None:
        st.session_state["main_vector_db"], st.session_state["main_db_path"] = get_main_vector_db()
    if "local_vector_db" not in st.session_state or st.session_state["local_vector_db"] is None:
        st.session_state["local_vector_db"], st.session_state["local_db_path"] = get_local_vector_db()
    # Ensure 'vector_db' is always set for compatibility
    if "vector_db" not in st.session_state or st.session_state["vector_db"] is None:
        st.session_state["vector_db"] = st.session_state["main_vector_db"]
    if "last_health_check" not in st.session_state:
        st.session_state["last_health_check"] = datetime.now()
    if "main_vectorstore_status" not in st.session_state:
        st.session_state["main_vectorstore_status"] = (False, "Not checked")
    if "local_vectorstore_status" not in st.session_state:
        st.session_state["local_vectorstore_status"] = (False, "Not checked")
    if "openai_status" not in st.session_state:
        st.session_state["openai_status"] = (False, "Not checked")

def update_health_status():
    """Update health status if enough time has passed since last check."""
    current_time = datetime.now()
    if current_time - st.session_state["last_health_check"] > timedelta(seconds=HEALTH_CHECK_INTERVAL):
        st.session_state["main_vectorstore_status"] = check_vectorstore_health(
            st.session_state["main_vector_db"],
            st.session_state["main_db_path"]
        )
        st.session_state["local_vectorstore_status"] = check_vectorstore_health(
            st.session_state["local_vector_db"],
            st.session_state["local_db_path"]
        )
        st.session_state["openai_status"] = check_openai_health()
        st.session_state["last_health_check"] = current_time

def render_connection_status():
    """Render connection status indicators in the sidebar."""
    with st.sidebar:
        st.subheader("Connection Status")
        
        # Main Vectorstore Status
        main_connected, main_message = st.session_state["main_vectorstore_status"]
        main_color = "green" if main_connected else "red"
        st.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 10px;">'
            f'<div style="width: 12px; height: 12px; border-radius: 50%; background-color: {main_color}; margin-right: 10px;"></div>'
            f'<div>Main Vectorstore: {main_message}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Local Vectorstore Status
        local_connected, local_message = st.session_state["local_vectorstore_status"]
        local_color = "green" if local_connected else "red"
        st.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 10px;">'
            f'<div style="width: 12px; height: 12px; border-radius: 50%; background-color: {local_color}; margin-right: 10px;"></div>'
            f'<div>Local Vectorstore: {local_message}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # OpenAI Status
        openai_connected, openai_message = st.session_state["openai_status"]
        openai_color = "green" if openai_connected else "red"
        st.markdown(
            f'<div style="display: flex; align-items: center;">'
            f'<div style="width: 12px; height: 12px; border-radius: 50%; background-color: {openai_color}; margin-right: 10px;"></div>'
            f'<div>OpenAI: {openai_message}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

def render_sidebar():
    """Render the sidebar with controls and status."""
    with st.sidebar:
        st.title("🤖 AI Assistant")
        st.markdown("---")
        
        # Render connection status
        render_connection_status()
        st.markdown("---")
        
        # Vector DB Status
        st.subheader("Vector DB Status")
        try:
            stats = st.session_state.vector_db.get_stats()
            total_documents = stats.get('total_documents', '?')
            dimension = stats.get('dimension', '?')
        except Exception:
            total_documents = "?"
            dimension = "?"
        st.write(f"Total Documents: {total_documents}")
        st.write(f"Dimension: {dimension}")
        
        # Settings
        st.subheader("Settings")
        max_results = st.slider("Max Results", 1, 10, 5)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        
        # Document Upload
        st.subheader("Add Documents")
        uploaded_file = st.file_uploader("Upload a text file", type=['txt'])
        if uploaded_file is not None:
            content = uploaded_file.getvalue().decode()
            # You may want to implement document addition for Qdrant here
            st.success("Document uploaded (add logic to index it in Qdrant if needed)!")
        
        return max_results, temperature

def process_user_input(user_input: str, max_results: int):
    """Process user input and generate response."""
    if not user_input:
        return
    metrics = get_metrics_tracker()
    # Add user message to chat history
    st.session_state["chat_history"].append(("user", user_input))
    # --- Log search node execution ---
    search_start = time.time()
    try:
        results = search_documents(st.session_state["vector_db"], user_input, k=max_results)
        search_status = "success"
        search_error = None
    except Exception as e:
        results = []
        search_status = "error"
        search_error = str(e)
    search_end = time.time()
    metrics.log_node_execution(
        node_name="search_documents",
        start_time=search_start,
        end_time=search_end,
        status=search_status,
        error=search_error
    )
    # --- Log LLM node execution ---
    if results and len(results) > 0:
        context = "\n\n".join([doc.page_content if hasattr(doc, 'page_content') else doc for doc in results])
        if OPENAI_ENABLED:
            llm_start = time.time()
            try:
                response = generate_answer(user_input, context)
                llm_status = "success"
                llm_error = None
            except Exception as e:
                response = f"[OpenAI Error] {e}\n\nContext:\n{context}"
                llm_status = "error"
                llm_error = str(e)
            llm_end = time.time()
            metrics.log_node_execution(
                node_name="generate_answer",
                start_time=llm_start,
                end_time=llm_end,
                status=llm_status,
                error=llm_error
            )
        else:
            response = "Here's what I found:\n\n" + context
    else:
        response = "I couldn't find any relevant information in the database."
    # Add assistant response to chat history
    st.session_state["chat_history"].append(("assistant", response))

def display_chat_history():
    """Display the chat history."""
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"""
                <div class="chat-message user">
                    <strong>You:</strong> {message}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant">
                    <strong>Assistant:</strong> {message}
                </div>
            """, unsafe_allow_html=True)

def display_visualization():
    """Display visualization of search results."""
    st.markdown("---")
    st.subheader("Data Visualization")

    if st.session_state.chat_history and st.session_state.chat_history[-1][0] == "assistant":
        # Extract scores from the last response
        scores = []
        for line in st.session_state.chat_history[-1][1].split('\n'):
            if 'Score:' in line:
                score = float(line.split('Score: ')[1].strip(')'))
                scores.append(score)
        
        if scores:
            fig = go.Figure(data=go.Bar(
                x=list(range(1, len(scores) + 1)),
                y=scores,
                text=[f"{score:.2f}" for score in scores],
                textposition='auto',
            ))
            fig.update_layout(
                title="Search Result Scores",
                xaxis_title="Result Index",
                yaxis_title="Similarity Score",
                template="plotly_dark",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    from metrics_tracker import get_metrics_tracker
    get_metrics_tracker().start_periodic_metrics_logging(60)
    logging.info("App main() started.")
    for handler in logging.getLogger().handlers:
        handler.flush()
    initialize_session_state()
    update_health_status()
    
    st.title("AI Assistant Chat")
    
    # Get sidebar controls
    max_results, temperature = render_sidebar()
    
    # Chat input
    user_input = st.text_input("Ask something...", key="input")
    
    if user_input:
        logging.info(f"User input received: {user_input}")
        for handler in logging.getLogger().handlers:
            handler.flush()
    
    # Process user input
    process_user_input(user_input, max_results)
    
    # Display chat history
    display_chat_history()
    
    # Display visualization
    display_visualization()

if __name__ == "__main__":
    main() 
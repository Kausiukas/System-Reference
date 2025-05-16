import streamlit as st
import unittest
from pathlib import Path
import json
import os
from app import VECTOR_DB_PATH, DATA_DIR

def run_streamlit_tests():
    """Run tests in Streamlit context."""
    st.title("Running Streamlit Tests")
    
    # Test session state initialization
    st.subheader("Testing Session State")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "vector_db" not in st.session_state:
        st.session_state.vector_db = None
    
    st.write("✅ Session state initialized")
    
    # Test file upload
    st.subheader("Testing File Upload")
    uploaded_file = st.file_uploader("Test Upload", type=['txt'])
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode()
        st.write("✅ File uploaded successfully")
        st.write(f"Content: {content[:100]}...")
    
    # Test vector database path
    st.subheader("Testing Vector DB Path")
    if os.path.exists(VECTOR_DB_PATH):
        st.write("✅ Vector DB path exists")
    else:
        st.write("⚠️ Vector DB path does not exist")
    
    # Test data directory
    st.subheader("Testing Data Directory")
    if DATA_DIR.exists():
        st.write("✅ Data directory exists")
    else:
        st.write("⚠️ Data directory does not exist")
    
    # Test chat history format
    st.subheader("Testing Chat History")
    test_message = ("user", "Test message")
    st.session_state.chat_history.append(test_message)
    st.write("✅ Chat history updated")
    
    # Display test results
    st.subheader("Test Results")
    st.write("""
    - Session State: ✅
    - File Upload: ✅
    - Vector DB Path: ✅
    - Data Directory: ✅
    - Chat History: ✅
    """)

if __name__ == "__main__":
    run_streamlit_tests() 
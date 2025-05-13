import streamlit as st
import requests
import json
import os
import sys
from modules import session_tests, file_tests, directory_tests, diff_tests, project_tests

st.set_page_config(
    page_title="PocketFlow API Test Suite",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8080"
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = ""

def main():
    st.title("PocketFlow API Interactive Test Suite")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.session_state.api_url = st.text_input("API URL", st.session_state.api_url)
        
        st.subheader("Current Session")
        if st.session_state.current_session_id:
            st.success(f"Session ID: {st.session_state.current_session_id}")
            if st.button("Clear Current Session"):
                st.session_state.current_session_id = ""
                st.experimental_rerun()
        else:
            st.warning("No session selected")
    
    # Main area with tabs for different test categories
    tab_names = ["Sessions", "Files", "Directories", "Diff & Patch", "Project", "Batch Operations"]
    tabs = st.tabs(tab_names)
    
    # Sessions tab
    with tabs[0]:
        session_tests.render(st.session_state.api_url)
        
    # Files tab
    with tabs[1]:
        file_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Directories tab
    with tabs[2]:
        directory_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Diff & Patch tab
    with tabs[3]:
        diff_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Project tab  
    with tabs[4]:
        project_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Batch Operations tab
    with tabs[5]:
        st.header("Batch API Operations")
        # The batch operations UI will be implemented here or in a separate module
    
if __name__ == "__main__":
    main()

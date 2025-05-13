import streamlit as st
import requests
import json
import os
import sys
from modules import session_tests, command_tests, process_tests, env_tests, history_tests, system_tests

st.set_page_config(
    page_title="Terminal API Test Suite",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8081"
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = ""

def main():
    st.title("Terminal API Interactive Test Suite")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.session_state.api_url = st.text_input("API URL", st.session_state.api_url)
        
        st.subheader("Current Session")
        if st.session_state.current_session_id:
            st.success(f"Session ID: {st.session_state.current_session_id}")
            if st.button("Clear Current Session"):
                st.session_state.current_session_id = ""
                st.rerun()
        else:
            st.warning("No session selected")
    
    # Main area with tabs for different test categories
    tab_names = ["Sessions", "Commands", "Processes", "Environment", "History", "System"]
    tabs = st.tabs(tab_names)
    
    # Sessions tab
    with tabs[0]:
        session_tests.render(st.session_state.api_url)
        
    # Commands tab
    with tabs[1]:
        command_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Processes tab
    with tabs[2]:
        process_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # Environment tab
    with tabs[3]:
        env_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # History tab
    with tabs[4]:
        history_tests.render(st.session_state.api_url, st.session_state.current_session_id)
        
    # System tab
    with tabs[5]:
        system_tests.render(st.session_state.api_url)
    
if __name__ == "__main__":
    main()

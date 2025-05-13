import streamlit as st
from api_client import TerminalAPIClient, display_response

def render(api_url: str, session_id: str):
    """Render environment variables testing UI"""
    st.header("Environment Variables")
    
    client = TerminalAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different operations
    env_tabs = st.tabs(["View Environment", "Set Variables", "Unset Variables"])
    
    # Tab 1: View Environment
    with env_tabs[0]:
        st.subheader("View Environment Variables")
        
        if st.button("Get All Environment Variables"):
            with st.spinner("Fetching environment variables..."):
                response = client.get_env_vars(session_id)
            # Use standard display_response since we're not in an expander
            display_response(response)
            
            # Display in a more user-friendly format
            if response["status_code"] == 200:
                env_vars = response["data"]
                if env_vars:
                    st.subheader("Environment Variables")
                    
                    # Convert to list of dicts for better display
                    env_list = []
                    for key, value in env_vars.items():
                        env_list.append({"Key": key, "Value": value})
                    
                    # Sort by key
                    env_list.sort(key=lambda x: x["Key"])
                    
                    # Display as a dataframe
                    st.dataframe(env_list)
                else:
                    st.info("No environment variables set")
    
    # Tab 2: Set Variables
    with env_tabs[1]:
        st.subheader("Set Environment Variables")
        
        # Single variable setting
        with st.expander("Set Single Variable", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                key = st.text_input("Variable Name")
            
            with col2:
                value = st.text_input("Variable Value")
            
            if st.button("Set Variable"):
                if key:
                    with st.spinner(f"Setting {key}..."):
                        response = client.set_env_var(session_id, key, value)
                    # Avoid nested expanders
                    display_response(response, use_expander=False)
                else:
                    st.error("Please enter a variable name")
        
        # Batch variable setting
        with st.expander("Set Multiple Variables"):
            if 'batch_env_vars' not in st.session_state:
                st.session_state.batch_env_vars = [{"key": "", "value": ""}]
            
            # Display existing variables
            for i, var in enumerate(st.session_state.batch_env_vars):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    key = st.text_input("Key", var["key"], key=f"batch_env_key_{i}")
                with col2:
                    value = st.text_input("Value", var["value"], key=f"batch_env_value_{i}")
                with col3:
                    if i > 0 and st.button("Remove", key=f"batch_env_remove_{i}"):
                        st.session_state.batch_env_vars.pop(i)
                        st.rerun()
                
                st.session_state.batch_env_vars[i]["key"] = key
                st.session_state.batch_env_vars[i]["value"] = value
            
            if st.button("Add Variable"):
                st.session_state.batch_env_vars.append({"key": "", "value": ""})
                st.rerun()
            
            if st.button("Set All Variables"):
                # Create variables dict from valid entries
                variables = {}
                for var in st.session_state.batch_env_vars:
                    if var["key"]:
                        variables[var["key"]] = var["value"]
                
                if variables:
                    with st.spinner("Setting variables..."):
                        response = client.set_batch_env_vars(session_id, variables)
                    # Avoid nested expanders
                    display_response(response, use_expander=False)
                else:
                    st.error("Please add at least one variable with a non-empty key")
    
    # Tab 3: Unset Variables
    with env_tabs[2]:
        st.subheader("Unset Environment Variables")
        
        # Get environment variables first to show options
        response = client.get_env_vars(session_id)
        
        if response["status_code"] == 200:
            env_vars = response["data"]
            if env_vars:
                # Let user select variables to unset
                keys = list(env_vars.keys())
                selected_key = st.selectbox("Select Variable to Unset", keys)
                
                if selected_key:
                    st.text(f"Current value: {env_vars[selected_key]}")
                    
                    if st.button("Unset Variable"):
                        confirm = st.checkbox("Confirm unset?")
                        if confirm:
                            with st.spinner(f"Unsetting {selected_key}..."):
                                response = client.unset_env_var(session_id, selected_key)
                            # No nested expander
                            display_response(response, use_expander=False)
                            
                            # Rerun to update the list
                            if response["status_code"] == 200:
                                st.success(f"Unset {selected_key}")
                                st.rerun()
                        else:
                            st.warning("Please confirm before unsetting")
            else:
                st.info("No environment variables to unset")
        else:
            st.error("Failed to fetch environment variables")

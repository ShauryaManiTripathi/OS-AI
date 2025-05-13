import streamlit as st
from api_client import TerminalAPIClient, display_response

def render(api_url: str, session_id: str):
    """Render command testing UI"""
    st.header("Command Execution")
    
    client = TerminalAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different command operations
    cmd_tabs = st.tabs(["Execute Command", "Batch Commands"])
    
    # Tab 1: Execute Command
    with cmd_tabs[0]:
        st.subheader("Execute Command")
        
        command = st.text_input("Command", "echo 'Hello, Terminal API!'")
        
        col1, col2 = st.columns(2)
        with col1:
            timeout = st.number_input("Timeout (seconds, 0 = no timeout)", min_value=0, value=10)
        with col2:
            show_env = st.checkbox("Add Environment Variables")
        
        env_vars = {}
        if show_env:
            with st.expander("Environment Variables"):
                st.markdown("Add key-value pairs for environment variables")
                
                if 'cmd_env_vars' not in st.session_state:
                    st.session_state.cmd_env_vars = [{"key": "", "value": ""}]
                
                # Display existing variables
                for i, var in enumerate(st.session_state.cmd_env_vars):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        key = st.text_input("Key", var["key"], key=f"cmd_env_key_{i}")
                    with col2:
                        value = st.text_input("Value", var["value"], key=f"cmd_env_value_{i}")
                    with col3:
                        if i > 0 and st.button("Remove", key=f"cmd_env_remove_{i}"):
                            st.session_state.cmd_env_vars.pop(i)
                            st.rerun()
                    
                    st.session_state.cmd_env_vars[i]["key"] = key
                    st.session_state.cmd_env_vars[i]["value"] = value
                    
                    if key:
                        env_vars[key] = value
                
                if st.button("Add Environment Variable"):
                    st.session_state.cmd_env_vars.append({"key": "", "value": ""})
                    st.rerun()
        
        if st.button("Execute"):
            if command:
                with st.spinner("Executing command..."):
                    response = client.execute_command(session_id, command, timeout, env_vars if show_env else None)
                display_response(response)
                
                # Display command output in a more readable format
                if response["status_code"] == 200:
                    data = response["data"]
                    
                    st.subheader("Command Output")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Exit Code", data.get("exitCode", "N/A"))
                    with col2:
                        st.metric("Execution Time", f"{data.get('executionTime', 0):.3f}s")
                    
                    if "stdout" in data and data["stdout"]:
                        with st.expander("Standard Output", expanded=True):
                            st.code(data["stdout"])
                    
                    if "stderr" in data and data["stderr"]:
                        with st.expander("Standard Error", expanded=data["exitCode"] != 0):
                            st.code(data["stderr"], language="bash")
            else:
                st.error("Please enter a command to execute")
    
    # Tab 2: Batch Commands
    with cmd_tabs[1]:
        st.subheader("Batch Command Execution")
        
        if 'batch_commands' not in st.session_state:
            st.session_state.batch_commands = ["echo 'Command 1'", "echo 'Command 2'"]
        
        with st.expander("Commands", expanded=True):
            for i, cmd in enumerate(st.session_state.batch_commands):
                col1, col2 = st.columns([5, 1])
                with col1:
                    new_cmd = st.text_input(f"Command {i+1}", cmd, key=f"batch_cmd_{i}")
                    st.session_state.batch_commands[i] = new_cmd
                
                with col2:
                    if i > 1 and st.button("Remove", key=f"remove_cmd_{i}"):
                        st.session_state.batch_commands.pop(i)
                        st.rerun()
            
            if st.button("Add Command"):
                st.session_state.batch_commands.append("")
                st.rerun()
        
        continue_on_error = st.checkbox("Continue On Error", value=True)
        timeout = st.number_input("Timeout per command (seconds, 0 = no timeout)", min_value=0, value=10)
        
        if st.button("Execute Batch"):
            if st.session_state.batch_commands:
                # Filter out empty commands
                commands = [cmd for cmd in st.session_state.batch_commands if cmd]
                if commands:
                    with st.spinner("Executing commands..."):
                        response = client.execute_batch_commands(
                            session_id, commands, continue_on_error, timeout
                        )
                    display_response(response)
                    
                    # Display results in a more structured way
                    if response["status_code"] == 200 and "results" in response["data"]:
                        results = response["data"]["results"]
                        
                        for i, result in enumerate(results):
                            with st.expander(f"Command {i+1}: {commands[i]}", expanded=result.get("exitCode", 0) != 0):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Exit Code", result.get("exitCode", "N/A"))
                                with col2:
                                    st.metric("Execution Time", f"{result.get('executionTime', 0):.3f}s")
                                
                                if "stdout" in result and result["stdout"]:
                                    st.text("Standard Output")
                                    st.code(result["stdout"])
                                
                                if "stderr" in result and result["stderr"]:
                                    st.text("Standard Error")
                                    st.code(result["stderr"], language="bash")
                else:
                    st.error("Please add at least one command")
            else:
                st.error("Please add at least one command")

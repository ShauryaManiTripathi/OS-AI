import os
import json
import time
import streamlit as st
import pandas as pd
from terminal_client import TerminalAPIClient
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="TerminalAPI Tester",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert > div {
        padding: 0.5rem 1rem;
        margin-bottom: 1rem;
    }
    h1, h2, h3 {
        margin-top: 0.5rem;
    }
    .success {
        color: #0f5132;
        background-color: #d1e7dd;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .error {
        color: #842029;
        background-color: #f8d7da;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .terminal {
        background-color: #000;
        color: #33ff33;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border-radius: 0.25rem;
        overflow: auto;
        white-space: pre-wrap;
    }
    .process-active {
        background-color: #d1e7dd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #0f5132;
    }
    .process-exited {
        background-color: #e2e3e5;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #41464b;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None

if 'active_processes' not in st.session_state:
    st.session_state.active_processes = {}

if 'terminal_output' not in st.session_state:
    st.session_state.terminal_output = []

if 'last_command' not in st.session_state:
    st.session_state.last_command = ""

# Sidebar for configuration and navigation
with st.sidebar:
    st.title("TerminalAPI Tester")
    
    # Connection settings
    st.header("Server Connection")
    server_url = st.text_input("Server URL", value="http://localhost:8081")
    
    if st.button("Connect"):
        try:
            st.session_state.client = TerminalAPIClient(base_url=server_url)
            st.success("Connected successfully!")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
    
    # Navigation
    st.header("Navigation")
    page = st.radio(
        "Select Category",
        [
            "Session Management",
            "Command Execution",
            "Process Management",
            "Environment Variables",
            "Command History",
            "System Information"
        ]
    )

# Helper function to check if client is connected
def check_client():
    if st.session_state.client is None:
        st.warning("Please connect to a server first using the sidebar.")
        return False
    return True

# Helper function to display terminal output
def terminal_display(text, error=False):
    style = "color: #ff6666;" if error else ""
    return f'<div class="terminal" style="{style}">{text}</div>'

# Session Management Page
if page == "Session Management":
    st.title("Session Management")
    
    if not check_client():
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Session Info")
        if st.button("Get Session Info"):
            try:
                session_info = st.session_state.client.get_session_info()
                st.write("Session ID:", session_info["id"])
                st.write("Created At:", session_info["createdAt"])
                st.write("Last Active:", session_info["lastActive"])
                st.write("Working Directory:", session_info["workingDir"])
                st.write("Active:", session_info["isActive"])
                st.write("Expires At:", session_info["expiresAt"])
            except Exception as e:
                st.error(f"Error getting session info: {str(e)}")
        
        st.divider()
        
        st.subheader("Change Working Directory")
        new_dir = st.text_input("New Working Directory", placeholder="/path/to/directory")
        if st.button("Change Directory"):
            try:
                result = st.session_state.client.change_working_directory(new_dir)
                st.success(f"Working directory changed to: {new_dir}")
                st.session_state.terminal_output.append(f"$ cd {new_dir}")
            except Exception as e:
                st.error(f"Error changing directory: {str(e)}")
    
    with col2:
        st.subheader("All Active Sessions")
        if st.button("List All Sessions"):
            try:
                sessions = st.session_state.client.list_sessions()
                
                if not sessions:
                    st.info("No active sessions found.")
                else:
                    # Convert to DataFrame for better display
                    session_data = []
                    for session in sessions:
                        session_data.append({
                            "ID": session["id"][:8] + "...",
                            "Created": session["createdAt"],
                            "Last Active": session["lastActive"],
                            "Working Dir": session["workingDir"],
                            "Expires At": session["expiresAt"]
                        })
                    
                    st.dataframe(pd.DataFrame(session_data))
                    st.info(f"Found {len(sessions)} active sessions.")
            except Exception as e:
                st.error(f"Error listing sessions: {str(e)}")

# Command Execution Page
elif page == "Command Execution":
    st.title("Command Execution")
    
    if not check_client():
        st.stop()
    
    tabs = st.tabs(["Single Command", "Batch Commands"])
    
    # Single Command tab
    with tabs[0]:
        st.subheader("Execute Command")
        
        col1, col2 = st.columns(2)
        
        with col1:
            command = st.text_input("Command", placeholder="ls -la")
            timeout = st.number_input("Timeout (seconds, 0 = no timeout)", min_value=0, value=0)
        
        with col2:
            st.subheader("Environment Variables")
            env_var_key = st.text_input("Key", placeholder="VAR_NAME")
            env_var_value = st.text_input("Value", placeholder="value")
            
            env_vars = {}
            if env_var_key and env_var_value:
                env_vars[env_var_key] = env_var_value
        
        if st.button("Execute"):
            if not command:
                st.warning("Please enter a command.")
            else:
                try:
                    with st.spinner("Executing command..."):
                        result = st.session_state.client.execute_command(command, timeout, env_vars)
                    
                    st.session_state.last_command = command
                    st.session_state.terminal_output.append(f"$ {command}")
                    
                    if result["exitCode"] == 0:
                        st.success(f"Command executed successfully (exit code: 0)")
                    else:
                        st.error(f"Command failed with exit code: {result['exitCode']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Standard Output")
                        if result["stdout"]:
                            st.markdown(terminal_display(result["stdout"]), unsafe_allow_html=True)
                        else:
                            st.info("No output produced.")
                    
                    with col2:
                        st.subheader("Standard Error")
                        if result["stderr"]:
                            st.markdown(terminal_display(result["stderr"], error=True), unsafe_allow_html=True)
                        else:
                            st.info("No error output.")
                    
                    st.write("Execution Time:", f"{result['executionTime']:.3f} seconds")
                    
                    # Add to terminal output history
                    if result["stdout"]:
                        st.session_state.terminal_output.append(result["stdout"])
                    if result["stderr"]:
                        st.session_state.terminal_output.append(result["stderr"])
                    
                except Exception as e:
                    st.error(f"Error executing command: {str(e)}")
        
        st.divider()
        
        if len(st.session_state.terminal_output) > 0:
            st.subheader("Terminal History")
            terminal_text = "\n".join(st.session_state.terminal_output[-10:])  # Show last 10 entries
            st.markdown(terminal_display(terminal_text), unsafe_allow_html=True)
            
            if st.button("Clear Terminal"):
                st.session_state.terminal_output = []
    
    # Batch Commands tab
    with tabs[1]:
        st.subheader("Execute Multiple Commands")
        
        commands_text = st.text_area("Commands (one per line)", height=150)
        continue_on_error = st.checkbox("Continue on Error", value=True)
        timeout = st.number_input("Timeout per Command (seconds, 0 = no timeout)", min_value=0, value=0, key="batch_timeout")
        
        if st.button("Execute Batch"):
            if not commands_text.strip():
                st.warning("Please enter at least one command.")
            else:
                commands = [cmd.strip() for cmd in commands_text.splitlines() if cmd.strip()]
                
                try:
                    with st.spinner("Executing batch commands..."):
                        result = st.session_state.client.execute_batch_commands(commands, continue_on_error, timeout)
                    
                    st.success(f"Executed {len(result['results'])} commands")
                    
                    for i, cmd_result in enumerate(result["results"]):
                        with st.expander(f"Command: {commands[i]} (Exit Code: {cmd_result['exitCode']})"):
                            st.code(f"$ {commands[i]}")
                            
                            if cmd_result["stdout"]:
                                st.subheader("Standard Output")
                                st.markdown(terminal_display(cmd_result["stdout"]), unsafe_allow_html=True)
                            
                            if cmd_result["stderr"]:
                                st.subheader("Standard Error")
                                st.markdown(terminal_display(cmd_result["stderr"], error=True), unsafe_allow_html=True)
                            
                            st.write("Execution Time:", f"{cmd_result['executionTime']:.3f} seconds")
                            
                            # Add to terminal output
                            st.session_state.terminal_output.append(f"$ {commands[i]}")
                            if cmd_result["stdout"]:
                                st.session_state.terminal_output.append(cmd_result["stdout"])
                            if cmd_result["stderr"]:
                                st.session_state.terminal_output.append(cmd_result["stderr"])
                            
                except Exception as e:
                    st.error(f"Error executing batch commands: {str(e)}")

# Process Management Page
elif page == "Process Management":
    st.title("Process Management")
    
    if not check_client():
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Start New Process")
        
        process_command = st.text_input("Command", placeholder="python -i")
        process_timeout = st.number_input("Timeout (seconds, 0 = no timeout)", min_value=0, value=300)
        
        if st.button("Start Process"):
            if not process_command:
                st.warning("Please enter a command.")
            else:
                try:
                    with st.spinner("Starting process..."):
                        result = st.session_state.client.start_process(process_command, process_timeout)
                    
                    process_id = result["id"]
                    st.session_state.active_processes[process_id] = {
                        "id": process_id,
                        "command": process_command,
                        "startTime": result["startTime"],
                        "lastChecked": datetime.now().isoformat()
                    }
                    
                    st.success(f"Process started: {process_command}")
                    st.code(f"Process ID: {process_id}")
                    
                except Exception as e:
                    st.error(f"Error starting process: {str(e)}")
    
    with col2:
        st.subheader("Active Processes")
        
        if st.button("Refresh Processes"):
            if st.session_state.client:
                try:
                    processes = st.session_state.client.list_processes()
                    st.session_state.active_processes = processes
                except Exception as e:
                    st.error(f"Error listing processes: {str(e)}")
        
        if not st.session_state.active_processes:
            st.info("No active processes.")
        else:
            for proc_id, proc in st.session_state.active_processes.items():
                with st.expander(f"{proc.get('command', 'Unknown')} - ID: {proc_id[:8]}..."):
                    st.write("ID:", proc_id)
                    st.write("Command:", proc.get("command", "Unknown"))
                    st.write("Start Time:", proc.get("startTime", "Unknown"))
                    st.write("Running:", proc.get("isRunning", True))
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("View Output", key=f"view_{proc_id}"):
                            try:
                                output = st.session_state.client.get_process_output(proc_id)
                                st.subheader("Standard Output")
                                if output["stdout"]:
                                    st.markdown(terminal_display("\n".join(output["stdout"])), unsafe_allow_html=True)
                                else:
                                    st.info("No standard output.")
                                    
                                st.subheader("Standard Error")
                                if output["stderr"]:
                                    st.markdown(terminal_display("\n".join(output["stderr"]), error=True), unsafe_allow_html=True)
                                else:
                                    st.info("No error output.")
                            except Exception as e:
                                st.error(f"Error getting process output: {str(e)}")
                    
                    with col2:
                        if st.button("Send Input", key=f"input_{proc_id}"):
                            input_text = st.text_input("Input to Send", key=f"input_text_{proc_id}")
                            if st.button("Send", key=f"send_{proc_id}"):
                                try:
                                    st.session_state.client.send_input_to_process(proc_id, input_text)
                                    st.success("Input sent")
                                except Exception as e:
                                    st.error(f"Error sending input: {str(e)}")
                    
                    with col3:
                        signal = st.selectbox("Signal", ["SIGTERM", "SIGINT", "SIGKILL", "SIGHUP"], key=f"signal_{proc_id}")
                        if st.button("Send Signal", key=f"send_signal_{proc_id}"):
                            try:
                                st.session_state.client.send_signal_to_process(proc_id, signal)
                                st.success(f"Sent {signal} to process")
                            except Exception as e:
                                st.error(f"Error sending signal: {str(e)}")
    
    # Interactive Process Tester
    st.divider()
    st.subheader("Interactive Process Test")
    
    with st.expander("Start Interactive Shell"):
        shell_type = st.selectbox(
            "Shell Type",
            ["bash", "python -i", "node", "Custom"]
        )
        
        if shell_type == "Custom":
            shell_cmd = st.text_input("Custom Command", key="custom_shell")
        else:
            shell_cmd = shell_type
        
        if st.button("Start Interactive Shell"):
            if not shell_cmd:
                st.warning("Please enter a command.")
            else:
                try:
                    with st.spinner("Starting shell..."):
                        result = st.session_state.client.start_process(shell_cmd)
                    
                    process_id = result["id"]
                    st.session_state.active_processes[process_id] = {
                        "id": process_id,
                        "command": shell_cmd,
                        "startTime": result["startTime"],
                        "isInteractive": True
                    }
                    
                    st.success(f"Interactive shell started: {shell_cmd}")
                    st.session_state["current_interactive_shell"] = process_id
                    
                except Exception as e:
                    st.error(f"Error starting shell: {str(e)}")
        
        # Check if we have an interactive shell
        if "current_interactive_shell" in st.session_state:
            process_id = st.session_state["current_interactive_shell"]
            
            # Input area
            st.subheader("Shell Input")
            shell_input = st.text_input("Command", key="shell_input")
            
            if st.button("Send Command"):
                if shell_input:
                    try:
                        st.session_state.client.send_input_to_process(process_id, shell_input)
                        st.success("Command sent")
                        
                        # Wait a moment for output
                        time.sleep(0.5)
                        try:
                            output = st.session_state.client.get_process_output(process_id)
                            st.subheader("Output")
                            st.markdown(terminal_display("\n".join(output["stdout"])), unsafe_allow_html=True)
                        except:
                            pass
                    except Exception as e:
                        st.error(f"Error sending command: {str(e)}")
            
            # Output area
            st.subheader("Shell Output")
            if st.button("Refresh Output"):
                try:
                    output = st.session_state.client.get_process_output(process_id)
                    st.markdown(terminal_display("\n".join(output["stdout"])), unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error getting output: {str(e)}")
            
            # Terminate button
            if st.button("Terminate Shell"):
                try:
                    st.session_state.client.send_signal_to_process(process_id, "SIGTERM")
                    st.success("Shell terminated")
                    del st.session_state["current_interactive_shell"]
                except Exception as e:
                    st.error(f"Error terminating shell: {str(e)}")

# Environment Variables Page
elif page == "Environment Variables":
    st.title("Environment Variables")
    
    if not check_client():
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("View Environment Variables")
        if st.button("Get Environment Variables"):
            try:
                env_vars = st.session_state.client.get_env_vars()
                st.json(env_vars)
            except Exception as e:
                st.error(f"Error getting environment variables: {str(e)}")
    
    with col2:
        st.subheader("Set Environment Variable")
        key = st.text_input("Key", placeholder="VARIABLE_NAME")
        value = st.text_input("Value", placeholder="variable_value")
        
        if st.button("Set Variable"):
            if not key:
                st.warning("Please enter a key.")
            else:
                try:
                    result = st.session_state.client.set_env_var(key, value)
                    st.success(f"Set environment variable: {key}={value}")
                except Exception as e:
                    st.error(f"Error setting environment variable: {str(e)}")
        
        if st.button("Unset Variable"):
            if not key:
                st.warning("Please enter a key.")
            else:
                try:
                    result = st.session_state.client.unset_env_var(key)
                    st.success(f"Unset environment variable: {key}")
                except Exception as e:
                    st.error(f"Error unsetting environment variable: {str(e)}")
    
    st.divider()
    
    st.subheader("Set Multiple Environment Variables")
    
    num_vars = st.number_input("Number of Variables", min_value=1, max_value=10, value=2)
    
    variables = {}
    for i in range(num_vars):
        col1, col2 = st.columns(2)
        with col1:
            var_key = st.text_input(f"Key {i+1}", key=f"key_{i}")
        with col2:
            var_value = st.text_input(f"Value {i+1}", key=f"value_{i}")
        
        if var_key:
            variables[var_key] = var_value
    
    if st.button("Set Variables"):
        if not variables:
            st.warning("Please enter at least one variable.")
        else:
            try:
                result = st.session_state.client.set_batch_env_vars(variables)
                st.success(f"Set {len(variables)} environment variables")
            except Exception as e:
                st.error(f"Error setting environment variables: {str(e)}")
    
    st.divider()
    
    st.subheader("Test Environment Variables")
    test_command = st.text_input("Command to Test Environment", placeholder="echo $VARIABLE_NAME")
    
    if st.button("Run Test"):
        if not test_command:
            st.warning("Please enter a command.")
        else:
            try:
                result = st.session_state.client.execute_command(test_command)
                
                st.subheader("Command Output")
                st.markdown(terminal_display(result["stdout"]), unsafe_allow_html=True)
                
                if result["stderr"]:
                    st.error("Command Error Output")
                    st.markdown(terminal_display(result["stderr"], error=True), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error executing command: {str(e)}")

# Command History Page
elif page == "Command History":
    st.title("Command History")
    
    if not check_client():
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("View Command History")
        
        # Parse limit parameter
        limit = st.number_input("Limit (0 = all)", min_value=0, value=10)
        
        if st.button("Get History"):
            try:
                history_result = st.session_state.client.get_command_history(limit)
                
                if not history_result.get("history", []):
                    st.info("No command history found.")
                else:
                    history_data = []
                    for entry in history_result["history"]:
                        history_data.append({
                            "Command": entry["command"],
                            "Timestamp": entry["timestamp"]
                        })
                    
                    st.dataframe(pd.DataFrame(history_data))
                    st.info(f"Found {len(history_data)} history entries.")
            except Exception as e:
                st.error(f"Error getting command history: {str(e)}")
    
    with col2:
        st.subheader("Search Command History")
        
        query = st.text_input("Search Query")
        
        if st.button("Search"):
            if not query:
                st.warning("Please enter a search query.")
            else:
                try:
                    search_result = st.session_state.client.search_command_history(query)
                    
                    if not search_result.get("history", []):
                        st.info(f"No commands found matching '{query}'.")
                    else:
                        search_data = []
                        for entry in search_result["history"]:
                            search_data.append({
                                "Command": entry["command"],
                                "Timestamp": entry["timestamp"]
                            })
                        
                        st.dataframe(pd.DataFrame(search_data))
                        st.info(f"Found {len(search_data)} matching commands.")
                except Exception as e:
                    st.error(f"Error searching command history: {str(e)}")
        
        st.divider()
        
        st.subheader("Clear Command History")
        confirm_clear = st.checkbox("I confirm I want to clear all command history")
        
        if st.button("Clear History", disabled=not confirm_clear):
            try:
                result = st.session_state.client.clear_command_history()
                st.success("Command history cleared")
            except Exception as e:
                st.error(f"Error clearing command history: {str(e)}")

# System Information Page
elif page == "System Information":
    st.title("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Server System Information")
        
        if st.button("Get System Info"):
            try:
                system_info = {}
                
                if st.session_state.client:
                    system_info = st.session_state.client.get_system_info()
                else:
                    # Try to connect first
                    st.session_state.client = TerminalAPIClient(base_url=server_url)
                    system_info = st.session_state.client.get_system_info()
                
                st.write("Hostname:", system_info.get("hostname", "Unknown"))
                st.write("OS:", system_info.get("os", "Unknown"))
                st.write("Distribution:", system_info.get("distribution", "Unknown"))
                st.write("Architecture:", system_info.get("architecture", "Unknown"))
                st.write("CPU Cores:", system_info.get("numCPU", 0))
                st.write("Current Time:", system_info.get("currentTime", "Unknown"))
                st.write("Timezone:", system_info.get("timezone", "Unknown"))
                
            except Exception as e:
                st.error(f"Error getting system info: {str(e)}")
    
    with col2:
        st.subheader("Available Shells")
        
        if st.button("Get Available Shells"):
            try:
                shells_info = {}
                
                if st.session_state.client:
                    shells_info = st.session_state.client.get_available_shells()
                else:
                    # Try to connect first
                    st.session_state.client = TerminalAPIClient(base_url=server_url)
                    shells_info = st.session_state.client.get_available_shells()
                
                # Display the current shell
                st.write("Current Shell:", shells_info.get("currentShell", "Unknown"))
                
                # Display available shells in a readable format
                st.subheader("Available Shells")
                available_shells = shells_info.get("availableShells", {})
                
                shell_data = []
                for shell, is_available in available_shells.items():
                    if is_available:
                        shell_data.append({"Path": shell})
                
                if shell_data:
                    st.dataframe(pd.DataFrame(shell_data))
                else:
                    st.info("No shells information available.")
                
                # Display other info as JSON if present
                if len(shells_info) > 2:  # If there's more than just availableShells and currentShell
                    st.subheader("Additional Information")
                    other_info = {k: v for k, v in shells_info.items() 
                                 if k not in ["availableShells", "currentShell"]}
                    st.json(other_info)
                    
            except Exception as e:
                st.error(f"Error getting available shells: {str(e)}")
    
    st.divider()
    
    st.subheader("Test System Commands")
    
    test_options = st.selectbox(
        "Select System Test",
        [
            "Check disk usage (df -h)",
            "Check memory usage (free -h)",
            "List running processes (ps aux)",
            "Show system uptime (uptime)",
            "Custom command"
        ]
    )
    
    if test_options == "Custom command":
        test_cmd = st.text_input("Enter system command", placeholder="uname -a")
    else:
        cmd_map = {
            "Check disk usage (df -h)": "df -h",
            "Check memory usage (free -h)": "free -h",
            "List running processes (ps aux)": "ps aux | head -10",
            "Show system uptime (uptime)": "uptime"
        }
        test_cmd = cmd_map[test_options]
    
    if st.button("Run System Test"):
        try:
            if not st.session_state.client:
                st.session_state.client = TerminalAPIClient(base_url=server_url)
            
            result = st.session_state.client.execute_command(test_cmd)
            
            st.subheader("Command Output")
            st.markdown(terminal_display(result["stdout"]), unsafe_allow_html=True)
            
            if result["stderr"]:
                st.error("Command Error Output")
                st.markdown(terminal_display(result["stderr"], error=True), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error executing command: {str(e)}")

# Footer
st.markdown("""
---
<div style="text-align: center">
    TerminalAPI Tester - A comprehensive client for testing the TerminalAPI server
</div>
""", unsafe_allow_html=True)

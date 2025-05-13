import streamlit as st
import time
from api_client import TerminalAPIClient, display_response

def render(api_url: str, session_id: str):
    """Render process testing UI"""
    st.header("Process Management")
    
    client = TerminalAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different process operations
    process_tabs = st.tabs(["Start Process", "Running Processes", "Process Interaction", "Process Output"])
    
    # Tab 1: Start Process
    with process_tabs[0]:
        st.subheader("Start Long-Running Process")
        
        command = st.text_input("Command", "python3 -c \"import time; i=0; while True: print(f'Count: {i}'); i+=1; time.sleep(1)\"")
        
        col1, col2 = st.columns(2)
        with col1:
            timeout = st.number_input("Timeout (seconds, 0 = no timeout)", min_value=0, value=300)
        
        with col2:
            show_env = st.checkbox("Add Environment Variables for Process")
        
        env_vars = {}
        if show_env:
            with st.expander("Environment Variables"):
                st.markdown("Add key-value pairs for environment variables")
                
                if 'process_env_vars' not in st.session_state:
                    st.session_state.process_env_vars = [{"key": "", "value": ""}]
                
                # Display existing variables
                for i, var in enumerate(st.session_state.process_env_vars):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        key = st.text_input("Key", var["key"], key=f"process_env_key_{i}")
                    with col2:
                        value = st.text_input("Value", var["value"], key=f"process_env_value_{i}")
                    with col3:
                        if i > 0 and st.button("Remove", key=f"process_env_remove_{i}"):
                            st.session_state.process_env_vars.pop(i)
                            st.rerun()
                    
                    st.session_state.process_env_vars[i]["key"] = key
                    st.session_state.process_env_vars[i]["value"] = value
                    
                    if key:
                        env_vars[key] = value
                
                if st.button("Add Environment Variable"):
                    st.session_state.process_env_vars.append({"key": "", "value": ""})
                    st.rerun()
        
        if st.button("Start Process"):
            if command:
                with st.spinner("Starting process..."):
                    response = client.start_process(session_id, command, timeout, env_vars if show_env else None)
                # Use without expander since we're not in an expander here
                display_response(response)
                
                # Store process ID in session state if successful
                if response["status_code"] == 201:
                    process_id = response["data"].get("id")
                    if process_id:
                        if 'running_processes' not in st.session_state:
                            st.session_state.running_processes = []
                        
                        # Add to running processes
                        process_info = {
                            "id": process_id,
                            "command": command,
                            "startTime": response["data"].get("startTime", ""),
                            "pid": response["data"].get("pid", 0)
                        }
                        st.session_state.running_processes.append(process_info)
                        st.success(f"Process started with ID: {process_id}")
            else:
                st.error("Please enter a command to execute")
    
    # Tab 2: List Running Processes
    with process_tabs[1]:
        st.subheader("Running Processes")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("Refresh Processes", key="refresh_processes"):
                with st.spinner("Fetching process list..."):
                    response = client.list_processes(session_id)
                
                if response["status_code"] == 200 and "processes" in response["data"]:
                    processes = response["data"]["processes"]
                    if processes:
                        # Update session state with latest processes
                        st.session_state.running_processes = []
                        for proc_id, proc_info in processes.items():
                            st.session_state.running_processes.append({
                                "id": proc_id,
                                "command": proc_info.get("command", ""),
                                "startTime": proc_info.get("startTime", ""),
                                "pid": proc_info.get("pid", 0),
                                "isRunning": proc_info.get("isRunning", False),
                                "exitCode": proc_info.get("exitCode", None)
                            })
                    else:
                        st.session_state.running_processes = []
        
        # Display running processes
        if 'running_processes' not in st.session_state:
            st.session_state.running_processes = []
        
        if not st.session_state.running_processes:
            st.info("No running processes found. Start a new process from the 'Start Process' tab.")
        else:
            for i, proc in enumerate(st.session_state.running_processes):
                with st.expander(f"{proc['command']} (ID: {proc['id']})", expanded=i==0):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.text(f"PID: {proc.get('pid', 'N/A')}")
                    with col2:
                        st.text(f"Started: {proc.get('startTime', 'N/A')}")
                    with col3:
                        if proc.get('isRunning', True):
                            st.text("Status: Running")
                        else:
                            st.text(f"Exit Code: {proc.get('exitCode', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("View Output", key=f"view_output_{i}"):
                            st.session_state.selected_process_id = proc['id']
                            st.rerun()
                    with col2:
                        if st.button("Send Signal", key=f"send_signal_{i}"):
                            st.session_state.signal_process_id = proc['id']
                            st.rerun()
    
    # Tab 3: Process Interaction
    with process_tabs[2]:
        st.subheader("Process Interaction")
        
        if 'running_processes' not in st.session_state:
            st.session_state.running_processes = []
        
        if not st.session_state.running_processes:
            st.info("No processes found. Start a new process first.")
        else:
            # Process selection
            process_options = {f"{proc['command']} (ID: {proc['id']})": proc['id'] for proc in st.session_state.running_processes}
            selected_option = st.selectbox("Select Process", options=list(process_options.keys()), key="interact_process_select")
            selected_process_id = process_options[selected_option] if selected_option else None
            
            if selected_process_id:
                with st.expander("Send Input to Process", expanded=True):
                    input_text = st.text_area("Input Text")
                    if st.button("Send Input"):
                        if input_text:
                            with st.spinner("Sending input..."):
                                response = client.send_process_input(session_id, selected_process_id, input_text)
                            # Use without expander since we're already in an expander
                            display_response(response, use_expander=False)
                        else:
                            st.error("Please enter input text to send")
                
                st.subheader("Send Signal to Process")
                signal_options = ["SIGTERM", "SIGKILL", "SIGINT", "SIGHUP"]
                signal = st.selectbox("Signal", options=signal_options)
                
                st.warning("⚠️ Sending a signal may terminate the process immediately!")
                confirm = st.checkbox("I understand and want to send the signal")
                
                if st.button("Send Signal"):
                    if confirm:
                        with st.spinner(f"Sending {signal}..."):
                            response = client.signal_process(session_id, selected_process_id, signal)
                        # Display without expander to avoid nesting
                        display_response(response, use_expander=False)
                        
                        # If successful, update process info and refresh
                        if response["status_code"] == 200:
                            st.success(f"Signal {signal} sent successfully")
                            # Refresh process list after a brief delay
                            time.sleep(1)
                            response = client.list_processes(session_id)
                            if response["status_code"] == 200:
                                if "processes" in response["data"]:
                                    # Update the process list
                                    st.session_state.running_processes = []
                                    for proc_id, proc_info in response["data"]["processes"].items():
                                        st.session_state.running_processes.append({
                                            "id": proc_id,
                                            "command": proc_info.get("command", ""),
                                            "startTime": proc_info.get("startTime", ""),
                                            "pid": proc_info.get("pid", 0),
                                            "isRunning": proc_info.get("isRunning", False),
                                            "exitCode": proc_info.get("exitCode", None)
                                        })
                            st.rerun()
                    else:
                        st.error("Please confirm by checking the checkbox before sending the signal")
    
    # Tab 4: Process Output
    with process_tabs[3]:
        st.subheader("Process Output")
        
        if 'running_processes' not in st.session_state:
            st.session_state.running_processes = []
        
        if not st.session_state.running_processes:
            st.info("No processes found. Start a new process first.")
        else:
            # Process selection
            process_options = {f"{proc['command']} (ID: {proc['id']})": proc['id'] for proc in st.session_state.running_processes}
            selected_option = st.selectbox("Select Process", options=list(process_options.keys()), key="output_process_select")
            selected_process_id = process_options[selected_option] if selected_option else None
            
            if selected_process_id:
                auto_refresh = st.checkbox("Auto-refresh (every 2 seconds)", value=False)
                
                if st.button("Get Output") or auto_refresh:
                    with st.spinner("Fetching output..."):
                        response = client.get_process_output(session_id, selected_process_id)
                    
                    if response["status_code"] == 200:
                        data = response["data"]
                        
                        # Show stdout
                        if "stdout" in data:
                            with st.expander("Standard Output", expanded=True):
                                stdout = data["stdout"]
                                if stdout:
                                    st.code("\n".join(stdout))
                                else:
                                    st.info("No standard output")
                        
                        # Show stderr
                        if "stderr" in data:
                            with st.expander("Standard Error", expanded=True):
                                stderr = data["stderr"]
                                if stderr:
                                    st.code("\n".join(stderr), language="bash")
                                else:
                                    st.info("No standard error")
                    else:
                        st.error(f"Failed to get output: {response['data'].get('error', 'Unknown error')}")
                
                if auto_refresh:
                    time.sleep(2)
                    st.rerun()

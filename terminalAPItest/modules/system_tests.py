import streamlit as st
from api_client import TerminalAPIClient, display_response

def render(api_url: str):
    """Render system information testing UI"""
    st.header("System Information")
    
    client = TerminalAPIClient(api_url)
    
    # Create tabs for different system operations
    system_tabs = st.tabs(["System Info", "Available Shells"])
    
    # Tab 1: System Info
    with system_tabs[0]:
        st.subheader("System Information")
        
        if st.button("Get System Info"):
            with st.spinner("Fetching system information..."):
                response = client.get_system_info()
            display_response(response)
            
            # Display system info in a more readable format
            if response["status_code"] == 200:
                info = response["data"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Hostname", info.get("hostname", "Unknown"))
                    st.metric("Operating System", info.get("os", "Unknown"))
                    st.metric("Architecture", info.get("architecture", "Unknown"))
                
                with col2:
                    st.metric("CPU Cores", info.get("numCPU", "Unknown"))
                    st.metric("Go Version", info.get("goVersion", "Unknown"))
                    st.metric("Working Directory", info.get("workingDir", "Unknown"))
                
                # Display current time and timezone
                st.subheader("Server Time")
                st.text(f"Current Time: {info.get('currentTime', 'Unknown')}")
                st.text(f"Timezone: {info.get('timezone', 'Unknown')}")
    
    # Tab 2: Available Shells
    with system_tabs[1]:
        st.subheader("Available Shells")
        
        if st.button("Get Available Shells"):
            with st.spinner("Fetching shell information..."):
                response = client.get_available_shells()
            display_response(response)
            
            # Display shells in a more readable format
            if response["status_code"] == 200:
                data = response["data"]
                
                st.subheader("Current Shell")
                st.info(data.get("currentShell", "Not set"))
                
                st.subheader("Available Shells")
                shells = data.get("availableShells", {})
                
                if shells:
                    # Create a list of shells with availability status
                    shell_list = []
                    for shell, available in shells.items():
                        shell_list.append({
                            "Shell": shell,
                            "Available": "Yes" if available else "No"
                        })
                    
                    # Display as dataframe
                    st.dataframe(shell_list)
                else:
                    st.info("No shell information available")

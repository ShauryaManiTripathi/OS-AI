import streamlit as st
from api_client import PocketFlowClient, display_response

def render(api_url: str):
    """Render session testing UI"""
    st.header("Session Management")
    
    client = PocketFlowClient(api_url)
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    # Column 1: Create and list sessions
    with col1:
        with st.expander("Create New Session", expanded=True):
            if st.button("Create Session"):
                response = client.create_session()
                display_response(response, use_expander=False)
                if response["status_code"] == 201:  # Successfully created
                    session_id = response["data"].get("id")
                    if session_id:
                        st.session_state.current_session_id = session_id
                        st.success(f"Set current session to: {session_id}")
        
        with st.expander("List All Sessions"):
            if st.button("Get All Sessions"):
                response = client.list_sessions()
                display_response(response, use_expander=False)
                
                # Also display the sessions in a nicer format if successful
                if response["status_code"] == 200 and "sessions" in response["data"]:
                    sessions = response["data"]["sessions"]
                    if sessions:
                        df_data = []
                        for session in sessions:
                            df_data.append({
                                "ID": session.get("id", ""),
                                "Created": session.get("createdAt", ""),
                                "Last Active": session.get("lastActive", ""),
                                "Working Dir": session.get("workingDir", ""),
                                "Active": "Yes" if session.get("isActive", False) else "No"
                            })
                        
                        if df_data:
                            st.dataframe(df_data)
                    else:
                        st.info("No sessions found")
    
    # Column 2: Session operations
    with col2:
        with st.expander("Get Session Details", expanded=True):
            session_id = st.text_input("Session ID", st.session_state.current_session_id, key="get_session_id")
            if st.button("Get Details"):
                if session_id:
                    response = client.get_session(session_id)
                    display_response(response, use_expander=False)
                    if response["status_code"] == 200:  # Successfully retrieved
                        st.session_state.current_session_id = session_id
                else:
                    st.error("Please enter a session ID")
        
        with st.expander("Set Working Directory"):
            session_id = st.text_input("Session ID", st.session_state.current_session_id, key="set_wd_session_id")
            directory = st.text_input("Working Directory", "/tmp")
            if st.button("Set Directory"):
                if session_id and directory:
                    response = client.set_working_directory(session_id, directory)
                    display_response(response, use_expander=False)
                else:
                    st.error("Please enter both session ID and directory")
        
        with st.expander("Delete Session"):
            session_id = st.text_input("Session ID", st.session_state.current_session_id, key="delete_session_id")
            if st.button("Delete Session"):
                if session_id:
                    delete_confirmation = st.checkbox("Confirm deletion?")
                    if delete_confirmation:
                        response = client.delete_session(session_id)
                        display_response(response, use_expander=False)
                        if response["status_code"] == 204 and st.session_state.current_session_id == session_id:
                            st.session_state.current_session_id = ""
                            st.warning("Current session has been deleted")
                else:
                    st.error("Please enter a session ID")
    
    # Display current session selection UI
    st.subheader("Select Current Working Session")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_session = st.text_input("Set active session ID", st.session_state.current_session_id)
    
    with col2:
        if st.button("Set as Current"):
            if selected_session:
                # Verify the session exists
                response = client.get_session(selected_session)
                if response["status_code"] == 200:
                    st.session_state.current_session_id = selected_session
                    st.success(f"Current session set to: {selected_session}")
                else:
                    st.error("Invalid session ID")
            else:
                st.error("Please enter a session ID")

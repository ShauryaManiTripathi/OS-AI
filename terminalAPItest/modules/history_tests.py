import streamlit as st
from api_client import TerminalAPIClient, display_response

def render(api_url: str, session_id: str):
    """Render command history testing UI"""
    st.header("Command History")
    
    client = TerminalAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different history operations
    history_tabs = st.tabs(["View History", "Search History", "Manage History"])
    
    # Tab 1: View History
    with history_tabs[0]:
        st.subheader("Command History")
        
        limit = st.number_input("Limit (0 for all)", min_value=0, value=10)
        
        if st.button("Get Command History"):
            with st.spinner("Fetching history..."):
                response = client.get_history(session_id, limit)
            # Using standard display_response since we're not inside an expander
            display_response(response)
            
            # Display history in a more user-friendly format
            if response["status_code"] == 200 and "history" in response["data"]:
                history = response["data"]["history"]
                if history:
                    st.subheader(f"Command History ({len(history)} entries)")
                    
                    for i, entry in enumerate(history):
                        with st.expander(f"{entry.get('command', 'Unknown command')}", expanded=i==0):
                            st.text(f"Timestamp: {entry.get('timestamp', 'Unknown')}")
                            
                            # Add a button to re-run the command
                            if st.button("Re-run Command", key=f"rerun_{i}"):
                                st.session_state.command_to_run = entry.get("command", "")
                                st.info(f"Command copied: {st.session_state.command_to_run}")
                                st.info("Go to the Commands tab to execute it")
                else:
                    st.info("No command history found")
    
    # Tab 2: Search History
    with history_tabs[1]:
        st.subheader("Search Command History")
        
        search_query = st.text_input("Search Query")
        
        if st.button("Search History"):
            if search_query:
                with st.spinner("Searching..."):
                    response = client.search_history(session_id, search_query)
                # Using standard display_response since we're not inside an expander
                display_response(response)
                
                # Display search results
                if response["status_code"] == 200 and "history" in response["data"]:
                    results = response["data"]["history"]
                    if results:
                        st.subheader(f"Search Results ({len(results)} matches)")
                        
                        for i, entry in enumerate(results):
                            with st.expander(f"{entry.get('command', 'Unknown command')}", expanded=i==0):
                                st.text(f"Timestamp: {entry.get('timestamp', 'Unknown')}")
                                
                                # Add a button to re-run the command
                                if st.button("Re-run Command", key=f"search_rerun_{i}"):
                                    st.session_state.command_to_run = entry.get("command", "")
                                    st.info(f"Command copied: {st.session_state.command_to_run}")
                                    st.info("Go to the Commands tab to execute it")
                    else:
                        st.info(f"No commands found matching '{search_query}'")
            else:
                st.error("Please enter a search query")
    
    # Tab 3: Manage History
    with history_tabs[2]:
        st.subheader("Manage Command History")
        
        if st.button("Clear Command History"):
            confirm = st.checkbox("Confirm clearing history?")
            if confirm:
                with st.spinner("Clearing history..."):
                    response = client.clear_history(session_id)
                # Use standard display_response since we're not in an expander
                display_response(response)
                
                if response["status_code"] == 200:
                    st.success("Command history cleared")
            else:
                st.warning("Please confirm before clearing history")

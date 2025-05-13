import streamlit as st
from api_client import PocketFlowClient, display_response

def render(api_url: str, session_id: str):
    """Render file testing UI"""
    st.header("File Operations")
    
    client = PocketFlowClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different file operations
    file_tabs = st.tabs(["List Files", "Read/View Files", "Create/Edit Files", "Delete Files", "Search Files"])
    
    # Tab 1: List Files
    with file_tabs[0]:
        st.subheader("List Files")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            directory_path = st.text_input("Directory Path", ".", key="list_dir_path")
        
        with col2:
            include_metadata = st.checkbox("Include Metadata")
        
        if st.button("List Files"):
            if include_metadata:
                response = client.list_files_with_metadata(session_id, directory_path)
            else:
                response = client.list_files(session_id, directory_path)
            
            display_response(response, use_expander=True)
    
    # Tab 2: Read Files
    with file_tabs[1]:
        st.subheader("Read File")
        
        file_path = st.text_input("File Path", key="read_file_path")
        
        if st.button("Read File"):
            if file_path:
                response = client.get_file(session_id, file_path)
                display_response(response)
                
                # If successful, display file content in a more readable format
                if response["status_code"] == 200 and "content" in response["data"]:
                    content = response["data"]["content"]
                    st.subheader("File Content")
                    
                    # Determine if it's likely code and should be displayed with syntax highlighting
                    extension = file_path.split('.')[-1] if '.' in file_path else None
                    code_extensions = ['py', 'js', 'html', 'css', 'go', 'json', 'md', 'ts', 'sh', 'bat', 'c', 'cpp', 'java']
                    
                    if extension and extension.lower() in code_extensions:
                        st.code(content, language=extension.lower())
                    else:
                        st.text_area("Content", content, height=300)
            else:
                st.error("Please enter a file path")
    
    # Tab 3: Create/Edit Files
    with file_tabs[2]:
        st.subheader("Create or Update File")
        
        file_path = st.text_input("File Path", key="create_file_path")
        file_content = st.text_area("File Content", "", height=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create File"):
                if file_path and file_content:
                    response = client.create_file(session_id, file_path, file_content)
                    display_response(response)
                else:
                    st.error("Please enter both file path and content")
        
        with col2:
            if st.button("Update File"):
                if file_path and file_content:
                    response = client.update_file(session_id, file_path, file_content)
                    display_response(response)
                else:
                    st.error("Please enter both file path and content")
    
    # Tab 4: Delete Files
    with file_tabs[3]:
        st.subheader("Delete File")
        
        file_path = st.text_input("File Path", key="delete_file_path")
        confirm_delete = st.checkbox("Confirm deletion?", key="confirm_delete_file")
        
        if st.button("Delete File"):
            if file_path:
                if confirm_delete:
                    response = client.delete_file(session_id, file_path)
                    display_response(response)
                else:
                    st.warning("Please confirm deletion by checking the box")
            else:
                st.error("Please enter a file path")
    
    # Tab 5: Search Files
    with file_tabs[4]:
        st.subheader("Search in Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_pattern = st.text_input("Search Pattern", key="search_pattern")
            search_dir = st.text_input("Search Directory", ".", key="search_dir")
        
        with col2:
            recursive_search = st.checkbox("Recursive Search")
        
        if st.button("Search Files"):
            if search_pattern:
                response = client.search_files(session_id, search_pattern, search_dir, recursive_search)
                display_response(response)
                
                # Display search results in a more structured way if successful
                if response["status_code"] == 200 and "results" in response["data"]:
                    results = response["data"]["results"]
                    if results:
                        st.subheader("Search Results")
                        
                        for file_path, matches in results.items():
                            with st.expander(f"File: {file_path} ({len(matches)} matches)"):
                                for i, match in enumerate(matches):
                                    st.text(f"{i+1}. {match}")
                    else:
                        st.info("No matches found")
            else:
                st.error("Please enter a search pattern")

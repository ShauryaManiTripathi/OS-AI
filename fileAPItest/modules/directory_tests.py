import streamlit as st
from api_client import PocketFlowClient, display_response
import json

def render(api_url: str, session_id: str):
    """Render directory testing UI"""
    st.header("Directory Operations")
    
    client = PocketFlowClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different directory operations
    dir_tabs = st.tabs(["List Directories", "Directory Tree", "Create Directory", "Delete Directory", "Directory Size"])
    
    # Tab 1: List Directories
    with dir_tabs[0]:
        st.subheader("List Directories")
        
        directory_path = st.text_input("Directory Path", ".", key="list_dirs_path")
        
        if st.button("List Directories"):
            response = client.list_directories(session_id, directory_path)
            display_response(response, use_expander=True)
            
            # If successful, display directories in a nicer format
            if response["status_code"] == 200 and "directories" in response["data"]:
                directories = response["data"]["directories"]
                if directories:
                    st.subheader("Directories")
                    for i, directory in enumerate(directories):
                        st.text(f"{i+1}. {directory}")
                else:
                    st.info("No directories found")
    
    # Tab 2: Directory Tree
    with dir_tabs[1]:
        st.subheader("Directory Tree Visualization")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            directory_path = st.text_input("Directory Path", ".", key="tree_dir_path")
        
        with col2:
            depth = st.number_input("Depth", min_value=1, max_value=10, value=2)
        
        if st.button("Get Directory Tree"):
            response = client.get_directory_tree(session_id, directory_path, depth)
            display_response(response)
            
            # If successful, display tree in a nicer format
            if response["status_code"] == 200 and "tree" in response["data"]:
                tree = response["data"]["tree"]
                if tree:
                    st.subheader("Directory Tree")
                    # You could implement a recursive tree visualization here
                    st.json(tree)  # For now, just showing the JSON
                else:
                    st.info("Empty directory or no access")
    
    # Tab 3: Create Directory
    with dir_tabs[2]:
        st.subheader("Create Directory")
        
        directory_path = st.text_input("Directory Path", key="create_dir_path")
        
        if st.button("Create Directory"):
            if directory_path:
                response = client.create_directory(session_id, directory_path)
                display_response(response)
            else:
                st.error("Please enter a directory path")
    
    # Tab 4: Delete Directory
    with dir_tabs[3]:
        st.subheader("Delete Directory")
        
        directory_path = st.text_input("Directory Path", key="delete_dir_path")
        confirm_delete = st.checkbox("Confirm deletion? This will delete all contents within the directory!", key="confirm_delete_dir")
        
        if st.button("Delete Directory"):
            if directory_path:
                if confirm_delete:
                    response = client.delete_directory(session_id, directory_path)
                    display_response(response)
                else:
                    st.warning("Please confirm deletion by checking the box")
            else:
                st.error("Please enter a directory path")
                
    # Tab 5: Directory Size
    with dir_tabs[4]:
        st.subheader("Calculate Directory Size")
        
        directory_path = st.text_input("Directory Path", ".", key="size_dir_path")
        
        if st.button("Calculate Size"):
            if directory_path:
                response = client.get_directory_size(session_id, directory_path)
                display_response(response)
                
                # Display size in a nicer format if successful
                if response["status_code"] == 200 and "size" in response["data"]:
                    size_bytes = response["data"]["size"]
                    size_formatted = response["data"].get("sizeFormatted", "")
                    
                    st.success(f"Directory Size: {size_formatted if size_formatted else size_bytes} bytes")
            else:
                st.error("Please enter a directory path")

def render_tree(tree, prefix=""):
    """Helper function to render a directory tree recursively"""
    lines = []
    for i, item in enumerate(tree):
        is_last = i == len(tree) - 1
        lines.append(f"{prefix}{'└── ' if is_last else '├── '}{item['name']}")
        
        if item.get('children'):
            lines.extend(render_tree(
                item['children'], 
                prefix + ('    ' if is_last else '│   ')
            ))
    
    return lines

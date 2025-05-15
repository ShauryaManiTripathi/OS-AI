import os
import json
import time
import streamlit as st
import pandas as pd
import plotly.express as px
from fileapi_client import FileAPIClient
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="FileAPI Tester",
    page_icon="📁",
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
    .file-content {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-family: monospace;
        overflow: auto;
        white-space: pre-wrap;
    }
    .info-panel {
        background-color: #e2e3e5;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None

if 'current_file_content' not in st.session_state:
    st.session_state.current_file_content = ""

if 'current_file_path' not in st.session_state:
    st.session_state.current_file_path = ""

# Sidebar for configuration and navigation
with st.sidebar:
    st.title("FileAPI Tester")
    
    # Connection settings
    st.header("Server Connection")
    server_url = st.text_input("Server URL", value="http://localhost:8080")
    
    if st.button("Connect"):
        try:
            st.session_state.client = FileAPIClient(base_url=server_url)
            st.success("Connected successfully!")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
    
    # Navigation
    st.header("Navigation")
    page = st.radio(
        "Select Operation",
        [
            "Session Management",
            "File Operations",
            "Directory Operations",
            "Project Operations",
            "Diff & Patch Operations"
        ]
    )

# Helper function to check if client is connected
def check_client():
    if st.session_state.client is None:
        st.warning("Please connect to a server first using the sidebar.")
        return False
    return True

# Helper function to format file size
def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# Helper function to display a code editor
def code_editor(content, key, language="plaintext"):
    return st.text_area("Edit content", value=content, height=300, key=key)

# Helper function to display a pretty JSON
def display_json(data):
    st.json(data)

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

# File Operations Page
elif page == "File Operations":
    st.title("File Operations")
    
    if not check_client():
        st.stop()
    
    tabs = st.tabs([
        "List Files", 
        "Create/Edit File", 
        "File Metadata", 
        "Delete File", 
        "Batch Operations", 
        "Search"
    ])
    
    # List Files tab
    with tabs[0]:
        st.subheader("List Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            path = st.text_input("Directory Path", value=".", key="list_files_path")
            include_metadata = st.checkbox("Include Metadata")
            
            if st.button("List Files"):
                try:
                    if include_metadata:
                        files = st.session_state.client.list_files_with_metadata(path)
                        
                        if not files:
                            st.info(f"No files found in '{path}'")
                        else:
                            file_data = []
                            for file in files:
                                file_data.append({
                                    "Name": file["name"],
                                    "Path": file["path"],
                                    "Size": format_size(file["size"]),
                                    "Modified": file["modTime"],
                                    "Type": file.get("contentType", "Unknown")
                                })
                            st.dataframe(pd.DataFrame(file_data))
                            
                    else:
                        files = st.session_state.client.list_files(path)
                        
                        if not files:
                            st.info(f"No files found in '{path}'")
                        else:
                            st.write(f"Files in '{path}':")
                            for file in files:
                                st.write(f"- {file}")
                except Exception as e:
                    st.error(f"Error listing files: {str(e)}")
    
    # Create/Edit File tab
    with tabs[1]:
        st.subheader("Create or Edit File")
        
        file_path = st.text_input("File Path", value=st.session_state.current_file_path, key="file_path")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Load File"):
                try:
                    content = st.session_state.client.get_file(file_path)
                    st.session_state.current_file_content = content
                    st.session_state.current_file_path = file_path
                    st.success(f"Loaded file: {file_path}")
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        
        with col2:
            file_exists = "New File"
            try:
                if st.session_state.client.file_exists(file_path):
                    file_exists = "Existing File"
            except:
                pass
            
            st.info(file_exists)
        
        content = code_editor(st.session_state.current_file_content, key="file_content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save File"):
                try:
                    if st.session_state.client.file_exists(file_path):
                        st.session_state.client.update_file(file_path, content)
                        st.success(f"Updated file: {file_path}")
                    else:
                        st.session_state.client.create_file(file_path, content)
                        st.success(f"Created file: {file_path}")
                    
                    st.session_state.current_file_content = content
                except Exception as e:
                    st.error(f"Error saving file: {str(e)}")
        
        with col2:
            if st.button("Create Backup"):
                try:
                    backup_path = st.session_state.client.backup_file(file_path)
                    st.success(f"Created backup at: {backup_path}")
                except Exception as e:
                    st.error(f"Error creating backup: {str(e)}")
    
    # File Metadata tab
    with tabs[2]:
        st.subheader("File Metadata")
        
        meta_path = st.text_input("File Path", key="metadata_path")
        
        if st.button("Get Metadata"):
            try:
                metadata = st.session_state.client.get_file_metadata(meta_path)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Name:", metadata["name"])
                    st.write("Path:", metadata["path"])
                    st.write("Size:", format_size(metadata["size"]))
                
                with col2:
                    st.write("Modified:", metadata["modTime"])
                    st.write("Is Directory:", metadata["isDir"])
                    st.write("Content Type:", metadata.get("contentType", "Unknown"))
                    st.write("Permissions:", metadata.get("permissions", "Unknown"))
            except Exception as e:
                st.error(f"Error getting metadata: {str(e)}")
    
    # Delete File tab
    with tabs[3]:
        st.subheader("Delete File")
        
        delete_path = st.text_input("File Path to Delete", key="delete_path")
        
        # Confirmation checkbox
        confirm_delete = st.checkbox("I confirm I want to delete this file")
        
        if st.button("Delete File", disabled=not confirm_delete):
            try:
                st.session_state.client.delete_file(delete_path)
                st.success(f"Deleted file: {delete_path}")
            except Exception as e:
                st.error(f"Error deleting file: {str(e)}")
    
    # Batch Operations tab
    with tabs[4]:
        st.subheader("Batch Operations")
        
        operation_type = st.selectbox(
            "Operation Type",
            ["Batch Read", "Extract Content", "Batch Create"]
        )
        
        if operation_type == "Batch Read" or operation_type == "Extract Content":
            file_paths_input = st.text_area(
                "Enter file paths (one per line)",
                height=150,
                key="batch_paths"
            )
            
            file_paths = [path.strip() for path in file_paths_input.split("\n") if path.strip()]
            
            if st.button("Execute Batch Operation"):
                if not file_paths:
                    st.warning("Please enter at least one file path.")
                else:
                    try:
                        if operation_type == "Batch Read":
                            results = st.session_state.client.batch_read_files(file_paths)
                            
                            for result in results:
                                with st.expander(f"{result['path']} - {'Success' if result['success'] else 'Failed'}"):
                                    if result['success']:
                                        st.code(result['result'], language="")
                                    else:
                                        st.error(result['error'])
                            
                        else:  # Extract Content
                            results = st.session_state.client.extract_content(file_paths)
                            
                            for path, content in results.items():
                                with st.expander(path):
                                    if content.startswith("ERROR:"):
                                        st.error(content)
                                    else:
                                        st.code(content, language="")
                    except Exception as e:
                        st.error(f"Error executing batch operation: {str(e)}")
        
        elif operation_type == "Batch Create":
            num_files = st.number_input("Number of files to create", min_value=1, max_value=10, value=2)
            
            files_data = {}
            for i in range(num_files):
                st.subheader(f"File {i+1}")
                file_path = st.text_input(f"File path {i+1}", key=f"batch_create_path_{i}")
                file_content = st.text_area(f"Content {i+1}", height=100, key=f"batch_create_content_{i}")
                
                if file_path:
                    files_data[file_path] = file_content
            
            if st.button("Create Files"):
                if not files_data:
                    st.warning("Please enter at least one file path and content.")
                else:
                    try:
                        result = st.session_state.client.batch_create_files(files_data)
                        
                        success_count = 0
                        failure_count = 0
                        
                        for file_result in result.get("results", []):
                            if file_result["success"]:
                                success_count += 1
                            else:
                                failure_count += 1
                                st.error(f"Failed to create {file_result['path']}: {file_result.get('error', 'Unknown error')}")
                        
                        st.success(f"Successfully created {success_count} files, {failure_count} failed.")
                    except Exception as e:
                        st.error(f"Error creating files: {str(e)}")
    
    # Search tab
    with tabs[5]:
        st.subheader("Search Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_pattern = st.text_input("Search Pattern", key="search_pattern")
            search_path = st.text_input("Directory to Search", value=".", key="search_path")
        
        with col2:
            search_recursive = st.checkbox("Search Recursively", value=True)
        
        if st.button("Search"):
            if not search_pattern:
                st.warning("Please enter a search pattern.")
            else:
                try:
                    results = st.session_state.client.search_files(search_pattern, search_path, search_recursive)
                    
                    st.write(f"Found matches in {results['matchedFiles']} files.")
                    
                    for file_path, matches in results.get("results", {}).items():
                        with st.expander(file_path):
                            for match in matches:
                                st.code(match, language="")
                except Exception as e:
                    st.error(f"Error searching files: {str(e)}")

# Directory Operations Page
elif page == "Directory Operations":
    st.title("Directory Operations")
    
    if not check_client():
        st.stop()
    
    tabs = st.tabs([
        "List Directories", 
        "Create Directory", 
        "Delete Directory", 
        "Directory Tree", 
        "Directory Size"
    ])
    
    # List Directories tab
    with tabs[0]:
        st.subheader("List Directories")
        
        list_dir_path = st.text_input("Directory Path", value=".", key="list_dir_path")
        
        if st.button("List Directories"):
            try:
                directories = st.session_state.client.list_directories(list_dir_path)
                
                if not directories:
                    st.info(f"No subdirectories found in '{list_dir_path}'")
                else:
                    st.write(f"Directories in '{list_dir_path}':")
                    for directory in directories:
                        st.write(f"- {directory}")
            except Exception as e:
                st.error(f"Error listing directories: {str(e)}")
    
    # Create Directory tab
    with tabs[1]:
        st.subheader("Create Directory")
        
        create_dir_path = st.text_input("Directory Path to Create", key="create_dir_path")
        
        if st.button("Create Directory"):
            try:
                result = st.session_state.client.create_directory(create_dir_path)
                st.success(f"Created directory: {create_dir_path}")
            except Exception as e:
                st.error(f"Error creating directory: {str(e)}")
    
    # Delete Directory tab
    with tabs[2]:
        st.subheader("Delete Directory")
        
        delete_dir_path = st.text_input("Directory Path to Delete", key="delete_dir_path")
        
        # Confirmation checkbox
        confirm_delete_dir = st.checkbox("I confirm I want to delete this directory and all its contents")
        
        if st.button("Delete Directory", disabled=not confirm_delete_dir):
            try:
                st.session_state.client.delete_directory(delete_dir_path)
                st.success(f"Deleted directory: {delete_dir_path}")
            except Exception as e:
                st.error(f"Error deleting directory: {str(e)}")
    
    # Directory Tree tab
    with tabs[3]:
        st.subheader("Directory Tree")
        
        tree_path = st.text_input("Directory Path", value=".", key="tree_path")
        tree_depth = st.slider("Tree Depth", min_value=1, max_value=10, value=2)
        
        if st.button("Show Directory Tree"):
            try:
                tree_result = st.session_state.client.get_directory_tree(tree_path, tree_depth)
                
                # Function to recursively display the tree structure
                def display_tree(entries, indent=""):
                    for entry in entries:
                        if entry["isDir"]:
                            st.markdown(f"{indent}📁 **{entry['name']}**")
                            if "children" in entry and entry["children"]:
                                display_tree(entry["children"], indent + "&nbsp;&nbsp;&nbsp;&nbsp;")
                        else:
                            size_str = format_size(entry.get("size", 0))
                            st.markdown(f"{indent}📄 {entry['name']} ({size_str})")
                
                st.write(f"Directory Tree for '{tree_result['path']}':")
                display_tree(tree_result["tree"])
                
            except Exception as e:
                st.error(f"Error getting directory tree: {str(e)}")
    
    # Directory Size tab
    with tabs[4]:
        st.subheader("Directory Size")
        
        size_path = st.text_input("Directory Path", value=".", key="size_path")
        
        if st.button("Calculate Size"):
            try:
                size_result = st.session_state.client.get_directory_size(size_path)
                
                st.write(f"Directory: {size_result['path']}")
                st.write(f"Size: {size_result['sizeFormatted']} ({size_result['size']} bytes)")
                
                # Create a simple chart if there are more than 0 bytes
                if size_result['size'] > 0:
                    st.write("Size visualization:")
                    st.progress(1.0)
                
            except Exception as e:
                st.error(f"Error calculating directory size: {str(e)}")

# Project Operations Page
elif page == "Project Operations":
    st.title("Project Operations")
    
    if not check_client():
        st.stop()
    
    tabs = st.tabs([
        "Project Summary", 
        "Code Context", 
        "File Structure",
        "Batch Create Files"
    ])
    
    # Project Summary tab
    with tabs[0]:
        st.subheader("Project Summary")
        
        if st.button("Get Project Summary"):
            try:
                summary = st.session_state.client.get_project_summary()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Project Name:", summary["name"])
                    st.write("Root Path:", summary["rootPath"])
                    st.write("File Count:", summary["fileCount"])
                    st.write("Directory Count:", summary["dirCount"])
                    st.write("Total Size:", format_size(summary["totalSize"]))
                
                with col2:
                    st.subheader("Key Files")
                    if "keyFiles" in summary and summary["keyFiles"]:
                        for key_file in summary["keyFiles"]:
                            st.write(f"- {key_file}")
                    else:
                        st.info("No key files detected")
                
                if "fileTypes" in summary and summary["fileTypes"]:
                    st.subheader("File Types")
                    
                    # Prepare data for chart
                    file_types_data = []
                    for file_type, count in summary["fileTypes"].items():
                        type_name = file_type if file_type else "No extension"
                        file_types_data.append({"Type": type_name, "Count": count})
                    
                    # Create DataFrame
                    df = pd.DataFrame(file_types_data)
                    
                    # Create chart
                    fig = px.bar(df, x="Type", y="Count", title="File Types Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                if "recentFiles" in summary and summary["recentFiles"]:
                    st.subheader("Recent Files")
                    for file in summary["recentFiles"]:
                        st.write(f"- {file['path']} (Modified: {file['modTime']})")
            except Exception as e:
                st.error(f"Error getting project summary: {str(e)}")
    
    # Code Context tab
    with tabs[1]:
        st.subheader("Extract Code Context")
        
        max_files = st.slider("Maximum Files to Include", min_value=1, max_value=20, value=5)
        
        if st.button("Extract Code Context"):
            try:
                context = st.session_state.client.extract_code_context(max_files)
                
                st.write("Project Name:", context["projectName"])
                
                # Project dependencies
                if "projectDependencies" in context and context["projectDependencies"]:
                    with st.expander("Project Dependencies"):
                        for dep in context["projectDependencies"]:
                            st.write(f"- {dep}")
                
                # Main files
                if "mainFiles" in context and context["mainFiles"]:
                    st.subheader("Main Files")
                    for file_path, file_info in context["mainFiles"].items():
                        with st.expander(f"{file_path} ({file_info.get('language', 'Unknown')})"):
                            st.code(file_info["content"], language=file_info.get("language", "").lower())
                            
                            if "dependencies" in file_info and file_info["dependencies"]:
                                st.write("Dependencies:")
                                for dep in file_info["dependencies"]:
                                    st.write(f"- {dep}")
                            
                            st.write(f"Size: {format_size(file_info['size'])}")
                            if "modTime" in file_info:
                                st.write(f"Modified: {file_info['modTime']}")
                
                # File structure visualization
                if "fileStructure" in context:
                    with st.expander("File Structure"):
                        st.json(context["fileStructure"])
                
            except Exception as e:
                st.error(f"Error extracting code context: {str(e)}")
    
    # File Structure tab
    with tabs[2]:
        st.subheader("File Structure")
        
        structure_path = st.text_input("Directory Path", value=".", key="structure_path")
        structure_depth = st.slider("Structure Depth", min_value=1, max_value=10, value=3, key="structure_depth")
        
        if st.button("Export File Structure"):
            try:
                structure = st.session_state.client.export_file_structure(structure_path, structure_depth)
                
                st.write(f"Structure for '{structure['path']}' with depth {structure['depth']}:")
                st.json(json.loads(structure["structure"]))
            except Exception as e:
                st.error(f"Error exporting file structure: {str(e)}")
    
    # Batch Create Files tab
    with tabs[3]:
        st.subheader("Batch Create Files")
        
        file_templates = {
            "Empty": "",
            "Python Script": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()\n",
            "HTML File": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Title</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>",
            "Markdown": "# Title\n\n## Section\n\nContent here.\n",
            "JSON": "{\n    \"key\": \"value\"\n}"
        }
        
        num_batch_files = st.number_input("Number of files to create", min_value=1, max_value=10, value=2)
        
        batch_files_data = {}
        for i in range(num_batch_files):
            st.subheader(f"File {i+1}")
            batch_file_path = st.text_input(f"File path {i+1}", key=f"project_batch_path_{i}")
            
            template = st.selectbox(
                f"Template for file {i+1}",
                options=list(file_templates.keys()),
                key=f"template_{i}"
            )
            
            default_content = file_templates[template]
            batch_file_content = st.text_area(
                f"Content {i+1}", 
                value=default_content, 
                height=150, 
                key=f"project_batch_content_{i}"
            )
            
            if batch_file_path:
                batch_files_data[batch_file_path] = batch_file_content
        
        if st.button("Create Files"):
            if not batch_files_data:
                st.warning("Please enter at least one file path and content.")
            else:
                try:
                    result = st.session_state.client.batch_create_files(batch_files_data)
                    
                    success_count = 0
                    failure_count = 0
                    
                    for file_result in result.get("results", []):
                        if file_result["success"]:
                            success_count += 1
                        else:
                            failure_count += 1
                            st.error(f"Failed to create {file_result['path']}: {file_result.get('error', 'Unknown error')}")
                    
                    st.success(f"Successfully created {success_count} files, {failure_count} failed.")
                except Exception as e:
                    st.error(f"Error creating files: {str(e)}")

# Diff & Patch Operations Page
elif page == "Diff & Patch Operations":
    st.title("Diff & Patch Operations")
    
    if not check_client():
        st.stop()
    
    tabs = st.tabs([
        "Generate Diff", 
        "Apply Patch"
    ])
    
    # Generate Diff tab
    with tabs[0]:
        st.subheader("Generate Diff")
        
        diff_method = st.radio(
            "Diff Method",
            ["Content Diff", "File Diff"]
        )
        
        if diff_method == "Content Diff":
            original_content = st.text_area("Original Content", height=200, key="original_content")
            modified_content = st.text_area("Modified Content", height=200, key="modified_content")
            
            if st.button("Generate Diff"):
                if not original_content or not modified_content:
                    st.warning("Please enter both original and modified content.")
                else:
                    try:
                        diff_result = st.session_state.client.generate_diff(
                            original_content=original_content,
                            modified_content=modified_content
                        )
                        
                        st.subheader("Diff Result")
                        st.code(diff_result["patches"], language="diff")
                        
                        # Store in session state for patch tab
                        st.session_state.last_diff = diff_result["patches"]
                        st.session_state.last_original = original_content
                    except Exception as e:
                        st.error(f"Error generating diff: {str(e)}")
        else:  # File Diff
            original_path = st.text_input("Original File Path", key="original_path")
            modified_path = st.text_input("Modified File Path", key="modified_path")
            
            if st.button("Generate Diff"):
                if not original_path or not modified_path:
                    st.warning("Please enter both original and modified file paths.")
                else:
                    try:
                        diff_result = st.session_state.client.generate_diff(
                            original_path=original_path,
                            modified_path=modified_path
                        )
                        
                        st.subheader("Diff Result")
                        st.code(diff_result["patches"], language="diff")
                        
                        # Store in session state for patch tab
                        st.session_state.last_diff = diff_result["patches"]
                        
                        # Get original content for patch tab
                        try:
                            original_content = st.session_state.client.get_file(original_path)
                            st.session_state.last_original = original_content
                            st.session_state.last_file_path = original_path
                        except:
                            pass
                            
                    except Exception as e:
                        st.error(f"Error generating diff: {str(e)}")
    
    # Apply Patch tab
    with tabs[1]:
        st.subheader("Apply Patch")
        
        # Get last diff and original content from session state if available
        last_diff = st.session_state.get("last_diff", "")
        last_original = st.session_state.get("last_original", "")
        last_file_path = st.session_state.get("last_file_path", "")
        
        original_content_for_patch = st.text_area("Original Content", value=last_original, height=200, key="patch_original")
        patches_content = st.text_area("Patches", value=last_diff, height=200, key="patches")
        
        apply_to_file = st.checkbox("Apply to File")
        
        file_path_for_patch = ""
        if apply_to_file:
            file_path_for_patch = st.text_input("File Path", value=last_file_path, key="patch_file_path")
        
        if st.button("Apply Patch"):
            if not patches_content:
                st.warning("Please enter patches to apply.")
            elif apply_to_file and not file_path_for_patch:
                st.warning("Please enter a file path.")
            else:
                try:
                    if apply_to_file:
                        # Use the simplified API - no need to pass original content
                        result = st.session_state.client.apply_patch(
                            file_path=file_path_for_patch,
                            patches=patches_content
                        )
                        st.success(f"Patch applied to file: {file_path_for_patch}")
                    else:
                        # For content-only patching, still use original API
                        result = st.session_state.client.apply_patch(
                            file_path=None,
                            patches=patches_content
                        )
                    
                    st.subheader("Patched Result")
                    st.code(result["result"], language="")
                except Exception as e:
                    st.error(f"Error applying patch: {str(e)}")

# Footer
st.markdown("""
---
<div style="text-align: center">
    FileAPI Tester - A comprehensive client for testing the FileAPI server
</div>
""", unsafe_allow_html=True)

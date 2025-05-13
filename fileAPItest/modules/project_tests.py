import streamlit as st
from api_client import FileAPIClient, display_response
import json

def render(api_url: str, session_id: str):
    """Render project testing UI"""
    st.header("Project Operations")
    
    client = FileAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for different project operations
    project_tabs = st.tabs(["Project Summary", "Code Context", "File Structure", "Batch File Creation"])
    
    # Tab 1: Project Summary
    with project_tabs[0]:
        st.subheader("Project Summary")
        
        if st.button("Get Project Summary"):
            response = client.get_project_summary(session_id)
            display_response(response)
            
            # If successful, display summary in a more structured way
            if response["status_code"] == 200:
                data = response["data"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Project Name", data.get("name", ""))
                    st.metric("File Count", data.get("fileCount", 0))
                    st.metric("Directory Count", data.get("dirCount", 0))
                
                with col2:
                    # Format size nicely
                    size = data.get("totalSize", 0)
                    size_str = format_size(size)
                    st.metric("Total Size", size_str)
                    
                    # Display file types distribution
                    if "fileTypes" in data:
                        st.subheader("File Types")
                        file_types = data["fileTypes"]
                        for ext, count in file_types.items():
                            st.text(f"{ext or 'no extension'}: {count} files")
                
                # Key files
                if "keyFiles" in data and data["keyFiles"]:
                    with st.expander("Key Project Files"):
                        for key_file in data["keyFiles"]:
                            st.text(key_file)
                
                # Recent files
                if "recentFiles" in data and data["recentFiles"]:
                    with st.expander("Recent Files"):
                        for rf in data["recentFiles"]:
                            st.text(f"{rf.get('path')} ({format_size(rf.get('size', 0))})")
    
    # Tab 2: Code Context
    with project_tabs[1]:
        st.subheader("Code Context for LLMs")
        
        max_files = st.slider("Max Files to Include", min_value=1, max_value=20, value=5)
        
        if st.button("Extract Code Context"):
            response = client.extract_code_context(session_id, max_files)
            display_response(response)
            
            # If successful, show a structured view of the context
            if response["status_code"] == 200:
                data = response["data"]
                
                st.subheader(f"Code Context for {data.get('projectName', 'Project')}")
                
                # Display dependencies
                if "dependencies" in data and data["dependencies"]:
                    with st.expander("Dependencies", expanded=True):
                        for dep in data["dependencies"]:
                            st.code(dep)
                
                # Main files content
                if "mainFiles" in data and data["mainFiles"]:
                    with st.expander("Main Files Content", expanded=True):
                        file_select = st.selectbox(
                            "Select a file to view",
                            options=list(data["mainFiles"].keys())
                        )
                        
                        if file_select:
                            content = data["mainFiles"].get(file_select, "")
                            if content:
                                # Try to determine language from file extension
                                extension = file_select.split('.')[-1] if '.' in file_select else None
                                if extension:
                                    st.code(content, language=extension)
                                else:
                                    st.code(content)
    
    # Tab 3: File Structure
    with project_tabs[2]:
        st.subheader("File Structure")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            directory_path = st.text_input("Directory Path", ".", key="structure_dir_path")
        
        with col2:
            depth = st.number_input("Depth", min_value=1, max_value=10, value=3)
        
        if st.button("Export File Structure"):
            response = client.export_file_structure(session_id, directory_path, depth)
            display_response(response)
            
            # If successful, show a nice tree structure
            if response["status_code"] == 200 and "structure" in response["data"]:
                structure = response["data"]["structure"]
                if structure:
                    try:
                        # Parse the structure JSON if it's a string
                        if isinstance(structure, str):
                            structure_data = json.loads(structure)
                        else:
                            structure_data = structure
                        
                        st.subheader(f"File Structure for {directory_path}")
                        st.json(structure_data)
                    except:
                        st.error("Failed to parse structure data")
    
    # Tab 4: Batch File Creation
    with project_tabs[3]:
        st.subheader("Batch File Creation")
        
        # Dynamic file entries
        if 'batch_files' not in st.session_state:
            st.session_state.batch_files = [{"path": "", "content": ""}]
        
        # Show existing entries
        for i, file_entry in enumerate(st.session_state.batch_files):
            with st.expander(f"File #{i+1}", expanded=i==0):
                file_path = st.text_input("File Path", file_entry["path"], key=f"batch_file_path_{i}")
                file_content = st.text_area("File Content", file_entry["content"], key=f"batch_file_content_{i}", height=150)
                
                # Update the session state
                st.session_state.batch_files[i]["path"] = file_path
                st.session_state.batch_files[i]["content"] = file_content
                
                # Remove button for entries beyond the first one
                if i > 0 and st.button("Remove", key=f"remove_file_{i}"):
                    st.session_state.batch_files.pop(i)
                    st.rerun()  # Updated from experimental_rerun
        
        # Add new file button
        if st.button("Add Another File"):
            st.session_state.batch_files.append({"path": "", "content": ""})
            st.rerun()  # Updated from experimental_rerun
        
        # Create files button
        if st.button("Create All Files"):
            # Build files dictionary
            files_dict = {}
            for file_entry in st.session_state.batch_files:
                if file_entry["path"] and file_entry["content"]:
                    files_dict[file_entry["path"]] = file_entry["content"]
            
            if files_dict:
                response = client.batch_create_files(session_id, files_dict)
                display_response(response)
            else:
                st.error("Please add at least one file with path and content")

def format_size(size_bytes):
    """Format size in bytes to a human-readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

import streamlit as st
from api_client import FileAPIClient, display_response

def render(api_url: str, session_id: str):
    """Render diff and patch testing UI"""
    st.header("Diff & Patch Operations")
    
    client = FileAPIClient(api_url)
    
    if not session_id:
        st.warning("Please create or select a session from the Sessions tab first")
        return
    
    # Create tabs for diff and patch operations
    diff_tabs = st.tabs(["Generate Diff", "Apply Patch"])
    
    # Tab 1: Generate Diff
    with diff_tabs[0]:
        st.subheader("Generate Diff")
        
        diff_method = st.radio("Diff Method", ["From Files", "From Content"])
        
        if diff_method == "From Files":
            col1, col2 = st.columns(2)
            
            with col1:
                original_path = st.text_input("Original File Path", key="diff_original_path")
            
            with col2:
                modified_path = st.text_input("Modified File Path", key="diff_modified_path")
            
            if st.button("Generate Diff from Files"):
                if original_path and modified_path:
                    response = client.generate_diff(session_id, original_path=original_path, modified_path=modified_path)
                    display_response(response)
                    
                    # Store patches in session state for easy reuse
                    if response["status_code"] == 200 and "patches" in response["data"]:
                        st.session_state.last_patches = response["data"]["patches"]
                        st.success("Patches stored for reuse in Apply Patch tab")
                else:
                    st.error("Please enter both original and modified file paths")
        
        else:  # From Content
            original_content = st.text_area("Original Content", "", height=200)
            modified_content = st.text_area("Modified Content", "", height=200)
            
            if st.button("Generate Diff from Content"):
                if original_content and modified_content:
                    response = client.generate_diff(session_id, 
                                                  original_content=original_content, 
                                                  modified_content=modified_content)
                    display_response(response)
                    
                    # Store patches in session state for easy reuse
                    if response["status_code"] == 200 and "patches" in response["data"]:
                        st.session_state.last_patches = response["data"]["patches"]
                        st.success("Patches stored for reuse in Apply Patch tab")
                else:
                    st.error("Please enter both original and modified content")
    
    # Tab 2: Apply Patch
    with diff_tabs[1]:
        st.subheader("Apply Patch")
        
        # Initialize last_patches in session state if it doesn't exist
        if 'last_patches' not in st.session_state:
            st.session_state.last_patches = ""
        
        patch_method = st.radio("Patch Method", ["To File", "To Content"])
        
        patches = st.text_area("Patches", st.session_state.last_patches, height=200)
        
        if patch_method == "To File":
            file_path = st.text_input("File Path to Patch", key="patch_file_path")
            original_content = st.text_area("Original Content (before patching)", "", height=200)
            
            if st.button("Apply Patch to File"):
                if file_path and patches and original_content:
                    response = client.apply_patch(session_id, file_path, original_content, patches)
                    display_response(response)
                else:
                    st.error("Please enter file path, original content, and patches")
        
        else:  # To Content
            original_content = st.text_area("Original Content to Patch", "", height=200)
            
            if st.button("Apply Patch to Content"):
                if patches and original_content:
                    response = client.apply_patch(session_id, "", original_content, patches)
                    display_response(response)
                    
                    # If successful, display the patched content
                    if response["status_code"] == 200 and "result" in response["data"]:
                        patched_content = response["data"]["result"]
                        st.subheader("Patched Content Result")
                        st.text_area("Patched Content", patched_content, height=200)
                else:
                    st.error("Please enter both original content and patches")

import requests
import json
import streamlit as st
from typing import Dict, List, Any, Optional, Union

class FileAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict:
        """Makes a request to the API and returns the JSON response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.lower() == "get":
                response = requests.get(url, params=params)
            elif method.lower() == "post":
                response = requests.post(url, json=data, params=params)
            elif method.lower() == "put":
                response = requests.put(url, json=data)
            elif method.lower() == "delete":
                response = requests.delete(url)
            else:
                return {"error": "Invalid HTTP method"}
            
            # Try to parse JSON response
            try:
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {}
                }
            except json.JSONDecodeError:
                return {
                    "status_code": response.status_code,
                    "data": {"text": response.text}
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 500,
                "data": {"error": f"Request failed: {str(e)}"}
            }
    
    # Session API endpoints
    def create_session(self) -> Dict:
        """Create a new session"""
        return self._make_request("post", "/sessions")
    
    def get_session(self, session_id: str) -> Dict:
        """Get session details"""
        return self._make_request("get", f"/sessions/{session_id}")
    
    def list_sessions(self) -> Dict:
        """List all sessions"""
        return self._make_request("get", "/sessions")
    
    def delete_session(self, session_id: str) -> Dict:
        """Delete a session"""
        return self._make_request("delete", f"/sessions/{session_id}")
    
    def set_working_directory(self, session_id: str, directory: str) -> Dict:
        """Set the working directory for a session"""
        return self._make_request("put", f"/sessions/{session_id}/cwd", 
                                {"workingDirectory": directory})
    
    # File API endpoints
    def list_files(self, session_id: str, directory: str = ".") -> Dict:
        """List files in a directory"""
        return self._make_request("get", f"/sessions/{session_id}/files", 
                                 params={"path": directory})
    
    def list_files_with_metadata(self, session_id: str, directory: str = ".") -> Dict:
        """List files with metadata in a directory"""
        return self._make_request("get", f"/sessions/{session_id}/files-metadata", 
                                 params={"path": directory})
    
    def get_file(self, session_id: str, file_path: str) -> Dict:
        """Get file content"""
        return self._make_request("get", f"/sessions/{session_id}/files/{file_path}")
    
    def create_file(self, session_id: str, file_path: str, content: str) -> Dict:
        """Create a new file"""
        return self._make_request("post", f"/sessions/{session_id}/files/{file_path}", 
                                {"content": content})
    
    def update_file(self, session_id: str, file_path: str, content: str) -> Dict:
        """Update file content"""
        return self._make_request("put", f"/sessions/{session_id}/files/{file_path}", 
                               {"content": content})
    
    def delete_file(self, session_id: str, file_path: str) -> Dict:
        """Delete a file"""
        return self._make_request("delete", f"/sessions/{session_id}/files/{file_path}")
    
    def search_files(self, session_id: str, pattern: str, directory: str = ".", recursive: bool = False) -> Dict:
        """Search for content in files"""
        return self._make_request("post", f"/sessions/{session_id}/search", 
                                {"pattern": pattern, "path": directory, "recursive": recursive})
    
    # Directory API endpoints
    def list_directories(self, session_id: str, directory: str = ".") -> Dict:
        """List directories"""
        return self._make_request("get", f"/sessions/{session_id}/directories", 
                                 params={"path": directory})
    
    def get_directory_tree(self, session_id: str, directory: str = ".", depth: int = 2) -> Dict:
        """Get directory tree structure"""
        return self._make_request("get", f"/sessions/{session_id}/directory-tree", 
                                 params={"path": directory, "depth": depth})
    
    def create_directory(self, session_id: str, directory_path: str) -> Dict:
        """Create a directory"""
        return self._make_request("post", f"/sessions/{session_id}/directories/{directory_path}")
    
    def delete_directory(self, session_id: str, directory_path: str) -> Dict:
        """Delete a directory"""
        return self._make_request("delete", f"/sessions/{session_id}/directories/{directory_path}")
    
    def get_directory_size(self, session_id: str, directory_path: str) -> Dict:
        """Get directory size"""
        return self._make_request("get", f"/sessions/{session_id}/directory-size/{directory_path}")
    
    # Diff & Patch API endpoints
    def generate_diff(self, session_id: str, original_path: str = "", modified_path: str = "", 
                     original_content: str = "", modified_content: str = "") -> Dict:
        """Generate diff between two files or contents"""
        data = {
            "originalPath": original_path,
            "modifiedPath": modified_path
        }
        if original_content:
            data["original"] = original_content
        if modified_content:
            data["modified"] = modified_content
            
        return self._make_request("post", f"/sessions/{session_id}/diff", data)
    
    def apply_patch(self, session_id: str, file_path: str, original: str, patches: str) -> Dict:
        """Apply patch to content or file"""
        return self._make_request("post", f"/sessions/{session_id}/patch", 
                                {"filePath": file_path, "original": original, "patches": patches})
    
    # Project API endpoints
    def get_project_summary(self, session_id: str) -> Dict:
        """Get project summary"""
        return self._make_request("get", f"/sessions/{session_id}/project")
    
    def extract_code_context(self, session_id: str, max_files: int = 10) -> Dict:
        """Extract code context for LLMs"""
        return self._make_request("get", f"/sessions/{session_id}/project/context", 
                                 params={"maxFiles": max_files})
    
    def export_file_structure(self, session_id: str, directory: str = ".", depth: int = 3) -> Dict:
        """Export file structure as JSON"""
        return self._make_request("get", f"/sessions/{session_id}/project/structure", 
                                 params={"path": directory, "depth": depth})
    
    def batch_create_files(self, session_id: str, files: Dict[str, str]) -> Dict:
        """Create multiple files at once"""
        return self._make_request("post", f"/sessions/{session_id}/project/batch-create", 
                                {"files": files})
    
    # Batch operations
    def batch_read_files(self, session_id: str, file_paths: List[str]) -> Dict:
        """Read multiple files at once"""
        return self._make_request("post", f"/sessions/{session_id}/batch-read", 
                                {"files": file_paths})

def display_response(response: Dict, use_expander: bool = True) -> None:
    """Utility function to display API responses in Streamlit"""
    if response["status_code"] >= 200 and response["status_code"] < 300:
        st.success(f"Status Code: {response['status_code']}")
    else:
        st.error(f"Status Code: {response['status_code']}")
    
    if use_expander:
        with st.expander("Response Details", expanded=True):
            st.json(response["data"])
    else:
        st.subheader("Response Details")
        st.json(response["data"])

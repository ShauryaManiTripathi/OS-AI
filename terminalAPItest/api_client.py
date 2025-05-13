import requests
import json
import streamlit as st
from typing import Dict, List, Any, Optional, Union

class TerminalAPIClient:
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
        """Create a new terminal session"""
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
    
    # Command API endpoints
    def execute_command(self, session_id: str, command: str, timeout: int = 0,
                       environment: Optional[Dict[str, str]] = None) -> Dict:
        """Execute a command and get output"""
        data = {
            "command": command,
            "timeout": timeout
        }
        if environment:
            data["environment"] = environment
        return self._make_request("post", f"/sessions/{session_id}/commands", data)
    
    def execute_batch_commands(self, session_id: str, commands: List[str], 
                              continue_on_error: bool = False, 
                              timeout: int = 0,
                              environment: Optional[Dict[str, str]] = None) -> Dict:
        """Execute multiple commands in sequence"""
        data = {
            "commands": commands,
            "continueOnError": continue_on_error,
            "timeout": timeout
        }
        if environment:
            data["environment"] = environment
        return self._make_request("post", f"/sessions/{session_id}/commands/batch", data)
    
    # Process API endpoints
    def start_process(self, session_id: str, command: str, timeout: int = 0,
                     environment: Optional[Dict[str, str]] = None) -> Dict:
        """Start a new long-running process"""
        data = {
            "command": command,
            "timeout": timeout
        }
        if environment:
            data["environment"] = environment
        return self._make_request("post", f"/sessions/{session_id}/processes", data)
    
    def list_processes(self, session_id: str) -> Dict:
        """List all running processes"""
        return self._make_request("get", f"/sessions/{session_id}/processes")
    
    def get_process(self, session_id: str, process_id: str) -> Dict:
        """Get details of a specific process"""
        return self._make_request("get", f"/sessions/{session_id}/processes/{process_id}")
    
    def get_process_output(self, session_id: str, process_id: str) -> Dict:
        """Get process output (stdout/stderr)"""
        return self._make_request("get", f"/sessions/{session_id}/processes/{process_id}/output")
    
    def send_process_input(self, session_id: str, process_id: str, input_text: str) -> Dict:
        """Send input to a running process"""
        return self._make_request("post", f"/sessions/{session_id}/processes/{process_id}/input", 
                               {"input": input_text})
    
    def signal_process(self, session_id: str, process_id: str, signal: str) -> Dict:
        """Send a signal to a process (SIGTERM, SIGKILL, etc.)"""
        return self._make_request("post", f"/sessions/{session_id}/processes/{process_id}/signal", 
                               {"signal": signal})
    
    # Environment API endpoints
    def get_env_vars(self, session_id: str) -> Dict:
        """Get all environment variables"""
        return self._make_request("get", f"/sessions/{session_id}/env")
    
    def set_env_var(self, session_id: str, key: str, value: str) -> Dict:
        """Set a specific environment variable"""
        return self._make_request("put", f"/sessions/{session_id}/env/{key}", 
                               {"value": value})
    
    def set_batch_env_vars(self, session_id: str, variables: Dict[str, str]) -> Dict:
        """Set multiple environment variables"""
        return self._make_request("put", f"/sessions/{session_id}/env", 
                               {"variables": variables})
    
    def unset_env_var(self, session_id: str, key: str) -> Dict:
        """Unset an environment variable"""
        return self._make_request("delete", f"/sessions/{session_id}/env/{key}")
    
    # History API endpoints
    def get_history(self, session_id: str, limit: int = 0) -> Dict:
        """Get command history"""
        params = {}
        if limit > 0:
            params["limit"] = limit
        return self._make_request("get", f"/sessions/{session_id}/history", params=params)
    
    def search_history(self, session_id: str, query: str) -> Dict:
        """Search command history"""
        return self._make_request("get", f"/sessions/{session_id}/history/search", 
                                params={"query": query})
    
    def clear_history(self, session_id: str) -> Dict:
        """Clear command history"""
        return self._make_request("delete", f"/sessions/{session_id}/history")
    
    # System API endpoints
    def get_system_info(self) -> Dict:
        """Get system information"""
        return self._make_request("get", "/system/info")
    
    def get_available_shells(self) -> Dict:
        """Get available shells"""
        return self._make_request("get", "/system/shells")

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

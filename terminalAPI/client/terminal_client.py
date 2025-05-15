import os
import json
import time
import requests
import atexit
from typing import Dict, List, Union, Optional, Any, Tuple

class TerminalAPIClient:
    """
    Comprehensive client for interacting with the terminalAPI server.
    
    This client automatically handles session creation and management,
    and provides methods for all API endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:8081", working_dir: str = None):
        """
        Initialize the Terminal API client.
        
        Args:
            base_url: The base URL of the terminalAPI server
            working_dir: The working directory to use. If None, uses the current directory.
        """
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.working_dir = working_dir or os.getcwd()
        
        # Create a session and set working directory
        self._create_session()
        self._set_working_directory()
        
        # Register cleanup function to be called on exit
        atexit.register(self.cleanup)
    
    def _create_session(self) -> None:
        """Create a new session on the server."""
        response = requests.post(f"{self.base_url}/sessions")
        if response.status_code != 201:
            raise Exception(f"Failed to create session: {response.text}")
        
        data = response.json()
        self.session_id = data["id"]
        print(f"Created session with ID: {self.session_id}")
    
    def _set_working_directory(self) -> None:
        """Set the working directory for the current session."""
        if not self.session_id:
            raise Exception("No active session")
        
        payload = {"workingDirectory": self.working_dir}
        response = requests.put(
            f"{self.base_url}/sessions/{self.session_id}/cwd", 
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to set working directory: {response.text}")
        
        print(f"Working directory set to: {self.working_dir}")
    
    def cleanup(self) -> None:
        """Delete the session when the client is destroyed."""
        if self.session_id:
            try:
                requests.delete(f"{self.base_url}/sessions/{self.session_id}")
                print(f"Cleaned up session: {self.session_id}")
                self.session_id = None
            except Exception as e:
                print(f"Error cleaning up session: {str(e)}")
    
    def _check_session(self) -> None:
        """Verify that a session exists."""
        if not self.session_id:
            raise Exception("No active session")
    
    # Session Management Methods
    
    def get_session_info(self) -> Dict:
        """Get information about the current session."""
        self._check_session()
        
        response = requests.get(f"{self.base_url}/sessions/{self.session_id}")
        if response.status_code != 200:
            raise Exception(f"Failed to get session info: {response.text}")
        
        return response.json()
    
    def list_sessions(self) -> List[Dict]:
        """List all active sessions on the server."""
        response = requests.get(f"{self.base_url}/sessions")
        if response.status_code != 200:
            raise Exception(f"Failed to list sessions: {response.text}")
        
        return response.json()["sessions"]
    
    def change_working_directory(self, new_dir: str) -> Dict:
        """
        Change the working directory for the current session.
        
        Args:
            new_dir: The new working directory path
        
        Returns:
            Updated session information
        """
        self._check_session()
        
        # Update the working directory
        self.working_dir = os.path.abspath(new_dir)
        
        payload = {"workingDirectory": self.working_dir}
        response = requests.put(
            f"{self.base_url}/sessions/{self.session_id}/cwd", 
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to change working directory: {response.text}")
        
        return response.json()
    
    # Command Execution Methods
    
    def execute_command(self, command: str, timeout: int = 0, environment: Dict[str, str] = None) -> Dict:
        """
        Execute a command in the current session.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds (0 = no timeout)
            environment: Additional environment variables for the command
        
        Returns:
            Command execution results
        """
        self._check_session()
        
        payload = {
            "command": command,
            "timeout": timeout,
            "environment": environment or {}
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/commands",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to execute command: {response.text}")
        
        return response.json()
    
    def execute_batch_commands(self, commands: List[str], continue_on_error: bool = False, 
                              timeout: int = 0, environment: Dict[str, str] = None) -> Dict:
        """
        Execute multiple commands in sequence.
        
        Args:
            commands: List of commands to execute
            continue_on_error: Whether to continue execution if a command fails
            timeout: Timeout in seconds per command (0 = no timeout)
            environment: Additional environment variables for all commands
        
        Returns:
            Results for each command
        """
        self._check_session()
        
        payload = {
            "commands": commands,
            "continueOnError": continue_on_error,
            "timeout": timeout,
            "environment": environment or {}
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/commands/batch",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to execute batch commands: {response.text}")
        
        return response.json()
    
    # Process Management Methods
    
    def start_process(self, command: str, timeout: int = 0, environment: Dict[str, str] = None) -> Dict:
        """
        Start a long-running process.
        
        Args:
            command: The command to run
            timeout: Timeout in seconds (0 = no timeout)
            environment: Additional environment variables for the process
        
        Returns:
            Process information
        """
        self._check_session()
        
        payload = {
            "command": command,
            "timeout": timeout,
            "environment": environment or {}
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/processes",
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to start process: {response.text}")
        
        return response.json()
    
    def list_processes(self) -> Dict:
        """
        List all running processes for the current session.
        
        Returns:
            Dictionary of processes
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/processes"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to list processes: {response.text}")
        
        return response.json().get("processes", {})
    
    def get_process(self, process_id: str) -> Dict:
        """
        Get information about a specific process.
        
        Args:
            process_id: ID of the process to get
        
        Returns:
            Process information
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/processes/{process_id}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get process: {response.text}")
        
        return response.json()
    
    def get_process_output(self, process_id: str) -> Dict:
        """
        Get the stdout and stderr of a process.
        
        Args:
            process_id: ID of the process
        
        Returns:
            Process output with stdout and stderr
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/processes/{process_id}/output"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get process output: {response.text}")
        
        return response.json()
    
    def send_input_to_process(self, process_id: str, input_text: str) -> Dict:
        """
        Send input to a running process.
        
        Args:
            process_id: ID of the process
            input_text: Text to send to the process stdin
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"input": input_text}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/processes/{process_id}/input",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send input to process: {response.text}")
        
        return response.json()
    
    def send_signal_to_process(self, process_id: str, signal: str) -> Dict:
        """
        Send a signal to a running process.
        
        Args:
            process_id: ID of the process
            signal: Signal to send (SIGTERM, SIGKILL, SIGINT, SIGHUP)
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"signal": signal}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/processes/{process_id}/signal",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send signal to process: {response.text}")
        
        return response.json()
    
    # Environment Variable Methods
    
    def get_env_vars(self) -> Dict[str, str]:
        """
        Get all environment variables for the current session.
        
        Returns:
            Dictionary of environment variables
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/env"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get environment variables: {response.text}")
        
        return response.json()
    
    def set_env_var(self, key: str, value: str) -> Dict:
        """
        Set an environment variable.
        
        Args:
            key: Environment variable name
            value: Environment variable value
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"value": value}
        response = requests.put(
            f"{self.base_url}/sessions/{self.session_id}/env/{key}",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to set environment variable: {response.text}")
        
        return response.json()
    
    def set_batch_env_vars(self, env_vars: Dict[str, str]) -> Dict:
        """
        Set multiple environment variables at once.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"variables": env_vars}
        response = requests.put(
            f"{self.base_url}/sessions/{self.session_id}/env",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to set environment variables: {response.text}")
        
        return response.json()
    
    def unset_env_var(self, key: str) -> Dict:
        """
        Unset (delete) an environment variable.
        
        Args:
            key: Name of the environment variable to unset
        
        Returns:
            Response message
        """
        self._check_session()
        
        response = requests.delete(
            f"{self.base_url}/sessions/{self.session_id}/env/{key}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to unset environment variable: {response.text}")
        
        return response.json()
    
    # Command History Methods
    
    def get_command_history(self, limit: int = 0) -> Dict:
        """
        Get command history for the current session.
        
        Args:
            limit: Maximum number of history entries to return (0 = all)
        
        Returns:
            Command history
        """
        self._check_session()
        
        params = {}
        if limit > 0:
            params["limit"] = limit
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/history",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get command history: {response.text}")
        
        return response.json()
    
    def search_command_history(self, query: str) -> Dict:
        """
        Search command history for the current session.
        
        Args:
            query: Search query
        
        Returns:
            Matching history entries
        """
        self._check_session()
        
        params = {"query": query}
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/history/search",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to search command history: {response.text}")
        
        return response.json()
    
    def clear_command_history(self) -> Dict:
        """
        Clear command history for the current session.
        
        Returns:
            Response message
        """
        self._check_session()
        
        response = requests.delete(
            f"{self.base_url}/sessions/{self.session_id}/history"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to clear command history: {response.text}")
        
        return response.json()
    
    # System Information Methods
    
    def get_system_info(self) -> Dict:
        """
        Get information about the server system.
        
        Returns:
            System information
        """
        response = requests.get(f"{self.base_url}/system/info")
        if response.status_code != 200:
            raise Exception(f"Failed to get system info: {response.text}")
        
        return response.json()
    
    def get_available_shells(self) -> Dict:
        """
        Get available shell programs on the server.
        
        Returns:
            Available shells
        """
        if self.session_id:
            # Try session-specific first
            response = requests.get(f"{self.base_url}/sessions/{self.session_id}/system/shells")
        else:
            # Fall back to general endpoint
            response = requests.get(f"{self.base_url}/system/shells")
            
        if response.status_code != 200:
            raise Exception(f"Failed to get available shells: {response.text}")
        
        return response.json()
    
    # Helper Methods
    
    def run_and_capture(self, command: str) -> Tuple[int, str, str]:
        """
        Run a command and return its exit code, stdout, and stderr.
        
        Args:
            command: Command to run
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        result = self.execute_command(command)
        return (
            result.get("exitCode", -1),
            result.get("stdout", ""),
            result.get("stderr", "")
        )
    
    def run_interactive_command(self, command: str) -> str:
        """
        Start an interactive process and return its ID.
        
        Args:
            command: Command to run interactively
        
        Returns:
            Process ID
        """
        result = self.start_process(command)
        return result.get("id")
    
    def get_environment_value(self, key: str) -> Optional[str]:
        """
        Get a specific environment variable value.
        
        Args:
            key: Environment variable name
        
        Returns:
            Environment variable value or None if not set
        """
        env_vars = self.get_env_vars()
        return env_vars.get(key)
    
    def set_working_environment(self, env_vars: Dict[str, str]) -> Dict:
        """
        Set up a working environment with multiple variables.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Response message
        """
        return self.set_batch_env_vars(env_vars)
    
    def execute_commands_in_shell(self, commands: List[str], shell: str = None) -> List[Dict]:
        """
        Execute multiple commands in a specific shell.
        
        Args:
            commands: List of commands to execute
            shell: Shell to use (if None, uses session default)
        
        Returns:
            List of command results
        """
        env = {}
        if shell:
            env = {"SHELL": shell}
        
        results = []
        for cmd in commands:
            result = self.execute_command(cmd, environment=env)
            results.append(result)
        
        return results


# Example usage:
if __name__ == "__main__":
    # Create client
    client = TerminalAPIClient()
    
    # Get session info
    session_info = client.get_session_info()
    print(f"Session info: {session_info}")
    
    # Execute a simple command
    result = client.execute_command("ls -la")
    print(f"Command output: {result['stdout']}")
    
    # Set an environment variable
    client.set_env_var("TEST_VAR", "test_value")
    
    # Verify the environment variable
    env_vars = client.get_env_vars()
    print(f"Environment variables: {env_vars}")
    
    # Get system info
    system_info = client.get_system_info()
    print(f"System info: {system_info}")
    
    # The client will automatically clean up the session when it exits

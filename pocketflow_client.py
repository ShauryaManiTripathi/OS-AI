import os
import json
import time
import requests
import atexit
from typing import Dict, List, Union, Optional, Any, Tuple, BinaryIO

# Import both clients
from fileAPI.client.fileapi_client import FileAPIClient
from terminalAPI.client.terminal_client import TerminalAPIClient

class PocketFlowClient:
    """
    Comprehensive unified client for interacting with both fileAPI and terminalAPI servers.
    
    This client provides access to all functionality of both APIs through a single interface,
    with automatic session management and coordination between the two subsystems.
    """
    
    def __init__(self, 
                file_api_url: str = "http://localhost:8080", 
                terminal_api_url: str = "http://localhost:8081",
                working_dir: str = None):
        """
        Initialize the PocketFlow client with both APIs.
        
        Args:
            file_api_url: The base URL of the fileAPI server (default: http://localhost:8080)
            terminal_api_url: The base URL of the terminalAPI server (default: http://localhost:8081)
            working_dir: The working directory to use. If None, uses the current directory.
        """
        self.working_dir = working_dir or os.getcwd()
        
        # Initialize both clients with the same working directory
        self.file_client = FileAPIClient(base_url=file_api_url, working_dir=self.working_dir)
        self.terminal_client = TerminalAPIClient(base_url=terminal_api_url, working_dir=self.working_dir)
        
        print(f"PocketFlow client initialized with working directory: {self.working_dir}")
        print(f"FileAPI session: {self.file_client.session_id}")
        print(f"TerminalAPI session: {self.terminal_client.session_id}")

    #========================================
    # FILE OPERATIONS
    #========================================
    
    def list_files(self, path: str = ".") -> List[str]:
        """
        List files in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            List of filenames
        """
        return self.file_client.list_files(path)
    
    def list_files_with_metadata(self, path: str = ".") -> List[Dict]:
        """
        List files with detailed metadata in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            List of file metadata objects
        """
        return self.file_client.list_files_with_metadata(path)
    
    def get_file(self, file_path: str) -> str:
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            File content as a string
        """
        return self.file_client.get_file(file_path)
    
    def create_file(self, file_path: str, content: str) -> Dict:
        """
        Create a new file with the specified content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: Content to write to the file
        
        Returns:
            Response message
        """
        return self.file_client.create_file(file_path, content)
    
    def update_file(self, file_path: str, content: str) -> Dict:
        """
        Update an existing file with new content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: New content for the file
        
        Returns:
            Response message
        """
        return self.file_client.update_file(file_path, content)
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file relative to working directory
        """
        self.file_client.delete_file(file_path)
    
    def get_file_metadata(self, file_path: str) -> Dict:
        """
        Get metadata for a specific file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            File metadata
        """
        return self.file_client.get_file_metadata(file_path)
    
    def batch_read_files(self, file_paths: List[str]) -> List[Dict]:
        """
        Read multiple files in one request.
        
        Args:
            file_paths: List of file paths to read
        
        Returns:
            List of results with file content
        """
        return self.file_client.batch_read_files(file_paths)
    
    def search_files(self, pattern: str, path: str = ".", recursive: bool = True) -> Dict:
        """
        Search for a pattern in files.
        
        Args:
            pattern: Pattern to search for
            path: Directory to search in (default: current directory)
            recursive: Whether to search recursively (default: True)
        
        Returns:
            Search results
        """
        return self.file_client.search_files(pattern, path, recursive)
    
    def extract_content(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Extract content from multiple files, with error handling.
        
        Args:
            file_paths: List of file paths to extract content from
        
        Returns:
            Dictionary mapping file paths to their content
        """
        return self.file_client.extract_content(file_paths)
    
    #========================================
    # DIRECTORY OPERATIONS
    #========================================
    
    def list_directories(self, path: str = ".") -> List[str]:
        """
        List directories in a path.
        
        Args:
            path: Relative path to list directories from (default: current directory)
        
        Returns:
            List of directory names
        """
        return self.file_client.list_directories(path)
    
    def create_directory(self, dir_path: str) -> Dict:
        """
        Create a new directory.
        
        Args:
            dir_path: Path to the directory to create
        
        Returns:
            Response message
        """
        return self.file_client.create_directory(dir_path)
    
    def delete_directory(self, dir_path: str) -> None:
        """
        Delete a directory and all its contents.
        
        Args:
            dir_path: Path to the directory to delete
        """
        self.file_client.delete_directory(dir_path)
    
    def get_directory_tree(self, path: str = ".", depth: int = 2) -> Dict:
        """
        Get a tree representation of a directory structure.
        
        Args:
            path: Path to get tree for (default: current directory)
            depth: Maximum depth of the tree (default: 2)
        
        Returns:
            Directory tree
        """
        return self.file_client.get_directory_tree(path, depth)
    
    def get_directory_size(self, dir_path: str) -> Dict:
        """
        Calculate the size of a directory.
        
        Args:
            dir_path: Path to the directory
        
        Returns:
            Directory size information
        """
        return self.file_client.get_directory_size(dir_path)
    
    #========================================
    # PROJECT OPERATIONS
    #========================================
    
    def get_project_summary(self) -> Dict:
        """
        Get a summary of the project in the working directory.
        
        Returns:
            Project summary information
        """
        return self.file_client.get_project_summary()
    
    def extract_code_context(self, max_files: int = 10) -> Dict:
        """
        Extract code context for LLM understanding.
        
        Args:
            max_files: Maximum number of files to include (default: 10)
        
        Returns:
            Code context information
        """
        return self.file_client.extract_code_context(max_files)
    
    def export_file_structure(self, path: str = ".", depth: int = 3) -> Dict:
        """
        Export the file structure as a nested JSON object.
        
        Args:
            path: Path to export structure for (default: current directory)
            depth: Maximum depth of the structure (default: 3)
        
        Returns:
            File structure information
        """
        return self.file_client.export_file_structure(path, depth)
    
    def batch_create_files(self, files: Dict[str, str]) -> Dict:
        """
        Create multiple files at once.
        
        Args:
            files: Dictionary mapping file paths to their content
        
        Returns:
            Results for each file creation
        """
        return self.file_client.batch_create_files(files)
    
    #========================================
    # COMMAND EXECUTION
    #========================================
    
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
        return self.terminal_client.execute_command(command, timeout, environment)
    
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
        return self.terminal_client.execute_batch_commands(
            commands, continue_on_error, timeout, environment
        )
    
    def run_and_capture(self, command: str) -> Tuple[int, str, str]:
        """
        Run a command and return its exit code, stdout, and stderr.
        
        Args:
            command: Command to run
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        return self.terminal_client.run_and_capture(command)
    
    #========================================
    # PROCESS MANAGEMENT
    #========================================
    
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
        return self.terminal_client.start_process(command, timeout, environment)
    
    def list_processes(self) -> Dict:
        """
        List all running processes for the current session.
        
        Returns:
            Dictionary of processes
        """
        return self.terminal_client.list_processes()
    
    def get_process(self, process_id: str) -> Dict:
        """
        Get information about a specific process.
        
        Args:
            process_id: ID of the process to get
        
        Returns:
            Process information
        """
        return self.terminal_client.get_process(process_id)
    
    def get_process_output(self, process_id: str) -> Dict:
        """
        Get the stdout and stderr of a process.
        
        Args:
            process_id: ID of the process
        
        Returns:
            Process output with stdout and stderr
        """
        return self.terminal_client.get_process_output(process_id)
    
    def send_input_to_process(self, process_id: str, input_text: str) -> Dict:
        """
        Send input to a running process.
        
        Args:
            process_id: ID of the process
            input_text: Text to send to the process stdin
        
        Returns:
            Response message
        """
        return self.terminal_client.send_input_to_process(process_id, input_text)
    
    def send_signal_to_process(self, process_id: str, signal: str) -> Dict:
        """
        Send a signal to a running process.
        
        Args:
            process_id: ID of the process
            signal: Signal to send (SIGTERM, SIGKILL, SIGINT, SIGHUP)
        
        Returns:
            Response message
        """
        return self.terminal_client.send_signal_to_process(process_id, signal)
    
    def run_interactive_command(self, command: str) -> str:
        """
        Start an interactive process and return its ID.
        
        Args:
            command: Command to run interactively
        
        Returns:
            Process ID
        """
        return self.terminal_client.run_interactive_command(command)
    
    #========================================
    # ENVIRONMENT VARIABLES
    #========================================
    
    def get_env_vars(self) -> Dict[str, str]:
        """
        Get all environment variables for the current session.
        
        Returns:
            Dictionary of environment variables
        """
        return self.terminal_client.get_env_vars()
    
    def set_env_var(self, key: str, value: str) -> Dict:
        """
        Set an environment variable.
        
        Args:
            key: Environment variable name
            value: Environment variable value
        
        Returns:
            Response message
        """
        return self.terminal_client.set_env_var(key, value)
    
    def set_batch_env_vars(self, env_vars: Dict[str, str]) -> Dict:
        """
        Set multiple environment variables at once.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Response message
        """
        return self.terminal_client.set_batch_env_vars(env_vars)
    
    def unset_env_var(self, key: str) -> Dict:
        """
        Unset (delete) an environment variable.
        
        Args:
            key: Name of the environment variable to unset
        
        Returns:
            Response message
        """
        return self.terminal_client.unset_env_var(key)
    
    def get_environment_value(self, key: str) -> Optional[str]:
        """
        Get a specific environment variable value.
        
        Args:
            key: Environment variable name
        
        Returns:
            Environment variable value or None if not set
        """
        return self.terminal_client.get_environment_value(key)
    
    def set_working_environment(self, env_vars: Dict[str, str]) -> Dict:
        """
        Set up a working environment with multiple variables.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Response message
        """
        return self.terminal_client.set_working_environment(env_vars)
    
    #========================================
    # COMMAND HISTORY
    #========================================
    
    def get_command_history(self, limit: int = 0) -> Dict:
        """
        Get command history for the current session.
        
        Args:
            limit: Maximum number of history entries to return (0 = all)
        
        Returns:
            Command history
        """
        return self.terminal_client.get_command_history(limit)
    
    def search_command_history(self, query: str) -> Dict:
        """
        Search command history for the current session.
        
        Args:
            query: Search query
        
        Returns:
            Matching history entries
        """
        return self.terminal_client.search_command_history(query)
    
    def clear_command_history(self) -> Dict:
        """
        Clear command history for the current session.
        
        Returns:
            Response message
        """
        return self.terminal_client.clear_command_history()
    
    #========================================
    # SYSTEM INFORMATION
    #========================================
    
    def get_system_info(self) -> Dict:
        """
        Get information about the server system.
        
        Returns:
            System information
        """
        return self.terminal_client.get_system_info()
    
    def get_available_shells(self) -> Dict:
        """
        Get available shell programs on the server.
        
        Returns:
            Available shells
        """
        return self.terminal_client.get_available_shells()
    
    #========================================
    # SESSION MANAGEMENT
    #========================================
    
    def get_file_session_info(self) -> Dict:
        """
        Get information about the current file API session.
        
        Returns:
            File session information
        """
        return self.file_client.get_session_info()
    
    def get_terminal_session_info(self) -> Dict:
        """
        Get information about the current terminal API session.
        
        Returns:
            Terminal session information
        """
        return self.terminal_client.get_session_info()
    
    def change_working_directory(self, new_dir: str) -> Dict:
        """
        Change the working directory for both sessions.
        
        Args:
            new_dir: The new working directory path
        
        Returns:
            Updated terminal session information
        """
        # Update internal working directory
        self.working_dir = os.path.abspath(new_dir)
        
        # Change directory for both APIs
        self.file_client.change_working_directory(new_dir)
        return self.terminal_client.change_working_directory(new_dir)
    
    #========================================
    # DIFF AND PATCH OPERATIONS
    #========================================
    
    def generate_diff(self, 
                    original_path: str = None, 
                    modified_path: str = None,
                    original_content: str = None,
                    modified_content: str = None) -> Dict:
        """
        Generate a diff between two files or content.
        
        You must provide either paths or content, but not both.
        
        Args:
            original_path: Path to the original file
            modified_path: Path to the modified file
            original_content: Original content string
            modified_content: Modified content string
        
        Returns:
            Diff patches
        """
        return self.file_client.generate_diff(
            original_path, modified_path, original_content, modified_content
        )
    
    def apply_patch(self, file_path: str, patches: str) -> Dict:
        """
        Apply patches to a file. Automatically reads the file content and applies the patches.
        
        Args:
            file_path: Path to the file to patch
            patches: Patches to apply
        
        Returns:
            Dictionary with the patched content
        """
        return self.file_client.apply_patch(file_path, patches)
    
    #========================================
    # HELPER METHODS
    #========================================
    
    def read_and_update_file(self, file_path: str, update_func) -> Dict:
        """
        Read a file, apply a function to its content, and update the file.
        
        Args:
            file_path: Path to the file
            update_func: Function that takes the file content and returns updated content
        
        Returns:
            Update response
        """
        return self.file_client.read_and_update_file(file_path, update_func)
    
    def find_files_by_extension(self, extension: str, path: str = ".", recursive: bool = True) -> List[str]:
        """
        Find all files with a specific extension.
        
        Args:
            extension: File extension to search for (e.g., ".py")
            path: Directory to search in (default: current directory)
            recursive: Whether to search recursively (default: True)
        
        Returns:
            List of file paths
        """
        return self.file_client.find_files_by_extension(extension, path, recursive)
    
    def get_project_files_by_type(self, file_types: List[str], max_per_type: int = 5) -> Dict[str, List[str]]:
        """
        Get a dictionary of project files organized by file type.
        
        Args:
            file_types: List of file extensions to fetch (e.g., ["py", "js", "go"])
            max_per_type: Maximum number of files to fetch per type
            
        Returns:
            Dictionary mapping file types to lists of files
        """
        return self.file_client.get_project_files_by_type(file_types, max_per_type)
    
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        return self.file_client.backup_file(file_path)
    
    def read_file_safely(self, file_path: str) -> Tuple[bool, str]:
        """
        Read a file with error handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Tuple of (success, content)
        """
        return self.file_client.read_file_safely(file_path)
    
    def save_file_safely(self, file_path: str, content: str) -> Tuple[bool, str]:
        """
        Save a file with error handling.
        
        Args:
            file_path: Path to the file to save
            content: Content to write to the file
            
        Returns:
            Tuple of (success, message)
        """
        return self.file_client.save_file_safely(file_path, content)
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return self.file_client.file_exists(file_path)
    
    def directory_exists(self, dir_path: str) -> bool:
        """
        Check if a directory exists.
        
        Args:
            dir_path: Path to the directory to check
            
        Returns:
            True if the directory exists, False otherwise
        """
        return self.file_client.directory_exists(dir_path)
    
    def ensure_directory_exists(self, dir_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if the directory exists or was created, False otherwise
        """
        return self.file_client.ensure_directory_exists(dir_path)
    
    def execute_commands_in_shell(self, commands: List[str], shell: str = None) -> List[Dict]:
        """
        Execute multiple commands in a specific shell.
        
        Args:
            commands: List of commands to execute
            shell: Shell to use (if None, uses session default)
        
        Returns:
            List of command results
        """
        return self.terminal_client.execute_commands_in_shell(commands, shell)
    
    #========================================
    # INTEGRATED OPERATIONS
    #========================================
    
    def edit_and_run_file(self, file_path: str, content: str = None) -> Dict:
        """
        Edit a file (or create if it doesn't exist) and then run it.
        
        Args:
            file_path: Path to the file to edit and run
            content: New content for the file. If None, the file is run without modification.
        
        Returns:
            Command execution results
        """
        # Check if the file exists
        exists = self.file_exists(file_path)
        
        # If content is provided, update or create the file
        if content is not None:
            if exists:
                self.update_file(file_path, content)
            else:
                self.create_file(file_path, content)
        
        # Determine how to run the file based on its extension
        ext = os.path.splitext(file_path)[1].lower()
        cmd = None
        
        if ext == '.py':
            cmd = f"python {file_path}"
        elif ext == '.js':
            cmd = f"node {file_path}"
        elif ext == '.sh':
            cmd = f"bash {file_path}"
        elif ext == '.go':
            cmd = f"go run {file_path}"
        elif ext == '.rb':
            cmd = f"ruby {file_path}"
        elif ext == '.java':
            cmd = f"javac {file_path} && java {os.path.splitext(os.path.basename(file_path))[0]}"
        elif ext == '.cpp' or ext == '.cc':
            output_name = os.path.splitext(os.path.basename(file_path))[0]
            cmd = f"g++ {file_path} -o {output_name} && ./{output_name}"
        elif ext == '.c':
            output_name = os.path.splitext(os.path.basename(file_path))[0]
            cmd = f"gcc {file_path} -o {output_name} && ./{output_name}"
        elif ext == '.rs':
            cmd = f"rustc {file_path} && ./{os.path.splitext(os.path.basename(file_path))[0]}"
        else:
            raise ValueError(f"Don't know how to run file with extension {ext}")
        
        # Execute the command
        return self.execute_command(cmd)
    
    def find_and_replace_in_files(self, pattern: str, replacement: str, path: str = ".", 
                                file_pattern: str = None, recursive: bool = True) -> Dict:
        """
        Find a pattern in files and replace it with another string.
        
        Args:
            pattern: Pattern to search for
            replacement: Text to replace the pattern with
            path: Directory to search in (default: current directory)
            file_pattern: Optional pattern to filter files (e.g., "*.py")
            recursive: Whether to search recursively (default: True)
        
        Returns:
            Dictionary with results
        """
        # First, find files containing the pattern
        search_results = self.search_files(pattern, path, recursive)
        
        results = {
            "pattern": pattern,
            "replacement": replacement,
            "filesModified": 0,
            "occurrencesReplaced": 0,
            "modifiedFiles": {}
        }
        
        # Process each file that had matches
        for file_path, matches in search_results.get("results", {}).items():
            # Skip if file doesn't match the file pattern
            if file_pattern and not self._matches_glob_pattern(file_path, file_pattern):
                continue
                
            # Skip if the file name was what matched, not the content
            if matches == ["[Filename matches search pattern]"]:
                continue
                
            try:
                # Read the file
                content = self.get_file(file_path)
                
                # Count occurrences before replacement
                original_count = content.count(pattern)
                
                if original_count > 0:
                    # Replace occurrences
                    new_content = content.replace(pattern, replacement)
                    
                    # Update the file
                    self.update_file(file_path, new_content)
                    
                    # Track stats
                    results["filesModified"] += 1
                    results["occurrencesReplaced"] += original_count
                    results["modifiedFiles"][file_path] = original_count
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                
        return results
    
    def _matches_glob_pattern(self, filename: str, pattern: str) -> bool:
        """Check if a filename matches a glob pattern like '*.py'"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def backup_project(self, output_path: str = None) -> str:
        """
        Create a backup of the current project directory.
        
        Args:
            output_path: Path where to save the backup. If None, saves with timestamp.
            
        Returns:
            Path to the backup directory
        """
        import shutil
        import datetime
        
        # Get current timestamp for the backup name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine backup location
        if not output_path:
            project_name = os.path.basename(self.working_dir)
            output_path = f"{project_name}_backup_{timestamp}"
        
        # Create absolute path
        if not os.path.isabs(output_path):
            output_path = os.path.join(os.path.dirname(self.working_dir), output_path)
        
        # Create the backup using system commands through terminal API
        try:
            # Use tar to create a compressed backup
            cmd = f"tar -czf {output_path}.tar.gz -C {os.path.dirname(self.working_dir)} {os.path.basename(self.working_dir)}"
            result = self.execute_command(cmd)
            
            if result["exitCode"] == 0:
                return f"{output_path}.tar.gz"
            else:
                # If tar fails, try a simple directory copy
                shutil.copytree(self.working_dir, output_path)
                return output_path
        except:
            # Fallback to Python's shutil if terminal command fails
            shutil.copytree(self.working_dir, output_path)
            return output_path
    
    def script_and_execute(self, script_content: str, script_path: str = None, 
                         interpreter: str = "python") -> Dict:
        """
        Create a script file and execute it.
        
        Args:
            script_content: Content of the script to create and run
            script_path: Path where to save the script. If None, creates a temporary file.
            interpreter: Interpreter to use (python, bash, node, etc.)
            
        Returns:
            Command execution results
        """
        import tempfile
        import os
        
        if not script_path:
            # Determine file extension based on interpreter
            ext_map = {
                "python": ".py",
                "bash": ".sh",
                "sh": ".sh",
                "node": ".js",
                "ruby": ".rb",
                "perl": ".pl",
                "php": ".php",
                "go": ".go",
            }
            ext = ext_map.get(interpreter.lower(), ".txt")
            
            # Create temp file with appropriate extension
            fd, script_path = tempfile.mkstemp(suffix=ext, prefix=f"{interpreter}_script_",
                                              dir=self.working_dir)
            os.close(fd)
        
        # Create the script file
        self.create_file(os.path.basename(script_path), script_content)
        
        # Make sure the script is executable (for shell scripts)
        if interpreter.lower() in ["bash", "sh"]:
            self.execute_command(f"chmod +x {script_path}")
        
        # Execute the script using the specified interpreter
        return self.execute_command(f"{interpreter} {script_path}")
    
    #========================================
    # CLEANUP AND SESSION MANAGEMENT
    #========================================
    
    def cleanup_sessions(self) -> None:
        """
        Clean up all sessions explicitly, terminating both clients.
        """
        # Clean up terminal session
        if hasattr(self, 'terminal_client') and self.terminal_client:
            self.terminal_client.cleanup()
        
        # Clean up file session
        if hasattr(self, 'file_client') and self.file_client:
            self.file_client.cleanup()
            
        print("All sessions cleaned up")


# Example usage:
if __name__ == "__main__":
    # Create the unified client
    client = PocketFlowClient()
    
    # Get system info
    system_info = client.get_system_info()
    print(f"System info: {system_info.get('hostname', 'Unknown')}, OS: {system_info.get('os', 'Unknown')}")
    
    # Create a file
    print("Creating test file...")
    client.create_file("test_script.py", "print('Hello from PocketFlow!')")
    
    # List files
    files = client.list_files()
    print(f"Files in current directory: {files}")
    
    # Execute the script
    print("Executing script...")
    result = client.execute_command("python test_script.py")
    print(f"Script output: {result['stdout']}")
    
    # Get environment variables
    env_vars = client.get_env_vars()
    print(f"Environment variables: {list(env_vars.keys())[:5]}")
    
    # Start a background process
    print("Starting a background process...")
    process = client.start_process("sleep 5 && echo 'Background process completed'")
    print(f"Process ID: {process['id']}")
    
    # Clean up test file
    client.delete_file("test_script.py")
    
    print("Demonstration completed. Sessions will be cleaned up automatically on exit.")
    # Sessions are automatically cleaned up when the client is destroyed

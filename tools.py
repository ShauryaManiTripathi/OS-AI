import os
import json
import time
import requests
import atexit
from typing import Dict, List, Union, Optional, Any, Tuple, BinaryIO

# Import both clients
from fileAPI.client.fileapi_client import FileAPIClient
from terminalAPI.client.terminal_client import TerminalAPIClient

class Tools:
    """
    Comprehensive unified client for interacting with both fileAPI and terminalAPI servers.
    
    This client provides text-formatted output of all operations for easy consumption by LLMs.
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
    # Helper methods for text formatting
    #========================================
    
    def _format_file_size(self, size_bytes):
        """Format file size in bytes to human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def _format_list_as_text(self, items, heading=None, indent=0):
        """Format a list of items as a text list with optional heading."""
        if not items:
            return "No items found."
        
        indentation = " " * indent
        result = f"{heading}\n" if heading else ""
        for i, item in enumerate(items):
            result += f"{indentation}- {item}\n"
        return result
    
    def _format_dict_as_text(self, data, heading=None, indent=0):
        """Format a dictionary as text with optional heading."""
        if not data:
            return "No data found."
        
        indentation = " " * indent
        result = f"{heading}\n" if heading else ""
        for key, value in data.items():
            result += f"{indentation}{key}: {value}\n"
        return result
    
    #========================================
    # FILE OPERATIONS
    #========================================
    
    def list_files(self, path: str = ".") -> str:
        """
        List files in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            Text list of filenames
        """
        files = self.file_client.list_files(path)
        if not files:
            return f"No files found in '{path}'."
        
        return f"Files in '{path}':\n" + "\n".join([f"- {file}" for file in files])
    
    def list_files_with_metadata(self, path: str = ".") -> str:
        """
        List files with detailed metadata in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            Text listing of files with metadata
        """
        files = self.file_client.list_files_with_metadata(path)
        if not files:
            return f"No files found in '{path}'."
        
        result = f"Files with metadata in '{path}':\n"
        for file in files:
            result += f"- {file['name']}\n"
            result += f"  Size: {self._format_file_size(file['size'])}\n"
            result += f"  Modified: {file['modTime']}\n"
            result += f"  Type: {file.get('contentType', 'Unknown')}\n"
            result += f"  Path: {file['path']}\n"
            result += "\n"
        
        return result
    
    def get_file(self, file_path: str) -> str:
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            File content as a string
        """
        return self.file_client.get_file(file_path)
    
    def create_file(self, file_path: str, content: str) -> str:
        """
        Create a new file with the specified content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: Content to write to the file
        
        Returns:
            Text confirmation message
        """
        self.file_client.create_file(file_path, content)
        return f"File '{file_path}' created successfully."
    
    def update_file(self, file_path: str, content: str) -> str:
        """
        Update an existing file with new content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: New content for the file
        
        Returns:
            Text confirmation message
        """
        self.file_client.update_file(file_path, content)
        return f"File '{file_path}' updated successfully."
    
    def delete_file(self, file_path: str) -> str:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file relative to working directory
            
        Returns:
            Text confirmation message
        """
        self.file_client.delete_file(file_path)
        return f"File '{file_path}' deleted successfully."
    
    def get_file_metadata(self, file_path: str) -> str:
        """
        Get metadata for a specific file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            Text representation of file metadata
        """
        meta = self.file_client.get_file_metadata(file_path)
        result = f"Metadata for '{file_path}':\n"
        result += f"Name: {meta['name']}\n"
        result += f"Size: {self._format_file_size(meta['size'])}\n"
        result += f"Modified: {meta['modTime']}\n"
        result += f"Is Directory: {meta['isDir']}\n"
        result += f"Path: {meta['path']}\n"
        if 'contentType' in meta:
            result += f"Content Type: {meta['contentType']}\n"
        if 'permissions' in meta:
            result += f"Permissions: {meta['permissions']}\n"
        
        return result
    
    def batch_read_files(self, file_paths: List[str]) -> str:
        """
        Read multiple files in one request.
        
        Args:
            file_paths: List of file paths to read
        
        Returns:
            Text with content of all files
        """
        results = self.file_client.batch_read_files(file_paths)
        output = f"Contents of {len(file_paths)} files:\n\n"
        
        for result in results:
            output += f"--- {result['path']} ---\n"
            if result['success']:
                output += f"{result['result']}\n"
            else:
                output += f"ERROR: {result['error']}\n"
            output += "\n"
        
        return output
    
    def search_files(self, pattern: str, path: str = ".", recursive: bool = True) -> str:
        """
        Search for a pattern in files.
        
        Args:
            pattern: Pattern to search for
            path: Directory to search in (default: current directory)
            recursive: Whether to search recursively (default: True)
        
        Returns:
            Text with search results
        """
        results = self.file_client.search_files(pattern, path, recursive)
        recursive_text = "recursively" if recursive else "non-recursively"
        output = f"Search for '{pattern}' in '{path}' ({recursive_text}):\n"
        
        if results.get("matchedFiles", 0) == 0:
            return output + "No matches found.\n"
        
        output += f"Found {results.get('matchedFiles', 0)} matching files:\n\n"
        
        for file_path, matches in results.get("results", {}).items():
            output += f"File: {file_path}\n"
            for match in matches[:10]:  # Limit to first 10 matches per file to avoid huge output
                output += f"  {match}\n"
            if len(matches) > 10:
                output += f"  ... and {len(matches) - 10} more matches.\n"
            output += "\n"
        
        return output
    
    def extract_content(self, file_paths: List[str]) -> str:
        """
        Extract content from multiple files, with error handling.
        
        Args:
            file_paths: List of file paths to extract content from
        
        Returns:
            Text with content of all files
        """
        results = self.file_client.extract_content(file_paths)
        output = ""
        
        for path, content in results.items():
            output += f"--- {path} ---\n{content}\n\n"
        
        return output
    
    #========================================
    # DIRECTORY OPERATIONS
    #========================================
    
    def list_directories(self, path: str = ".") -> str:
        """
        List directories in a path.
        
        Args:
            path: Relative path to list directories from (default: current directory)
        
        Returns:
            Text list of directories
        """
        dirs = self.file_client.list_directories(path)
        if not dirs:
            return f"No directories found in '{path}'."
        
        return f"Directories in '{path}':\n" + "\n".join([f"- {d}" for d in dirs])
    
    def create_directory(self, dir_path: str) -> str:
        """
        Create a new directory.
        
        Args:
            dir_path: Path to the directory to create
        
        Returns:
            Text confirmation message
        """
        self.file_client.create_directory(dir_path)
        return f"Directory '{dir_path}' created successfully."
    
    def delete_directory(self, dir_path: str) -> str:
        """
        Delete a directory and all its contents.
        
        Args:
            dir_path: Path to the directory to delete
            
        Returns:
            Text confirmation message
        """
        self.file_client.delete_directory(dir_path)
        return f"Directory '{dir_path}' deleted successfully with all its contents."
    
    def get_directory_tree(self, path: str = ".", depth: int = 2) -> str:
        """
        Get a tree representation of a directory structure.
        
        Args:
            path: Path to get tree for (default: current directory)
            depth: Maximum depth of the tree (default: 2)
        
        Returns:
            Text representation of directory tree
        """
        tree_data = self.file_client.get_directory_tree(path, depth)
        
        def format_tree(entries, indent=""):
            result = ""
            for entry in entries:
                if entry.get("isDir"):
                    result += f"{indent}📁 {entry['name']}/\n"
                    if "children" in entry and entry["children"]:
                        result += format_tree(entry["children"], indent + "  ")
                else:
                    size = entry.get("size", 0)
                    result += f"{indent}📄 {entry['name']} ({self._format_file_size(size)})\n"
            return result
        
        output = f"Directory tree for '{path}' (depth: {depth}):\n"
        if "tree" in tree_data:
            output += format_tree(tree_data["tree"])
        
        return output
    
    def get_directory_size(self, dir_path: str) -> str:
        """
        Calculate the size of a directory.
        
        Args:
            dir_path: Path to the directory
        
        Returns:
            Text with directory size information
        """
        size_data = self.file_client.get_directory_size(dir_path)
        return f"Directory '{dir_path}' size: {self._format_file_size(size_data.get('size', 0))}"
    
    #========================================
    # PROJECT OPERATIONS
    #========================================
    
    def get_project_summary(self) -> str:
        """
        Get a summary of the project in the working directory.
        
        Returns:
            Text summary of project information
        """
        summary = self.file_client.get_project_summary()
        output = f"Project Summary: {summary['name']}\n"
        output += f"Root path: {summary['rootPath']}\n"
        output += f"Files: {summary['fileCount']}\n"
        output += f"Directories: {summary['dirCount']}\n"
        output += f"Total size: {self._format_file_size(summary['totalSize'])}\n\n"
        
        output += "File types:\n"
        for ext, count in summary.get('fileTypes', {}).items():
            ext_name = ext if ext else '(no extension)'
            output += f"- {ext_name}: {count} files\n"
        
        output += "\nKey files:\n"
        for file in summary.get('keyFiles', []):
            output += f"- {file}\n"
        
        return output
    
    def extract_code_context(self, max_files: int = 10) -> str:
        """
        Extract code context for LLM understanding.
        
        Args:
            max_files: Maximum number of files to include (default: 10)
        
        Returns:
            Text with code context information
        """
        context = self.file_client.extract_code_context(max_files)
        output = f"Code context for project: {context['projectName']}\n\n"
        
        output += "Project dependencies:\n"
        for dep in context.get('projectDependencies', []):
            output += f"- {dep}\n"
        
        output += "\nMain files:\n"
        for file_path, file_info in context.get('mainFiles', {}).items():
            output += f"--- {file_path} ---\n"
            output += f"Language: {file_info.get('language', 'Unknown')}\n"
            output += f"Size: {self._format_file_size(file_info.get('size', 0))}\n"
            
            if 'dependencies' in file_info and file_info['dependencies']:
                output += "Dependencies: " + ", ".join(file_info['dependencies']) + "\n"
                
            output += "Content:\n```\n"
            output += file_info.get('content', '')
            output += "\n```\n\n"
        
        return output
    
    def export_file_structure(self, path: str = ".", depth: int = 3) -> str:
        """
        Export the file structure as a nested text representation.
        
        Args:
            path: Path to export structure for (default: current directory)
            depth: Maximum depth of the structure (default: 3)
        
        Returns:
            Text representation of file structure
        """
        structure = self.file_client.export_file_structure(path, depth)
        
        def format_structure(struct, indent=0):
            result = ""
            for name, info in struct.items():
                prefix = " " * indent
                if isinstance(info, dict):
                    if "size" in info and "modTime" in info:
                        # This is a file
                        result += f"{prefix}- {name} ({self._format_file_size(info['size'])})\n"
                    else:
                        # This is a directory
                        result += f"{prefix}+ {name}/\n"
                        result += format_structure(info, indent + 2)
            return result
        
        output = f"File structure for '{path}' (depth: {depth}):\n"
        output += format_structure(json.loads(structure))
        
        return output
    
    def batch_create_files(self, files: Dict[str, str]) -> str:
        """
        Create multiple files at once.
        
        Args:
            files: Dictionary mapping file paths to their content
        
        Returns:
            Text summary of file creation results
        """
        results = self.file_client.batch_create_files(files)
        output = f"Created {len(files)} files:\n"
        
        success_count = 0
        failure_count = 0
        
        for result in results.get("results", []):
            if result.get('success'):
                output += f"- ✅ {result['path']} created successfully\n"
                success_count += 1
            else:
                output += f"- ❌ {result['path']} failed: {result.get('error', 'unknown error')}\n"
                failure_count += 1
        
        output += f"\nSummary: {success_count} files created successfully, {failure_count} failed."
        return output
    
    #========================================
    # COMMAND EXECUTION
    #========================================
    
    def execute_command(self, command: str, timeout: int = 0, environment: Dict[str, str] = None) -> str:
        """
        Execute a command in the current session.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds (0 = no timeout)
            environment: Additional environment variables for the command
        
        Returns:
            Text with command output and result information
        """
        result = self.terminal_client.execute_command(command, timeout, environment)
        
        output = f"Command: {command}\n"
        output += f"Exit code: {result['exitCode']}\n"
        
        if result['stdout']:
            output += "\n--- Standard Output ---\n"
            output += result['stdout']
        
        if result['stderr']:
            output += "\n--- Standard Error ---\n"
            output += result['stderr']
            
        output += f"\nExecution time: {result.get('executionTime', 0):.2f} seconds\n"
        
        return output
    
    def execute_batch_commands(self, commands: List[str], continue_on_error: bool = False, 
                              timeout: int = 0, environment: Dict[str, str] = None) -> str:
        """
        Execute multiple commands in sequence.
        
        Args:
            commands: List of commands to execute
            continue_on_error: Whether to continue execution if a command fails
            timeout: Timeout in seconds per command (0 = no timeout)
            environment: Additional environment variables for all commands
        
        Returns:
            Text with all command outputs and results
        """
        results = self.terminal_client.execute_batch_commands(
            commands, continue_on_error, timeout, environment
        )
        
        output = f"Executed {len(commands)} commands:\n\n"
        
        for i, result in enumerate(results.get("results", [])):
            output += f"Command {i+1}: {result['command']}\n"
            output += f"Exit code: {result['exitCode']}\n"
            
            if result['stdout']:
                output += "--- Standard Output ---\n"
                output += f"{result['stdout']}\n"
            
            if result['stderr']:
                output += "--- Standard Error ---\n"
                output += f"{result['stderr']}\n"
                
            output += f"Execution time: {result.get('executionTime', 0):.2f} seconds\n"
            output += "-" * 40 + "\n"
        
        return output
    
    def run_and_capture(self, command: str) -> str:
        """
        Run a command and return its exit code, stdout, and stderr.
        
        Args:
            command: Command to run
        
        Returns:
            Text with command output and exit code
        """
        exit_code, stdout, stderr = self.terminal_client.run_and_capture(command)
        
        output = f"Command: {command}\n"
        output += f"Exit code: {exit_code}\n"
        
        if stdout:
            output += "\n--- Standard Output ---\n"
            output += stdout
        
        if stderr:
            output += "\n--- Standard Error ---\n"
            output += stderr
            
        return output
    
    #========================================
    # PROCESS MANAGEMENT
    #========================================
    
    def start_process(self, command: str, timeout: int = 0, environment: Dict[str, str] = None) -> str:
        """
        Start a long-running process.
        
        Args:
            command: The command to run
            timeout: Timeout in seconds (0 = no timeout)
            environment: Additional environment variables for the process
        
        Returns:
            Text with process information
        """
        process_info = self.terminal_client.start_process(command, timeout, environment)
        
        output = f"Process started: {command}\n"
        output += f"Process ID: {process_info['id']}\n"
        output += f"Started at: {process_info['startTime']}\n"
        output += f"PID: {process_info.get('pid', 'Unknown')}\n"
        
        return output
    
    def list_processes(self) -> str:
        """
        List all running processes for the current session.
        
        Returns:
            Text listing of running processes
        """
        processes = self.terminal_client.list_processes()
        
        if not processes:
            return "No active processes found."
            
        output = f"Active processes ({len(processes)}):\n\n"
        
        for proc_id, proc in processes.items():
            status = "Running" if proc.get("isRunning") else "Stopped"
            output += f"ID: {proc_id}\n"
            output += f"Command: {proc.get('command', 'Unknown')}\n"
            output += f"Started at: {proc.get('startTime', 'Unknown')}\n"
            output += f"Status: {status}\n"
            output += f"PID: {proc.get('pid', 'Unknown')}\n"
            output += "-" * 40 + "\n"
        
        return output
    
    def get_process(self, process_id: str) -> str:
        """
        Get information about a specific process.
        
        Args:
            process_id: ID of the process to get
        
        Returns:
            Text with process details
        """
        process = self.terminal_client.get_process(process_id)
        
        output = f"Process details for ID: {process_id}\n"
        output += f"Command: {process.get('command', 'Unknown')}\n"
        output += f"Started at: {process.get('startTime', 'Unknown')}\n"
        output += f"Status: {'Running' if process.get('isRunning') else 'Stopped'}\n"
        
        if not process.get("isRunning", False) and "exitCode" in process:
            output += f"Exit code: {process['exitCode']}\n"
            
        output += f"PID: {process.get('pid', 'Unknown')}\n"
        
        return output
    
    def get_process_output(self, process_id: str) -> str:
        """
        Get the stdout and stderr of a process.
        
        Args:
            process_id: ID of the process
        
        Returns:
            Text with process output
        """
        output_data = self.terminal_client.get_process_output(process_id)
        
        output = f"Output for process ID: {process_id}\n\n"
        
        if output_data.get("stdout"):
            output += "--- Standard Output ---\n"
            output += "\n".join(output_data["stdout"]) + "\n"
        else:
            output += "No standard output.\n"
        
        if output_data.get("stderr"):
            output += "\n--- Standard Error ---\n"
            output += "\n".join(output_data["stderr"]) + "\n"
        
        return output
    
    def send_input_to_process(self, process_id: str, input_text: str) -> str:
        """
        Send input to a running process.
        
        Args:
            process_id: ID of the process
            input_text: Text to send to the process stdin
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.send_input_to_process(process_id, input_text)
        return f"Input sent to process {process_id}: '{input_text}'"
    
    def send_signal_to_process(self, process_id: str, signal: str) -> str:
        """
        Send a signal to a running process.
        
        Args:
            process_id: ID of the process
            signal: Signal to send (SIGTERM, SIGKILL, SIGINT, SIGHUP)
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.send_signal_to_process(process_id, signal)
        return f"Signal {signal} sent to process {process_id}"
    
    def run_interactive_command(self, command: str) -> str:
        """
        Start an interactive process and return its ID.
        
        Args:
            command: Command to run interactively
        
        Returns:
            Text with process ID and instructions
        """
        process_id = self.terminal_client.run_interactive_command(command)
        
        output = f"Interactive process started: {command}\n"
        output += f"Process ID: {process_id}\n\n"
        output += "Use the following methods to interact with this process:\n"
        output += "- send_input_to_process(process_id, input_text)\n"
        output += "- get_process_output(process_id)\n"
        output += "- send_signal_to_process(process_id, signal)\n"
        
        return output
    
    #========================================
    # ENVIRONMENT VARIABLES
    #========================================
    
    def get_env_vars(self) -> str:
        """
        Get all environment variables for the current session.
        
        Returns:
            Text listing of all environment variables
        """
        env_vars = self.terminal_client.get_env_vars()
        
        if not env_vars:
            return "No environment variables found."
            
        output = f"Environment Variables ({len(env_vars)}):\n\n"
        
        # Sort keys for consistent output
        for key in sorted(env_vars.keys()):
            output += f"{key}={env_vars[key]}\n"
        
        return output
    
    def set_env_var(self, key: str, value: str) -> str:
        """
        Set an environment variable.
        
        Args:
            key: Environment variable name
            value: Environment variable value
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.set_env_var(key, value)
        return f"Environment variable set: {key}={value}"
    
    def set_batch_env_vars(self, env_vars: Dict[str, str]) -> str:
        """
        Set multiple environment variables at once.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Text confirmation message with all variables set
        """
        self.terminal_client.set_batch_env_vars(env_vars)
        
        output = f"Set {len(env_vars)} environment variables:\n"
        for key, value in env_vars.items():
            output += f"- {key}={value}\n"
        
        return output
    
    def unset_env_var(self, key: str) -> str:
        """
        Unset (delete) an environment variable.
        
        Args:
            key: Name of the environment variable to unset
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.unset_env_var(key)
        return f"Environment variable '{key}' removed"
    
    def get_environment_value(self, key: str) -> str:
        """
        Get a specific environment variable value.
        
        Args:
            key: Environment variable name
        
        Returns:
            Text with variable name and value
        """
        value = self.terminal_client.get_environment_value(key)
        if value is None:
            return f"Environment variable '{key}' not found"
        return f"{key}={value}"
    
    def set_working_environment(self, env_vars: Dict[str, str]) -> str:
        """
        Set up a working environment with multiple variables.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.set_working_environment(env_vars)
        
        output = f"Working environment set up with {len(env_vars)} variables:\n"
        for key, value in env_vars.items():
            output += f"- {key}={value}\n"
        
        return output
    
    #========================================
    # COMMAND HISTORY
    #========================================
    
    def get_command_history(self, limit: int = 0) -> str:
        """
        Get command history for the current session.
        
        Args:
            limit: Maximum number of history entries to return (0 = all)
        
        Returns:
            Text with command history
        """
        history = self.terminal_client.get_command_history(limit)
        
        if not history.get("history"):
            return "No command history available."
            
        entries = history.get("history", [])
        limit_text = f" (limited to {limit})" if limit > 0 else ""
        output = f"Command history{limit_text}:\n\n"
        
        for i, entry in enumerate(entries):
            output += f"{i+1}. [{entry['timestamp']}] {entry['command']}\n"
        
        return output
    
    def search_command_history(self, query: str) -> str:
        """
        Search command history for the current session.
        
        Args:
            query: Search query
        
        Returns:
            Text with matching history entries
        """
        results = self.terminal_client.search_command_history(query)
        
        entries = results.get("history", [])
        if not entries:
            return f"No commands found matching '{query}'."
            
        output = f"Command history entries matching '{query}':\n\n"
        
        for i, entry in enumerate(entries):
            output += f"{i+1}. [{entry['timestamp']}] {entry['command']}\n"
        
        return output
    
    def clear_command_history(self) -> str:
        """
        Clear command history for the current session.
        
        Returns:
            Text confirmation message
        """
        self.terminal_client.clear_command_history()
        return "Command history cleared"
    
    #========================================
    # SYSTEM INFORMATION
    #========================================
    
    def get_system_info(self) -> str:
        """
        Get information about the server system.
        
        Returns:
            Text with system information
        """
        info = self.terminal_client.get_system_info()
        
        output = "System Information:\n"
        output += f"Hostname: {info.get('hostname', 'Unknown')}\n"
        output += f"OS: {info.get('os', 'Unknown')}\n"
        output += f"Distribution: {info.get('distribution', 'Unknown')}\n"
        output += f"Architecture: {info.get('architecture', 'Unknown')}\n"
        output += f"CPU cores: {info.get('numCPU', 'Unknown')}\n"
        output += f"Current time: {info.get('currentTime', 'Unknown')}\n"
        output += f"Timezone: {info.get('timezone', 'Unknown')}\n"
        
        return output
    
    def get_available_shells(self) -> str:
        """
        Get available shell programs on the server.
        
        Returns:
            Text listing of available shells
        """
        shells = self.terminal_client.get_available_shells()
        
        output = "Available Shells:\n"
        output += f"Current shell: {shells.get('currentShell', 'Unknown')}\n\n"
        
        available = shells.get("availableShells", {})
        if not available:
            output += "No shell information available."
            return output
            
        output += "Available shells:\n"
        for shell, is_available in available.items():
            status = "✅ Available" if is_available else "❌ Not available"
            output += f"- {shell} ({status})\n"
        
        return output
    
    #========================================
    # SESSION MANAGEMENT
    #========================================
    
    def get_file_session_info(self) -> str:
        """
        Get information about the current file API session.
        
        Returns:
            Text with session information
        """
        info = self.file_client.get_session_info()
        
        output = "File API Session Info:\n"
        output += f"ID: {info['id']}\n"
        output += f"Created: {info['createdAt']}\n"
        output += f"Last active: {info['lastActive']}\n"
        output += f"Working directory: {info['workingDir']}\n"
        output += f"Active: {info['isActive']}\n"
        output += f"Expires: {info['expiresAt']}\n"
        
        return output
    
    def get_terminal_session_info(self) -> str:
        """
        Get information about the current terminal API session.
        
        Returns:
            Text with session information
        """
        info = self.terminal_client.get_session_info()
        
        output = "Terminal API Session Info:\n"
        output += f"ID: {info['id']}\n"
        output += f"Created: {info['createdAt']}\n"
        output += f"Last active: {info['lastActive']}\n"
        output += f"Working directory: {info['workingDir']}\n"
        output += f"Active: {info['isActive']}\n"
        output += f"Expires: {info['expiresAt']}\n"
        
        return output
    
    def change_working_directory(self, new_dir: str) -> str:
        """
        Change the working directory for both sessions.
        
        Args:
            new_dir: The new working directory path
        
        Returns:
            Text confirmation message
        """
        # Update internal working directory
        self.working_dir = os.path.abspath(new_dir)
        
        # Change directory for both APIs
        self.file_client.change_working_directory(new_dir)
        self.terminal_client.change_working_directory(new_dir)
        
        return f"Working directory changed to: {new_dir}"
    
    #========================================
    # DIFF AND PATCH OPERATIONS
    #========================================
    
    def generate_diff(self, 
                    original_path: str = None, 
                    modified_path: str = None,
                    original_content: str = None,
                    modified_content: str = None) -> str:
        """
        Generate a diff between two files or content.
        
        You must provide either paths or content, but not both.
        
        Args:
            original_path: Path to the original file
            modified_path: Path to the modified file
            original_content: Original content string
            modified_content: Modified content string
        
        Returns:
            Text with diff patches
        """
        result = self.file_client.generate_diff(
            original_path, modified_path, original_content, modified_content
        )
        
        output = "Diff Patches:\n\n"
        output += result["patches"]
        
        return output
    
    def apply_patch(self, file_path: str, patches: str) -> str:
        """
        Apply patches to a file. Automatically reads the file content and applies the patches.
        
        Args:
            file_path: Path to the file to patch
            patches: Patches to apply
        
        Returns:
            Text with patched content
        """
        result = self.file_client.apply_patch(file_path, patches)
        
        output = f"Patches applied to file: {file_path}\n\n"
        output += "Resulting content:\n"
        output += result["result"]
        
        return output
    
    #========================================
    # HELPER METHODS
    #========================================
    
    def read_and_update_file(self, file_path: str, update_func) -> str:
        """
        Read a file, apply a function to its content, and update the file.
        
        Args:
            file_path: Path to the file
            update_func: Function that takes the file content and returns updated content
        
        Returns:
            Text confirmation message
        """
        self.file_client.read_and_update_file(file_path, update_func)
        return f"File '{file_path}' updated using the provided function."
    
    def find_files_by_extension(self, extension: str, path: str = ".", recursive: bool = True) -> str:
        """
        Find all files with a specific extension.
        
        Args:
            extension: File extension to search for (e.g., ".py")
            path: Directory to search in (default: current directory)
            recursive: Whether to search recursively (default: True)
        
        Returns:
            Text list of matching files
        """
        files = self.file_client.find_files_by_extension(extension, path, recursive)
        
        if not files:
            return f"No files with extension '{extension}' found in '{path}'."
            
        recursive_text = "recursively" if recursive else "non-recursively"
        output = f"Files with extension '{extension}' in '{path}' ({recursive_text}):\n"
        
        for file in files:
            output += f"- {file}\n"
        
        return output
    
    def get_project_files_by_type(self, file_types: List[str], max_per_type: int = 5) -> str:
        """
        Get a dictionary of project files organized by file type.
        
        Args:
            file_types: List of file extensions to fetch (e.g., ["py", "js", "go"])
            max_per_type: Maximum number of files to fetch per type
            
        Returns:
            Text listing of files by type
        """
        result = self.file_client.get_project_files_by_type(file_types, max_per_type)
        
        if not result:
            return f"No files found with types: {', '.join(file_types)}"
            
        output = f"Project files by type (max {max_per_type} per type):\n\n"
        
        for file_type, files in result.items():
            output += f"{file_type} files:\n"
            for file in files:
                output += f"- {file}\n"
            output += "\n"
        
        return output
    
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Text confirmation message
        """
        backup_path = self.file_client.backup_file(file_path)
        return f"File '{file_path}' backed up to '{backup_path}'"
    
    def read_file_safely(self, file_path: str) -> str:
        """
        Read a file with error handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Text with file content or error message
        """
        success, content = self.file_client.read_file_safely(file_path)
        
        if success:
            return f"Content of '{file_path}':\n\n{content}"
        else:
            return f"Error reading '{file_path}': {content}"
    
    def save_file_safely(self, file_path: str, content: str) -> str:
        """
        Save a file with error handling.
        
        Args:
            file_path: Path to the file to save
            content: Content to write to the file
            
        Returns:
            Text confirmation message
        """
        success, message = self.file_client.save_file_safely(file_path, content)
        
        if success:
            return f"File '{file_path}' saved successfully."
        else:
            return f"Error saving '{file_path}': {message}"
    
    def file_exists(self, file_path: str) -> str:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Text indicating whether file exists
        """
        exists = self.file_client.file_exists(file_path)
        if exists:
            return f"File '{file_path}' exists."
        else:
            return f"File '{file_path}' does not exist."
    
    def directory_exists(self, dir_path: str) -> str:
        """
        Check if a directory exists.
        
        Args:
            dir_path: Path to the directory to check
            
        Returns:
            Text indicating whether directory exists
        """
        exists = self.file_client.directory_exists(dir_path)
        if exists:
            return f"Directory '{dir_path}' exists."
        else:
            return f"Directory '{dir_path}' does not exist."
    
    def ensure_directory_exists(self, dir_path: str) -> str:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            Text confirmation message
        """
        exists = self.file_client.ensure_directory_exists(dir_path)
        if exists:
            return f"Directory '{dir_path}' exists or was created successfully."
        else:
            return f"Failed to create directory '{dir_path}'."
    
    def execute_commands_in_shell(self, commands: List[str], shell: str = None) -> str:
        """
        Execute multiple commands in a specific shell.
        
        Args:
            commands: List of commands to execute
            shell: Shell to use (if None, uses session default)
        
        Returns:
            Text with all command outputs
        """
        results = self.terminal_client.execute_commands_in_shell(commands, shell)
        
        shell_text = f" using {shell}" if shell else ""
        output = f"Executed {len(commands)} commands{shell_text}:\n\n"
        
        for i, result in enumerate(results):
            output += f"Command {i+1}: {commands[i]}\n"
            output += f"Exit code: {result['exitCode']}\n"
            
            if result['stdout']:
                output += "--- Standard Output ---\n"
                output += f"{result['stdout']}\n"
            
            if result['stderr']:
                output += "--- Standard Error ---\n"
                output += f"{result['stderr']}\n"
                
            output += f"Execution time: {result.get('executionTime', 0):.2f} seconds\n"
            output += "-" * 40 + "\n"
        
        return output
    
    #========================================
    # INTEGRATED OPERATIONS
    #========================================
    
    def edit_and_run_file(self, file_path: str, content: str = None) -> str:
        """
        Edit a file (or create if it doesn't exist) and then run it.
        
        Args:
            file_path: Path to the file to edit and run
            content: New content for the file. If None, the file is run without modification.
        
        Returns:
            Text with execution results
        """
        # Check if the file exists
        exists = self.file_exists(file_path)
        
        # If content is provided, update or create the file
        if content is not None:
            if "exists" in exists:  # Check if the file exists based on the string returned by file_exists
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
            return f"Don't know how to run file with extension {ext}"
        
        # Execute the command
        result = self.execute_command(cmd)
        
        if content is not None:
            return f"File '{file_path}' updated and executed:\n\n{result}"
        else:
            return f"File '{file_path}' executed:\n\n{result}"
    
    def find_and_replace_in_files(self, pattern: str, replacement: str, path: str = ".", 
                                file_pattern: str = None, recursive: bool = True) -> str:
        """
        Find a pattern in files and replace it with another string.
        
        Args:
            pattern: Pattern to search for
            replacement: Text to replace the pattern with
            path: Directory to search in (default: current directory)
            file_pattern: Optional pattern to filter files (e.g., "*.py")
            recursive: Whether to search recursively (default: True)
        
        Returns:
            Text summary of find and replace operation
        """
        # First, find files containing the pattern
        search_results = self.file_client.search_files(pattern, path, recursive)
        
        import fnmatch
        
        files_modified = 0
        occurrences_replaced = 0
        modified_files = {}
        
        # Process each file that had matches
        for file_path, matches in search_results.get("results", {}).items():
            # Skip if file doesn't match the file pattern
            if file_pattern and not fnmatch.fnmatch(file_path, file_pattern):
                continue
                
            # Skip if the file name was what matched, not the content
            if matches == ["[Filename matches search pattern]"]:
                continue
                
            try:
                # Read the file
                content = self.file_client.get_file(file_path)
                
                # Count occurrences before replacement
                original_count = content.count(pattern)
                
                if original_count > 0:
                    # Replace occurrences
                    new_content = content.replace(pattern, replacement)
                    
                    # Update the file
                    self.file_client.update_file(file_path, new_content)
                    
                    # Track stats
                    files_modified += 1
                    occurrences_replaced += original_count
                    modified_files[file_path] = original_count
            except Exception as e:
                return f"Error processing {file_path}: {str(e)}"
                
        # Create output
        output = f"Find and Replace Summary:\n"
        output += f"Pattern: '{pattern}'\n"
        output += f"Replacement: '{replacement}'\n"
        output += f"Path: {path}\n"
        output += f"Recursive: {recursive}\n"
        output += f"File pattern: {file_pattern if file_pattern else 'None'}\n\n"
        output += f"Files modified: {files_modified}\n"
        output += f"Occurrences replaced: {occurrences_replaced}\n\n"
        
        if modified_files:
            output += "Modified files:\n"
            for file, count in modified_files.items():
                output += f"- {file}: {count} occurrences\n"
        
        return output
    
    def backup_project(self, output_path: str = None) -> str:
        """
        Create a backup of the current project directory.
        
        Args:
            output_path: Path where to save the backup. If None, saves with timestamp.
            
        Returns:
            Text confirmation message with backup path
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
            result = self.terminal_client.execute_command(cmd)
            
            if result["exitCode"] == 0:
                return f"Project backed up successfully to '{output_path}.tar.gz'"
            else:
                # If tar fails, try a simple directory copy
                shutil.copytree(self.working_dir, output_path)
                return f"Project backed up successfully to '{output_path}' (uncompressed)"
        except:
            # Fallback to Python's shutil if terminal command fails
            try:
                shutil.copytree(self.working_dir, output_path)
                return f"Project backed up successfully to '{output_path}' (uncompressed)"
            except Exception as e:
                return f"Error backing up project: {str(e)}"
    
    def script_and_execute(self, script_content: str, script_path: str = None, 
                         interpreter: str = "python") -> str:
        """
        Create a script file and execute it.
        
        Args:
            script_content: Content of the script to create and run
            script_path: Path where to save the script. If None, creates a temporary file.
            interpreter: Interpreter to use (python, bash, node, etc.)
            
        Returns:
            Text with execution results
        """
        import tempfile
        
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
        self.file_client.create_file(os.path.basename(script_path), script_content)
        
        # Make sure the script is executable (for shell scripts)
        if interpreter.lower() in ["bash", "sh"]:
            self.terminal_client.execute_command(f"chmod +x {script_path}")
        
        # Execute the script using the specified interpreter
        result = self.execute_command(f"{interpreter} {script_path}")
        
        return f"Created and executed script at '{script_path}':\n\n{result}"
    
    #========================================
    # CLEANUP AND SESSION MANAGEMENT
    #========================================
    
    def cleanup_sessions(self) -> str:
        """
        Clean up all sessions explicitly, terminating both clients.
        
        Returns:
            Text confirmation message
        """
        # Clean up terminal session
        if hasattr(self, 'terminal_client') and self.terminal_client:
            self.terminal_client.cleanup()
        
        # Clean up file session
        if hasattr(self, 'file_client') and self.file_client:
            self.file_client.cleanup()
            
        return "All sessions cleaned up successfully"


# Example usage
if __name__ == "__main__":
    # Create the unified client
    client = Tools()
    
    # Get system info
    system_info = client.get_system_info()
    print(system_info)
    
    # Create a test file
    print(client.create_file("test_script.py", """print('Hello from PocketFlow!')\ndef todo():\n\tprint('This is a test script.')\ntodo()"""))
    
    # List files
    print(client.list_files())
    
    # Execute the script
    print(client.execute_command("python test_script.py"))
    
    # Get environment variables
    print(client.get_env_vars())
    
    # Clean up test file
    print(client.delete_file("test_script.py"))
    
    print("Demonstration completed. Sessions will be cleaned up automatically on exit.")
    # Sessions are automatically cleaned up when the client is destroyed

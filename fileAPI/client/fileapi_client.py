import os
import json
import time
import requests
import atexit
from typing import Dict, List, Union, Optional, Any, Tuple, BinaryIO

class FileAPIClient:
    """
    Comprehensive client for interacting with the fileAPI server.
    
    This client automatically handles session creation and management,
    and provides methods for all API endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", working_dir: str = None):
        """
        Initialize the FileAPI client.
        
        Args:
            base_url: The base URL of the fileAPI server
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
        return self._set_working_directory()
    
    # File Operations
    
    def list_files(self, path: str = ".") -> List[str]:
        """
        List files in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            List of filenames
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/files",
            params={"path": path}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to list files: {response.text}")
        
        return response.json().get("files", [])
    
    def list_files_with_metadata(self, path: str = ".") -> List[Dict]:
        """
        List files with detailed metadata in a directory.
        
        Args:
            path: Relative path to the directory (default: current directory)
        
        Returns:
            List of file metadata objects
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/files-metadata",
            params={"path": path}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to list files with metadata: {response.text}")
        
        return response.json().get("files", [])
    
    def get_file(self, file_path: str) -> str:
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            File content as a string
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/files/{file_path}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to read file: {response.text}")
        
        return response.json().get("content", "")
    
    def create_file(self, file_path: str, content: str) -> Dict:
        """
        Create a new file with the specified content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: Content to write to the file
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"content": content}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/files/{file_path}",
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create file: {response.text}")
        
        return response.json()
    
    def update_file(self, file_path: str, content: str) -> Dict:
        """
        Update an existing file with new content.
        
        Args:
            file_path: Path to the file relative to working directory
            content: New content for the file
        
        Returns:
            Response message
        """
        self._check_session()
        
        payload = {"content": content}
        response = requests.put(
            f"{self.base_url}/sessions/{self.session_id}/files/{file_path}",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to update file: {response.text}")
        
        return response.json()
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file relative to working directory
        """
        self._check_session()
        
        response = requests.delete(
            f"{self.base_url}/sessions/{self.session_id}/files/{file_path}"
        )
        
        if response.status_code != 204:
            raise Exception(f"Failed to delete file: {response.text}")
    
    def get_file_metadata(self, file_path: str) -> Dict:
        """
        Get metadata for a specific file.
        
        Args:
            file_path: Path to the file relative to working directory
        
        Returns:
            File metadata
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/file-metadata/{file_path}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get file metadata: {response.text}")
        
        return response.json()
    
    def batch_read_files(self, file_paths: List[str]) -> List[Dict]:
        """
        Read multiple files in one request.
        
        Args:
            file_paths: List of file paths to read
        
        Returns:
            List of results with file content
        """
        self._check_session()
        
        payload = {"files": file_paths}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/batch-read",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to batch read files: {response.text}")
        
        return response.json().get("results", [])
    
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
        self._check_session()
        
        payload = {
            "pattern": pattern,
            "path": path,
            "recursive": recursive
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/search",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to search files: {response.text}")
        
        return response.json()
    
    def extract_content(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Extract content from multiple files, with error handling.
        
        Args:
            file_paths: List of file paths to extract content from
        
        Returns:
            Dictionary mapping file paths to their content
        """
        self._check_session()
        
        payload = {"files": file_paths}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/extract",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to extract content: {response.text}")
        
        return response.json()
    
    # Directory Operations
    
    def list_directories(self, path: str = ".") -> List[str]:
        """
        List directories in a path.
        
        Args:
            path: Relative path to list directories from (default: current directory)
        
        Returns:
            List of directory names
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/directories",
            params={"path": path}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to list directories: {response.text}")
        
        return response.json().get("directories", [])
    
    def create_directory(self, dir_path: str) -> Dict:
        """
        Create a new directory.
        
        Args:
            dir_path: Path to the directory to create
        
        Returns:
            Response message
        """
        self._check_session()
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/directories/{dir_path}"
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create directory: {response.text}")
        
        return response.json()
    
    def delete_directory(self, dir_path: str) -> None:
        """
        Delete a directory and all its contents.
        
        Args:
            dir_path: Path to the directory to delete
        """
        self._check_session()
        
        response = requests.delete(
            f"{self.base_url}/sessions/{self.session_id}/directories/{dir_path}"
        )
        
        if response.status_code != 204:
            raise Exception(f"Failed to delete directory: {response.text}")
    
    def get_directory_tree(self, path: str = ".", depth: int = 2) -> Dict:
        """
        Get a tree representation of a directory structure.
        
        Args:
            path: Path to get tree for (default: current directory)
            depth: Maximum depth of the tree (default: 2)
        
        Returns:
            Directory tree
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/directory-tree",
            params={"path": path, "depth": depth}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get directory tree: {response.text}")
        
        return response.json()
    
    def get_directory_size(self, dir_path: str) -> Dict:
        """
        Calculate the size of a directory.
        
        Args:
            dir_path: Path to the directory
        
        Returns:
            Directory size information
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/directory-size/{dir_path}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get directory size: {response.text}")
        
        return response.json()
    
    # Project Operations
    
    def get_project_summary(self) -> Dict:
        """
        Get a summary of the project in the working directory.
        
        Returns:
            Project summary information
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/project"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get project summary: {response.text}")
        
        return response.json()
    
    def extract_code_context(self, max_files: int = 10) -> Dict:
        """
        Extract code context for LLM understanding.
        
        Args:
            max_files: Maximum number of files to include (default: 10)
        
        Returns:
            Code context information
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/project/context",
            params={"maxFiles": max_files}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to extract code context: {response.text}")
        
        return response.json()
    
    def export_file_structure(self, path: str = ".", depth: int = 3) -> Dict:
        """
        Export the file structure as a nested JSON object.
        
        Args:
            path: Path to export structure for (default: current directory)
            depth: Maximum depth of the structure (default: 3)
        
        Returns:
            File structure information
        """
        self._check_session()
        
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/project/structure",
            params={"path": path, "depth": depth}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to export file structure: {response.text}")
        
        return response.json()
    
    def batch_create_files(self, files: Dict[str, str]) -> Dict:
        """
        Create multiple files at once.
        
        Args:
            files: Dictionary mapping file paths to their content
        
        Returns:
            Results for each file creation
        """
        self._check_session()
        
        payload = {"files": files}
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/project/batch-create",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to batch create files: {response.text}")
        
        return response.json()
    
    # Diff and Patch Operations
    
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
        self._check_session()
        
        if (original_path and not modified_path) or (not original_path and modified_path):
            raise ValueError("You must provide both original_path and modified_path or neither")
            
        if (original_content and not modified_content) or (not original_content and modified_content):
            raise ValueError("You must provide both original_content and modified_content or neither")
            
        if not (original_path or original_content):
            raise ValueError("You must provide either paths or content to compare")
        
        payload = {}
        if original_path and modified_path:
            payload = {
                "originalPath": original_path,
                "modifiedPath": modified_path
            }
        else:
            payload = {
                "original": original_content,
                "modified": modified_content
            }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/diff",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to generate diff: {response.text}")
        
        return response.json()
    
    def apply_patch(self, file_path: str, patches: str) -> Dict:
        """
        Apply patches to a file. Automatically reads the file content and applies the patches.
        
        Args:
            file_path: Path to the file to patch
            patches: Patches to apply
        
        Returns:
            Dictionary with the patched content
        """
        self._check_session()
        
        # Read the original content from the file
        original_content = self.get_file(file_path)
        
        payload = {
            "filePath": file_path,
            "original": original_content,
            "patches": patches
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/patch",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to apply patch: {response.text}")
        
        return response.json()
    
    # Helper Methods
    
    def read_and_update_file(self, file_path: str, update_func) -> Dict:
        """
        Read a file, apply a function to its content, and update the file.
        
        Args:
            file_path: Path to the file
            update_func: Function that takes the file content and returns updated content
        
        Returns:
            Update response
        """
        content = self.get_file(file_path)
        updated_content = update_func(content)
        return self.update_file(file_path, updated_content)
    
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
        # Ensure the extension starts with a period
        if not extension.startswith("."):
            extension = "." + extension
            
        # Use the search endpoint to find files with the extension
        results = self.search_files(extension, path, recursive)
        
        # Extract just the file paths that end with the extension
        matching_files = []
        for file_path, _ in results.get("results", {}).items():
            if file_path.endswith(extension):
                matching_files.append(file_path)
        
        return matching_files
    
    def get_project_files_by_type(self, file_types: List[str], max_per_type: int = 5) -> Dict[str, List[str]]:
        """
        Get a dictionary of project files organized by file type.
        
        Args:
            file_types: List of file extensions to fetch (e.g., ["py", "js", "go"])
            max_per_type: Maximum number of files to fetch per type
            
        Returns:
            Dictionary mapping file types to lists of files
        """
        result = {}
        summary = self.get_project_summary()
        
        for file_ext in file_types:
            # Ensure file extension has a dot
            if not file_ext.startswith("."):
                file_ext = "." + file_ext
                
            # Find this type in the summary
            count = summary.get("fileTypes", {}).get(file_ext, 0)
            if count > 0:
                files = self.find_files_by_extension(file_ext)
                result[file_ext] = files[:max_per_type]
                
        return result
    
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        content = self.get_file(file_path)
        backup_path = f"{file_path}.bak.{int(time.time())}"
        self.create_file(backup_path, content)
        return backup_path

    def read_file_safely(self, file_path: str) -> Tuple[bool, str]:
        """
        Read a file with error handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Tuple of (success, content)
        """
        try:
            content = self.get_file(file_path)
            return True, content
        except Exception as e:
            return False, str(e)
            
    def save_file_safely(self, file_path: str, content: str) -> Tuple[bool, str]:
        """
        Save a file with error handling.
        
        Args:
            file_path: Path to the file to save
            content: Content to write to the file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.file_exists(file_path):
                self.update_file(file_path, content)
            else:
                self.create_file(file_path, content)
            return True, f"Successfully saved {file_path}"
        except Exception as e:
            return False, str(e)
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        try:
            self.get_file_metadata(file_path)
            return True
        except:
            return False
            
    def directory_exists(self, dir_path: str) -> bool:
        """
        Check if a directory exists.
        
        Args:
            dir_path: Path to the directory to check
            
        Returns:
            True if the directory exists, False otherwise
        """
        try:
            dirs = self.list_directories(os.path.dirname(dir_path.rstrip('/')))
            return os.path.basename(dir_path.rstrip('/')) in dirs
        except:
            return False

    def ensure_directory_exists(self, dir_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if the directory exists or was created, False otherwise
        """
        if self.directory_exists(dir_path):
            return True
            
        try:
            self.create_directory(dir_path)
            return True
        except:
            return False


# Example usage:
if __name__ == "__main__":
    # Create client
    client = FileAPIClient()
    
    # Get session info
    session_info = client.get_session_info()
    print(f"Session info: {session_info}")
    
    # List files in current directory
    files = client.list_files()
    print(f"Files in current directory: {files}")
    
    # Create a file
    client.create_file("test.txt", "Hello, fileAPI!")
    
    # Read the file
    content = client.get_file("test.txt")
    print(f"File content: {content}")
    
    # Update the file
    client.update_file("test.txt", "Updated content")
    
    # Delete the file
    client.delete_file("test.txt")
    
    # Get project summary
    summary = client.get_project_summary()
    print(f"Project has {summary.get('fileCount')} files and {summary.get('dirCount')} directories")

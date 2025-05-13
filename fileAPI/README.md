# PocketFlow - Advanced File Operations API

An API service providing comprehensive file and folder operations with session-based state management, optimized for LLMs and development workflows.

## Features

- **Session Management**: Create and manage isolated working sessions
- **File Operations**: Create, read, update, delete, search, and batch operations
- **Directory Operations**: List, create, delete directories with tree structure support
- **Diff & Patch**: Generate and apply diffs between files
- **Project Context**: Extract code project structure and context for LLMs
- **LLM Assistance**: Specialized endpoints for AI code assistance
- **Batch Operations**: Efficiently work with multiple files at once

## Getting Started

### Prerequisites
- Go 1.16 or later
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pocketflow.git
cd pocketflow
```

2. Download dependencies:
```bash
go mod download
```

3. Start the server:
```bash
go run main.go
```

The server will start on port 8080.

## API Documentation

### Session Management
- **Create Session**: `POST /sessions`
- **Get Session**: `GET /sessions/{sessionId}`
- **List Sessions**: `GET /sessions`
- **Delete Session**: `DELETE /sessions/{sessionId}`
- **Set Working Directory**: `PUT /sessions/{sessionId}/cwd`

### File Operations
- **List Files**: `GET /sessions/{sessionId}/files?path=path/to/dir`
- **List Files with Metadata**: `GET /sessions/{sessionId}/files-metadata?path=path/to/dir`
- **Get File**: `GET /sessions/{sessionId}/files/path/to/file`
- **Get File Metadata**: `GET /sessions/{sessionId}/file-metadata/path/to/file`
- **Create File**: `POST /sessions/{sessionId}/files/path/to/file`
- **Update File**: `PUT /sessions/{sessionId}/files/path/to/file`
- **Delete File**: `DELETE /sessions/{sessionId}/files/path/to/file`
- **Batch Read Files**: `POST /sessions/{sessionId}/batch-read`
- **Search Files**: `POST /sessions/{sessionId}/search`

### Directory Operations
- **List Directories**: `GET /sessions/{sessionId}/directories?path=path/to/dir`
- **Get Directory Tree**: `GET /sessions/{sessionId}/directory-tree?path=path&depth=3`
- **Get Directory Size**: `GET /sessions/{sessionId}/directory-size/path/to/dir`
- **Create Directory**: `POST /sessions/{sessionId}/directories/path/to/dir`
- **Delete Directory**: `DELETE /sessions/{sessionId}/directories/path/to/dir`

### Diff and Patch Operations
- **Generate Diff**: `POST /sessions/{sessionId}/diff`
- **Apply Patch**: `POST /sessions/{sessionId}/patch`

### Project Operations
- **Get Project Summary**: `GET /sessions/{sessionId}/project`
- **Extract Code Context**: `GET /sessions/{sessionId}/project/context?maxFiles=10`
- **Get Project Structure**: `GET /sessions/{sessionId}/project/structure?depth=3`
- **Batch Create Files**: `POST /sessions/{sessionId}/project/batch-create`

### LLM Assistance
- **Extract Content**: `POST /sessions/{sessionId}/extract`
- **Search Content**: `POST /sessions/{sessionId}/search`

## Examples

### Working with Sessions

```bash
# Create a session
curl -X POST http://localhost:8080/sessions

# Response:
# {
#   "id": "f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e",
#   "createdAt": "2023-06-15T10:30:45Z",
#   "lastActive": "2023-06-15T10:30:45Z",
#   "workingDir": "",
#   "isActive": true,
#   "expiresAt": "2023-06-16T10:30:45Z"
# }

# Set working directory
curl -X PUT http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/cwd \
  -H "Content-Type: application/json" \
  -d '{"workingDirectory": "/path/to/project"}'
```

### Extracting Project Context for LLMs

```bash
# Get project context for LLM
curl -X GET "http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/project/context?maxFiles=5"
```

### Batch File Operations

```bash
# Create multiple files at once
curl -X POST http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/project/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "files": {
      "src/main.go": "package main\n\nfunc main() {\n\tprintln(\"Hello, World!\")\n}",
      "README.md": "# My Project\n\nThis is a sample project.",
      "config.json": "{\n\t\"version\": \"1.0.0\"\n}"
    }
  }'
```

## Usage with LLMs

PocketFlow is specifically designed to help LLMs interact with codebases efficiently. The project summary and code context endpoints provide LLMs with structured information about projects to improve their code understanding and generation capabilities.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

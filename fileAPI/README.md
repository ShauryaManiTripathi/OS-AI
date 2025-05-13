# fileAPI - File Operations API for Code Exploration

A comprehensive API service providing file and directory operations through a RESTful interface, specifically designed to help LLMs explore, understand, and modify codebases. fileAPI offers session-based state management, code analysis, diff generation, and batch operations to simplify working with files programmatically.

## Key Features

- **Session Management**: Create isolated working sessions with automatic expiration (24h default)
- **File Operations**: Create, read, update, delete, search, metadata extraction, and batch operations
- **Directory Navigation**: Traverse directory structures with tree visualization and size calculation
- **Code Intelligence**: Extract project summaries, dependencies, and structured code context
- **Diff & Patch**: Generate and apply diffs between files or text content
- **Language Support**: Dependency detection for many languages (Go, JavaScript, Python, Java, etc.)
- **LLM Assistance**: Purpose-built endpoints for AI code understanding and generation

## Getting Started

### Prerequisites
- Go 1.16 or later
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fileAPI.git
cd fileAPI
```

2. Download dependencies:
```bash
go mod download
```

3. Start the server:
```bash
# Either use go run
go run main.go

# Or build and run
go build
./fileAPI
```

The server will start on port 8080 by default.

## API Reference

### Session Management

Sessions are the foundation of all operations. Create a session first, set a working directory, then perform file operations.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions` | POST | Create a new session |
| `/sessions` | GET | List all active sessions |
| `/sessions/{sessionId}` | GET | Get details for a specific session |
| `/sessions/{sessionId}` | DELETE | Delete a session |
| `/sessions/{sessionId}/cwd` | PUT | Set working directory for a session |

### File Operations

Interact with files in the context of a session.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/files?path=dir` | GET | List files in directory |
| `/sessions/{sessionId}/files-metadata?path=dir` | GET | List files with metadata |
| `/sessions/{sessionId}/files/*` | GET | Get file content |
| `/sessions/{sessionId}/files/*` | POST | Create a file |
| `/sessions/{sessionId}/files/*` | PUT | Update a file |
| `/sessions/{sessionId}/files/*` | DELETE | Delete a file |
| `/sessions/{sessionId}/file-metadata/*` | GET | Get file metadata |
| `/sessions/{sessionId}/batch-read` | POST | Read multiple files at once |
| `/sessions/{sessionId}/search` | POST | Search across files |
| `/sessions/{sessionId}/extract` | POST | Extract content from multiple files |

### Directory Operations

Work with directory structures.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/directories?path=dir` | GET | List directories |
| `/sessions/{sessionId}/directories/*` | POST | Create directory |
| `/sessions/{sessionId}/directories/*` | DELETE | Delete directory |
| `/sessions/{sessionId}/directory-tree?path=dir&depth=3` | GET | Get directory tree structure |
| `/sessions/{sessionId}/directory-size/*` | GET | Calculate directory size |

### Code Intelligence

Analyze code projects for structure, dependencies, and context.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/project` | GET | Get project summary |
| `/sessions/{sessionId}/project/context?maxFiles=10` | GET | Extract code context for LLMs |
| `/sessions/{sessionId}/project/structure?depth=3` | GET | Get file structure as JSON |
| `/sessions/{sessionId}/project/batch-create` | POST | Create multiple files at once |

### Diff and Patch

Compare files and apply changes.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/diff` | POST | Generate diff between files or content |
| `/sessions/{sessionId}/patch` | POST | Apply patch to file or content |

## Usage Examples

### Basic Workflow

```bash
# 1. Create a session
curl -X POST http://localhost:8080/sessions

# Response
# {
#   "id": "f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e",
#   "createdAt": "2023-06-15T10:30:45Z",
#   "lastActive": "2023-06-15T10:30:45Z",
#   "workingDir": "",
#   "isActive": true,
#   "expiresAt": "2023-06-16T10:30:45Z"
# }

# 2. Set working directory for the session
curl -X PUT http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/cwd \
  -H "Content-Type: application/json" \
  -d '{"workingDirectory": "/path/to/project"}'

# 3. List files in a directory
curl -X GET "http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/files?path=src"

# 4. Read a specific file
curl -X GET http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/files/src/main.go
```

### Code Analysis for LLMs

```bash
# Get project context with file contents and dependencies
curl -X GET "http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/project/context?maxFiles=5"

# Response will include key files with content, dependencies, and structure:
# {
#   "projectName": "myproject",
#   "mainFiles": {
#     "main.go": {
#       "content": "package main\n\nfunc main() {...}",
#       "dependencies": ["fmt"],
#       "size": 120,
#       "language": "Go"
#     }
#   },
#   "projectDependencies": ["github.com/example/pkg v1.2.3"],
#   "fileStructure": {...}
# }
```

### Making Code Changes

```bash
# Create multiple files in one request
curl -X POST http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/project/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "files": {
      "src/main.go": "package main\n\nfunc main() {\n\tprintln(\"Hello, World!\")\n}",
      "README.md": "# My Project\n\nThis is a sample project.",
      "config.json": "{\n\t\"version\": \"1.0.0\"\n}"
    }
  }'

# Generate a diff between original and modified content
curl -X POST http://localhost:8080/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/diff \
  -H "Content-Type: application/json" \
  -d '{
    "original": "func Process() {\n\treturn nil\n}",
    "modified": "func Process() error {\n\treturn nil\n}"
  }'
```

## LLM Integration

fileAPI is specifically designed to help Language Models understand and modify code:

1. **Context Extraction**: Retrieve essential code context with dependencies
2. **Multiple File Handling**: Process many files in a single request
3. **Metadata Analysis**: Understand project structure without loading all files
4. **Language-Aware**: Extract dependencies across numerous programming languages
5. **Efficient Updates**: Make changes to files or generate diffs for human review

## Development

### Project Structure

# terminalAPI - Remote Command Execution API

A comprehensive API service that enables remote command execution, interactive shell sessions, and process management through a RESTful interface. terminalAPI is designed to work alongside fileAPI to provide a complete development environment for AI assistants and remote development workflows.

## Key Features

- **Session Management**: Create isolated terminal sessions with environment variables and working directories
- **Command Execution**: Run shell commands with input/output capture and custom environments
- **Process Management**: Start long-running processes, interact with stdin/stdout, and monitor status
- **Environment Control**: Set, get, and manage environment variables for each session
- **Command History**: Track and search command history for each session
- **Signal Handling**: Send signals (SIGTERM, SIGKILL, etc.) to running processes
- **Batch Execution**: Run multiple commands with conditional execution logic

## Getting Started

### Prerequisites
- Go 1.16 or later
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/terminalAPI.git
cd terminalAPI
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
./terminalAPI
```

The server will start on port 8081 by default.

## API Reference

### Session Management

Sessions are the foundation of all operations. Create a session first, set a working directory, then execute commands.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions` | POST | Create a new terminal session |
| `/sessions` | GET | List all active sessions |
| `/sessions/{sessionId}` | GET | Get details for a specific session |
| `/sessions/{sessionId}` | DELETE | Delete a session and kill all its processes |
| `/sessions/{sessionId}/cwd` | PUT | Set working directory for a session |

### Command Execution

Execute commands within a session context.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/commands` | POST | Execute a command and get output |
| `/sessions/{sessionId}/commands/batch` | POST | Execute multiple commands in sequence |

### Process Management

Start and manage long-running processes.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/processes` | POST | Start a new process |
| `/sessions/{sessionId}/processes` | GET | List all running processes |
| `/sessions/{sessionId}/processes/{processId}` | GET | Get process details |
| `/sessions/{sessionId}/processes/{processId}/output` | GET | Get process stdout/stderr |
| `/sessions/{sessionId}/processes/{processId}/input` | POST | Send input to process stdin |
| `/sessions/{sessionId}/processes/{processId}/signal` | POST | Send a signal to a process |

### Environment Variables

Manage environment variables for a session.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/env` | GET | Get all environment variables |
| `/sessions/{sessionId}/env` | PUT | Set multiple environment variables |
| `/sessions/{sessionId}/env/{key}` | PUT | Set a specific environment variable |
| `/sessions/{sessionId}/env/{key}` | DELETE | Unset an environment variable |

### Command History

Track and search command history.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{sessionId}/history` | GET | Get command history |
| `/sessions/{sessionId}/history/search` | GET | Search command history |
| `/sessions/{sessionId}/history` | DELETE | Clear command history |

### System Information

Get information about the server environment.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/system/info` | GET | Get system information |
| `/system/shells` | GET | Get available shells |

## Usage Examples

### Basic Workflow

```bash
# 1. Create a session
curl -X POST http://localhost:8081/sessions

# Response
# {
#   "id": "f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e",
#   "createdAt": "2023-06-15T10:30:45Z",
#   "lastActive": "2023-06-15T10:30:45Z",
#   "workingDir": "",
#   "isActive": true,
#   "expiresAt": "2023-06-16T10:30:45Z",
#   "envVars": {"SHELL": "/bin/bash"}
# }

# 2. Set working directory
curl -X PUT http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/cwd \
  -H "Content-Type: application/json" \
  -d '{"workingDirectory": "/path/to/project"}'

# 3. Execute a command
curl -X POST http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ls -la",
    "timeout": 10
  }'
```

### Running Interactive Processes

```bash
# 1. Start a long-running process
curl -X POST http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/processes \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python3 -i",
    "timeout": 300
  }'

# Response
# {
#   "id": "b5d0c2a1-7b5d-4b1a-8f0e-3e9b6a7c8d9e",
#   "command": "python3 -i",
#   "startTime": "2023-06-15T10:35:45Z",
#   "isRunning": true,
#   "pid": 12345
# }

# 2. Send input to the process
curl -X POST http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/processes/b5d0c2a1-7b5d-4b1a-8f0e-3e9b6a7c8d9e/input \
  -H "Content-Type: application/json" \
  -d '{
    "input": "print('Hello, world!')"
  }'

# 3. Get process output
curl -X GET http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/processes/b5d0c2a1-7b5d-4b1a-8f0e-3e9b6a7c8d9e/output
```

### Managing Environment Variables

```bash
# Set environment variables
curl -X PUT http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/env \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "NODE_ENV": "development",
      "DEBUG": "app:*"
    }
  }'

# Execute a command with custom environment
curl -X POST http://localhost:8081/sessions/f7e0c9a2-7b5d-4b1a-8f0e-3e9b6a7c8d9e/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo $NODE_ENV $DEBUG",
    "environment": {
      "CUSTOM_VAR": "custom-value"
    }
  }'
```

## Integration with fileAPI

terminalAPI is designed to work seamlessly with fileAPI:

1. Use fileAPI to browse, edit, and manage files
2. Use terminalAPI to execute commands against those files
3. Combine both APIs to provide a complete development environment

For example, you could:
1. Create a session in both APIs with the same working directory
2. Edit a file using fileAPI
3. Run a build command using terminalAPI
4. Examine the results using fileAPI

## Development

### Project Structure


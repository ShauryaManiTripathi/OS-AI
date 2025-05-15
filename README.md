# file and Terminal API

![License](https://img.shields.io/badge/license-MIT-blue.svg)

A powerful backend toolkit providing seamless file system and terminal access through RESTful APIs. Designed specifically for LLMs and AI tools to easily interact with file systems and execute commands in a controlled environment.

## 🔑 Key Features

### File API
- **Session-based management**: Isolated working contexts with state tracking
- **Complete file operations**: Create, read, update, delete files with metadata support
- **Directory management**: Create, list, navigate directory structures
- **Batch operations**: Process multiple files at once for efficiency
- **Diff and patch**: Compare files and apply changes with precision
- **Project analysis**: Extract code context, dependencies, and structure

### Terminal API
- **Command execution**: Run terminal commands securely
- **Session persistence**: Maintain terminal state between commands
- **Output streaming**: Real-time command output
- **Environment variable management**: Set and manage environment variables
- **Working directory control**: Execute commands in specific directories

## 🤖 AI Agent Capabilities

This API is specifically designed to enable AI agents with full access to your PC for seamless autonomous tasking:

- **Full System Access**: AI agents can navigate, read, and modify any accessible part of the file system
- **Tool Creation**: Agents can write, compile, and execute their own tools to solve complex tasks
- **Autonomous Workflows**: Complete end-to-end task handling without human intervention
- **Self-improvement**: Agents can analyze their own performance and modify their approaches
- **Custom Integration**: Build specialized AI assistants for development, system administration, or data processing

By providing comprehensive file system and terminal access, AI agents can perform virtually any computational task, creating a truly autonomous digital assistant that can handle complex workflows by developing and executing its own solutions.

## 📋 Prerequisites

- Go 1.18 or higher
- Unix-like environment (Linux, macOS) or WSL for Windows users

## 🚀 Getting Started

### Installation

1. Clone this repository:
```bash
git clone https://github.com/ShauryaManiTripathi/OS-AI
cd pocketflow-api
```

2. Install dependencies:
```bash
go mod download
```

3. Build the application:
```bash
go build -o XYZ-api ./cmd
```

4. Run the server:
```bash
./XYZ-api
```

## 🔧 Usage

### File API Examples

Create a session:
```bash
curl -X POST http://localhost:8080/sessions
```

Set working directory:
```bash
curl -X PUT http://localhost:8080/sessions/SESSION_ID/cwd \
  -H "Content-Type: application/json" \
  -d '{"workingDirectory": "/path/to/project"}'
```

Read a file:
```bash
curl -X GET http://localhost:8080/sessions/SESSION_ID/files/src/main.go
```

Create a file:
```bash
curl -X POST http://localhost:8080/sessions/SESSION_ID/files/src/hello.go \
  -H "Content-Type: application/json" \
  -d '{"content": "package main\n\nfunc main() {\n\tprintln(\"Hello, World!\")\n}"}'
```

### Terminal API Examples

Execute a command:
```bash
curl -X POST http://localhost:8081/terminal/SESSION_ID/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'
```

Set environment variable:
```bash
curl -X PUT http://localhost:8081/terminal/SESSION_ID/env \
  -H "Content-Type: application/json" \
  -d '{"name": "DEBUG", "value": "true"}'
```

## 📘 API Documentation

### File API

Core concepts:
- **Sessions**: All operations happen within a session context
- **Working Directory**: Each session has a working directory that serves as the root for relative paths
- **File and Directory Operations**: Create/read/update/delete files and directories
- **Diff and Patch**: Compare files and apply changes
- **Project Analysis**: Extract code context, dependencies, and structure

API categories:
- Session Management
- File Operations
- Directory Operations
- Diff and Patch
- Project Operations

### Terminal API

Core concepts:
- **Command Execution**: Run commands securely within sessions
- **Output Handling**: Capture and stream command output
- **Environment Management**: Set variables for command execution
- **Working Directory**: Set directory context for commands

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

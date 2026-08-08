# TaskFlow

A powerful Python CLI tool for ticket/issue tracking with real-time collaboration.

## Features

- **Ticket Management**: Create, update, and track tickets with labels, priority, and assignees
- **Real-time Collaboration**: WebSocket-based live updates across team members
- **Notification Engine**: Smart notifications for ticket changes and assignments
- **Persistent Storage**: SQLite-backed data persistence

## Installation

    pip install -e .

## Usage

    taskflow init          # Initialize a new project
    taskflow tickets list  # List all tickets
    taskflow tickets create --title "Bug fix" --priority high
    taskflow ws start      # Start WebSocket server

## Development

    pip install -e ".[dev]"
    pytest tests/

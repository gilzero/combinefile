# CombineCode

A modern web application for intelligent file concatenation, built with FastAPI. CombineCode helps you combine multiple files while respecting `.gitignore` rules and custom ignore patterns.

## Features

- 🔍 Smart file concatenation with `.gitignore` support
- 🎯 Custom file ignore patterns with glob syntax
- 🎨 Clean web interface
- ⚡ Asynchronous file processing
- 📝 Detailed logging with emoji indicators
- 🔒 Secure file handling with error protection

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/combinecode.git
   cd combinecode
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to `http://localhost:8000`

3. Use the web interface to:
   - Specify the target directory
   - Add custom ignore patterns (optional)
   - Process and combine files
   - Download the resulting file

## Project Structure

```
combinecode/
├── main.py           # FastAPI application and core logic
├── requirements.txt  # Python dependencies
├── static/          # Static assets
├── templates/       # HTML templates
├── output/         # Generated files
└── test_main.http  # API test file
```

## Dependencies

- FastAPI (>=0.68.0) - Web framework
- Uvicorn (>=0.15.0) - ASGI server
- Python-multipart (>=0.0.5) - Form data handling
- Pathspec (>=0.9.0) - Gitignore pattern matching
- Aiofiles (>=0.8.0) - Async file operations
- Jinja2 (>=3.0.0) - Template engine

## Development

The application uses:
- FastAPI for the backend API
- Jinja2 templates for the frontend
- Async operations for file handling
- Custom emoji-based logging for better debugging

## License

This project is open source and available under the MIT License.

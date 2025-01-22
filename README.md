# File Concatenator

A FastAPI-based application that concatenates files while respecting `.gitignore` rules. This tool traverses directories and combines file contents into a single text file, making it useful for code analysis, backup, or documentation purposes.

## Features

- 📁 Recursive directory traversal
- 🚫 Respects `.gitignore` rules
- ⚡ Asynchronous file operations
- 🔗 Handles symbolic links
- 🛡️ Comprehensive error handling
- 📝 Clear file separation in output

## Requirements

- Python 3.7+
- FastAPI
- uvicorn
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
uvicorn main:app --reload
```

2. The server will start at `http://localhost:8000`

3. Access the API:
   - Interactive API documentation: `http://localhost:8000/docs`
   - Alternative API documentation: `http://localhost:8000/redoc`

### API Endpoints

#### POST /concatenate
Concatenates all files in the specified directory (and subdirectories), respecting `.gitignore` rules.

- **Parameters**:
  - `directory` (optional): Target directory path (defaults to current directory)
- **Returns**: Text file containing concatenated contents

Example using curl:
```bash
curl -X POST "http://localhost:8000/concatenate" -H "accept: text/plain" > concatenated_files.txt
```

## Output Format

The concatenated output file includes clear separators between files:
```
================================================================================
File: path/to/file1.txt
================================================================================
[Contents of file1.txt]

================================================================================
File: path/to/file2.py
================================================================================
[Contents of file2.py]
```

## Error Handling

The application includes comprehensive error handling for:
- File access issues
- Invalid directories
- Malformed `.gitignore` files
- Encoding issues

## License

MIT License

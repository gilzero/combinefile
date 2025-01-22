# File Concatenator

A powerful web application that combines multiple files into a single document while providing comprehensive codebase statistics.

## Features

### Core Functionality
- 📁 Concatenate files from any directory
- 🔍 Respect `.gitignore` rules and custom ignore patterns
- ⚡ Asynchronous file processing for better performance
- 📊 Comprehensive codebase statistics

### Statistics & Analysis
- **File Analysis**
  - Total files processed and skipped
  - File type distribution
  - Total size and line counts
  - Average lines per file

- **Code Analysis**
  - Lines of code (excluding comments and empty lines)
  - Comment line count
  - Empty line count
  - Code-to-comment ratio

- **Directory Analysis**
  - Total directories
  - Directory depth
  - Empty directories
  - Directory with most files

- **Filter Statistics**
  - Files filtered by .gitignore
  - Files filtered by custom rules
  - Most effective filter patterns

### User Interface
- 🎨 Modern, responsive Bootstrap-based dashboard
- 📈 Real-time processing status
- 🎉 Interactive success animations
- 📥 Easy file download
- 🎯 Custom ignore pattern management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gilzero/combinefile.git
cd combinefile
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python main.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Enter the directory path you want to process (or leave empty for current directory)

4. (Optional) Add custom ignore patterns

5. Click "Process Files" and wait for the results

6. Download the concatenated file and view the statistics

## Configuration

- Custom ignore patterns support glob syntax (e.g., `*.txt`, `src/**`)
- The application automatically respects existing `.gitignore` rules
- Output files are saved in the `output` directory with timestamps

## Technical Details

### Architecture
- FastAPI backend for high performance
- Async file processing for better scalability
- Pydantic models for data validation
- Bootstrap 5 frontend with modern UI components

### File Processing
- Handles various file types
- Smart comment detection
- Efficient line counting
- Proper error handling

### Statistics Engine
- Real-time stat calculation
- Accurate file type detection
- Directory tree analysis
- Pattern effectiveness tracking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI and Bootstrap
- Uses pathspec for .gitignore parsing
- Confetti effects powered by canvas-confetti

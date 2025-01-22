# File Concatenator v3

A powerful web application that combines multiple files into a single document while providing comprehensive codebase statistics and visualization.

## New in Version 3
- 🌳 Enhanced directory tree visualization with file sizes
- 🎨 Dark/Light theme support with system preference detection
- 📊 Improved statistics dashboard with modern UI
- 📷 Export statistics as Image or PDF
- ♿ Better accessibility support
- 🎯 Improved ignore pattern management

## Features

### Core Functionality
- 📁 Concatenate files from any directory
- 🔍 Respect `.gitignore` rules and custom ignore patterns
- ⚡ Asynchronous file processing for better performance
- 📊 Comprehensive codebase statistics

### Statistics & Visualization
- **Interactive Directory Tree**
  - Visual directory structure
  - File size information
  - Color-coded files and directories
  - Hover effects for better UX

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
  - Total directories and depth
  - Empty directories detection
  - Directory with most files
  - Complete directory tree

### Modern UI/UX
- 🎨 Dark/Light theme with system preference sync
- 📱 Fully responsive design
- 🖼️ Export statistics as Image/PDF
- ♿ ARIA labels and keyboard navigation
- 🎯 Enhanced ignore pattern management
- 🎉 Interactive success animations

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

4. (Optional) Add custom ignore patterns using the "Add Pattern" button

5. Click "Process Files" and wait for the results

6. View the statistics, export as Image/PDF, or download the concatenated file

## Known Issues
- 🐛 Processing spinner animation may not work in some browsers
- 🐛 Very long file paths might overflow in the directory tree view
- 🐛 PDF export might fail with very large directory structures
- ⚠️ Memory usage can be high with extremely large codebases

## Technical Details

### Architecture
- FastAPI backend for high performance
- Async file processing for better scalability
- Pydantic models for data validation
- Bootstrap 5 frontend with modern UI components

### Frontend Features
- Theme detection and persistence
- Canvas-based PDF/Image export
- Responsive grid layout
- Accessible UI components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI and Bootstrap 5
- Uses pathspec for .gitignore parsing
- PDF export powered by jsPDF
- Image export using html2canvas
- Confetti effects by canvas-confetti

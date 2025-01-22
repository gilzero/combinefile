from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import pathlib
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import tempfile
import logging
from typing import List, Optional
import aiofiles
from datetime import datetime
import sys
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis to log messages based on level."""
    
    EMOJI_LEVELS = {
        logging.DEBUG: "🔍",    # Magnifying glass for detailed inspection
        logging.INFO: "ℹ️ ",     # Information
        logging.WARNING: "⚠️ ",  # Warning sign
        logging.ERROR: "❌",    # Cross mark for errors
        logging.CRITICAL: "🚨"  # Emergency light for critical issues
    }
    
    EMOJI_KEYWORDS = {
        "Starting": "🚀",      # Rocket for start
        "Complete": "✅",      # Check mark for completion
        "Found": "🔎",        # Magnifying glass for finding
        "Processing": "⚙️ ",   # Gear for processing
        "Skipping": "⏭️ ",     # Skip forward for skipped items
        "Filtered": "🔍",     # Magnifying glass for filtering
        "Ignoring": "🚫",     # Prohibited for ignored items
        "Error": "❌",        # Cross mark for errors
        "Cleaning": "🧹",     # Broom for cleanup
        "Directory": "📁",    # Folder for directory operations
        "File": "📄",         # Page for file operations
        "Loading": "📥",      # Inbox for loading
        "Saving": "📥",       # Outbox for saving
        "Success": "🎉",      # Party popper for success
        "Failed": "💥",       # Collision for failure
        "Initialize": "🎬",   # Clapper board for initialization
    }

    def format(self, record):
        # Add level emoji
        level_emoji = self.EMOJI_LEVELS.get(record.levelno, "")
        
        # Add keyword emoji
        keyword_emoji = ""
        message = str(record.msg)
        for keyword, emoji in self.EMOJI_KEYWORDS.items():
            if keyword.lower() in message.lower():
                keyword_emoji = emoji
                break
        
        # Combine emojis with the original format
        record.msg = f"{level_emoji} {keyword_emoji} {record.msg}"
        return super().format(record)

# Configure logging with emoji formatter
formatter = EmojiFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler with emojis
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# File handler with emojis
log_file = os.path.join(os.path.dirname(__file__), 'output', 'app.log')
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
logger = logging.getLogger(__name__)

class ConcatenateRequest(BaseModel):
    directory: str = "."
    additional_ignores: List[str] = []

app = FastAPI(title="File Concatenator", description="Concatenates files respecting .gitignore rules")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FileConcatenationError(Exception):
    """Custom exception for file concatenation errors."""
    pass

class FileConcatenator:
    def __init__(self, base_dir: str = ".", additional_ignores: List[str] = None):
        try:
            logger.info(f"Initializing concatenator for directory: {base_dir}")
            self.base_dir = pathlib.Path(base_dir).resolve()
            if not self.base_dir.exists():
                raise FileConcatenationError(f"Directory does not exist: {base_dir}")
            
            self.additional_ignores = additional_ignores or []
            logger.info(f"Additional ignore patterns: {self.additional_ignores}")
            
            # Initialize statistics
            self.stats = {
                'file_stats': {
                    'total_files': 0,
                    'processed_files': 0,
                    'skipped_files': 0,
                    'file_types': {},
                    'largest_file': {'path': None, 'size': 0},
                    'total_size': 0,
                    'total_lines': 0,
                    'empty_lines': 0,
                    'comment_lines': 0
                },
                'dir_stats': {
                    'total_dirs': 0,
                    'max_depth': 0,
                    'dirs_with_most_files': {'path': None, 'count': 0},
                    'empty_dirs': 0
                },
                'filter_stats': {
                    'gitignore_filtered': 0,
                    'custom_filtered': 0,
                    'pattern_matches': {}  # Pattern -> count of files filtered
                }
            }
            
            # Load gitignore patterns and combine with additional ignores
            self.gitignore_patterns = self._load_gitignore()
            all_patterns = self.gitignore_patterns + self.additional_ignores
            self.gitignore_spec = PathSpec.from_lines(GitWildMatchPattern, all_patterns)
            
            # Create output directory if it doesn't exist
            self.output_dir = pathlib.Path(__file__).parent / "output"
            self.output_dir.mkdir(exist_ok=True)
            logger.info(f"Output directory ready at: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise FileConcatenationError(f"Initialization error: {str(e)}")

    def _load_gitignore(self) -> List[str]:
        """Load .gitignore patterns if the file exists."""
        gitignore_path = self.base_dir / ".gitignore"
        patterns = []
        try:
            logger.info(f"Loading gitignore from: {gitignore_path}")
            if gitignore_path.exists():
                with open(gitignore_path, "r") as f:
                    patterns = [line.strip() for line in f if line.strip() 
                              and not line.startswith("#")]
                logger.info(f"Successfully loaded {len(patterns)} gitignore patterns")
            else:
                logger.warning("No gitignore file found")
        except Exception as e:
            logger.error(f"Failed to read gitignore: {e}")
            logger.warning("Proceeding with empty gitignore patterns")
        
        return patterns

    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is a comment based on common comment markers."""
        comment_markers = ['#', '//', '/*', '*', '<!--', '-->', '"""', "'''"]
        stripped = line.strip()
        return any(stripped.startswith(marker) for marker in comment_markers)

    def _update_file_stats(self, file_path: pathlib.Path, content: str):
        """Update file statistics for a processed file."""
        # Update file type stats
        file_type = file_path.suffix or 'no_extension'
        self.stats['file_stats']['file_types'][file_type] = \
            self.stats['file_stats']['file_types'].get(file_type, 0) + 1

        # Update size stats
        file_size = file_path.stat().st_size
        self.stats['file_stats']['total_size'] += file_size
        if file_size > self.stats['file_stats']['largest_file']['size']:
            self.stats['file_stats']['largest_file'] = {
                'path': str(file_path.relative_to(self.base_dir)),
                'size': file_size
            }

        # Update line stats
        lines = content.splitlines()
        self.stats['file_stats']['total_lines'] += len(lines)
        self.stats['file_stats']['empty_lines'] += sum(1 for line in lines if not line.strip())
        self.stats['file_stats']['comment_lines'] += sum(1 for line in lines if self._is_comment_line(line))

    def _update_dir_stats(self, current_path: pathlib.Path, files_count: int):
        """Update directory statistics."""
        self.stats['dir_stats']['total_dirs'] += 1
        
        # Update depth stats
        relative_path = current_path.relative_to(self.base_dir)
        depth = len(relative_path.parts)
        self.stats['dir_stats']['max_depth'] = max(self.stats['dir_stats']['max_depth'], depth)
        
        # Update directory with most files
        if files_count > self.stats['dir_stats']['dirs_with_most_files']['count']:
            self.stats['dir_stats']['dirs_with_most_files'] = {
                'path': str(relative_path),
                'count': files_count
            }
        
        # Update empty directory count
        if files_count == 0:
            self.stats['dir_stats']['empty_dirs'] += 1

    def _update_filter_stats(self, file_path: pathlib.Path, is_gitignore: bool):
        """Update filter statistics when a file is ignored."""
        rel_path = str(file_path.relative_to(self.base_dir))
        
        if is_gitignore:
            self.stats['filter_stats']['gitignore_filtered'] += 1
            # Check which gitignore pattern matched
            for pattern in self.gitignore_patterns:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self.stats['filter_stats']['pattern_matches'][pattern] = \
                        self.stats['filter_stats']['pattern_matches'].get(pattern, 0) + 1
        else:
            self.stats['filter_stats']['custom_filtered'] += 1
            # Check which custom pattern matched
            for pattern in self.additional_ignores:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self.stats['filter_stats']['pattern_matches'][pattern] = \
                        self.stats['filter_stats']['pattern_matches'].get(pattern, 0) + 1

    def _is_ignored(self, path: pathlib.Path) -> bool:
        """Check if path should be ignored based on .gitignore rules."""
        try:
            rel_path = str(path.relative_to(self.base_dir))
            
            # Check gitignore patterns first
            for pattern in self.gitignore_patterns:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self._update_filter_stats(path, True)
                    return True
            
            # Then check additional patterns
            for pattern in self.additional_ignores:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self._update_filter_stats(path, False)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to check ignore status: {path}, {str(e)}")
            return False

    async def concatenate_files(self) -> str:
        """Concatenate all files in directory respecting .gitignore rules."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"output_{timestamp}.txt"
        
        logger.info(f"Starting file concatenation to: {output_file}")
        
        try:
            async with aiofiles.open(output_file, mode="w") as outfile:
                files = self._walk_directory()
                self.stats['file_stats']['total_files'] = len(files)
                logger.info(f"Found {len(files)} files to process")
                
                for file_path in files:
                    try:
                        if file_path.is_file() and not file_path.is_symlink():
                            rel_path = file_path.relative_to(self.base_dir)
                            logger.debug(f"Processing file: {rel_path}")
                            
                            await outfile.write(f"\n{'='*80}\n")
                            await outfile.write(f"File: {rel_path}\n")
                            await outfile.write(f"{'='*80}\n")
                            
                            async with aiofiles.open(file_path, "r", errors="replace") as infile:
                                content = await infile.read()
                                await outfile.write(content)
                                await outfile.write("\n")
                                
                                # Update statistics
                                self._update_file_stats(file_path, content)
                                self.stats['file_stats']['processed_files'] += 1
                            
                            logger.debug(f"Successfully processed: {rel_path}")
                        else:
                            logger.debug(f"Skipping non-regular file: {file_path}")
                            self.stats['file_stats']['skipped_files'] += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to process file {file_path}: {e}")
                        self.stats['file_stats']['skipped_files'] += 1
            
            # Calculate averages
            if self.stats['file_stats']['processed_files'] > 0:
                self.stats['file_stats']['avg_file_size'] = \
                    self.stats['file_stats']['total_size'] / self.stats['file_stats']['processed_files']
                self.stats['file_stats']['avg_lines_per_file'] = \
                    self.stats['file_stats']['total_lines'] / self.stats['file_stats']['processed_files']
            
            logger.info(f"Concatenation complete! Processed: {self.stats['file_stats']['processed_files']}, "
                       f"Skipped: {self.stats['file_stats']['skipped_files']}, "
                       f"Total: {self.stats['file_stats']['total_files']}")
            return str(output_file)
            
        except Exception as e:
            error_msg = f"Concatenation failed: {str(e)}"
            logger.error(error_msg)
            if output_file.exists():
                logger.info(f"Cleaning up failed output: {output_file}")
                output_file.unlink()
            raise FileConcatenationError(error_msg)

    def _walk_directory(self) -> List[pathlib.Path]:
        """Walk directory tree respecting .gitignore rules."""
        files = []
        try:
            logger.info(f"Starting directory scan from: {self.base_dir}")
            for root, dirs, filenames in os.walk(self.base_dir):
                root_path = pathlib.Path(root)
                
                # Update directory statistics
                self._update_dir_stats(root_path, len(filenames))
                
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
                
                # Filter and collect non-ignored files
                for filename in filenames:
                    file_path = root_path / filename
                    if not self._is_ignored(file_path):
                        files.append(file_path)
                    else:
                        logger.debug(f"Ignoring file: {file_path}")
                        
            logger.info(f"Directory scan complete! Found {len(files)} files")
            return sorted(files)
            
        except Exception as e:
            error_msg = f"Directory scan failed: {str(e)}"
            logger.error(error_msg)
            raise FileConcatenationError(error_msg)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the home page."""
    logger.info("Serving home page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/concatenate")
async def concatenate_files(request: ConcatenateRequest):
    """
    Concatenate all files in the specified directory and its subdirectories,
    respecting .gitignore rules and additional ignore patterns.
    """
    logger.info(f"Received concatenation request for: {request.directory}")
    logger.info(f"Additional ignore patterns: {request.additional_ignores}")
    
    try:
        if not request.directory or request.directory.isspace():
            request.directory = "."
            
        concatenator = FileConcatenator(
            request.directory, 
            additional_ignores=request.additional_ignores
        )
        output_file = await concatenator.concatenate_files()
        filename = os.path.basename(output_file)
        logger.info(f"Successfully created: {filename}")
        
        # Format statistics for response
        stats = {
            'file_stats': {
                'total': concatenator.stats['file_stats']['total_files'],
                'processed': concatenator.stats['file_stats']['processed_files'],
                'skipped': concatenator.stats['file_stats']['skipped_files'],
                'by_type': concatenator.stats['file_stats']['file_types'],
                'largest_file': concatenator.stats['file_stats']['largest_file'],
                'total_size': concatenator.stats['file_stats']['total_size'],
                'avg_size': concatenator.stats['file_stats'].get('avg_file_size', 0),
                'lines': {
                    'total': concatenator.stats['file_stats']['total_lines'],
                    'code': (concatenator.stats['file_stats']['total_lines'] - 
                            concatenator.stats['file_stats']['empty_lines'] - 
                            concatenator.stats['file_stats']['comment_lines']),
                    'comments': concatenator.stats['file_stats']['comment_lines'],
                    'empty': concatenator.stats['file_stats']['empty_lines'],
                    'avg_per_file': concatenator.stats['file_stats'].get('avg_lines_per_file', 0)
                }
            },
            'directory_stats': {
                'total': concatenator.stats['dir_stats']['total_dirs'],
                'empty': concatenator.stats['dir_stats']['empty_dirs'],
                'max_depth': concatenator.stats['dir_stats']['max_depth'],
                'most_files': concatenator.stats['dir_stats']['dirs_with_most_files']
            },
            'filter_stats': {
                'gitignore_filtered': concatenator.stats['filter_stats']['gitignore_filtered'],
                'custom_filtered': concatenator.stats['filter_stats']['custom_filtered'],
                'most_effective_patterns': sorted(
                    [{'pattern': k, 'files_filtered': v} 
                     for k, v in concatenator.stats['filter_stats']['pattern_matches'].items()],
                    key=lambda x: x['files_filtered'],
                    reverse=True
                )[:5]  # Top 5 most effective patterns
            }
        }
        
        headers = {
            'X-File-Stats': json.dumps(stats)
        }
        
        return FileResponse(
            output_file,
            media_type="text/plain",
            filename=filename,
            headers=headers
        )
    except FileConcatenationError as e:
        error_msg = f"Concatenation request failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error in request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/hello/{name}")
async def say_hello(name: str):
    logger.info(f"Greeting user: {name}")
    return {"message": f"Hello {name}"}

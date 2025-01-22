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
    def __init__(self, base_dir: str = "."):
        try:
            logger.info(f"Initializing concatenator for directory: {base_dir}")
            self.base_dir = pathlib.Path(base_dir).resolve()
            if not self.base_dir.exists():
                raise FileConcatenationError(f"Directory does not exist: {base_dir}")
            
            self.gitignore_spec = self._load_gitignore()
            
            # Create output directory if it doesn't exist
            self.output_dir = pathlib.Path(__file__).parent / "output"
            self.output_dir.mkdir(exist_ok=True)
            logger.info(f"Output directory ready at: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise FileConcatenationError(f"Initialization error: {str(e)}")

    def _load_gitignore(self) -> PathSpec:
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
        
        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    async def concatenate_files(self) -> str:
        """Concatenate all files in directory respecting .gitignore rules."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"output_{timestamp}.txt"
        
        logger.info(f"Starting file concatenation to: {output_file}")
        total_files = 0
        processed_files = 0
        skipped_files = 0
        
        try:
            async with aiofiles.open(output_file, mode="w") as outfile:
                files = self._walk_directory()
                total_files = len(files)
                logger.info(f"Found {total_files} files to process")
                
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
                            processed_files += 1
                            logger.debug(f"Successfully processed: {rel_path}")
                            
                        else:
                            logger.debug(f"Skipping non-regular file: {file_path}")
                            skipped_files += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to process file {file_path}: {e}")
                        skipped_files += 1
            
            logger.info(f"Concatenation complete! Processed: {processed_files}, "
                       f"Skipped: {skipped_files}, Total: {total_files}")
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
                
                # Filter out ignored directories
                original_dir_count = len(dirs)
                dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
                filtered_dir_count = len(dirs)
                if original_dir_count != filtered_dir_count:
                    logger.debug(f"Filtered {original_dir_count - filtered_dir_count} "
                               f"directories in {root_path}")
                
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

    def _is_ignored(self, path: pathlib.Path) -> bool:
        """Check if path should be ignored based on .gitignore rules."""
        try:
            rel_path = str(path.relative_to(self.base_dir))
            is_ignored = self.gitignore_spec.match_file(rel_path)
            if is_ignored:
                logger.debug(f"Ignoring path: {rel_path}")
            return is_ignored
        except Exception as e:
            logger.error(f"Failed to check ignore status: {path}, {str(e)}")
            return False

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the home page."""
    logger.info("Serving home page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/concatenate")
async def concatenate_files(directory: str = "."):
    """
    Concatenate all files in the specified directory and its subdirectories,
    respecting .gitignore rules.
    """
    logger.info(f"Received concatenation request for: {directory}")
    try:
        if not directory or directory.isspace():
            directory = "."
            
        concatenator = FileConcatenator(directory)
        output_file = await concatenator.concatenate_files()
        filename = os.path.basename(output_file)
        logger.info(f"Successfully created: {filename}")
        return FileResponse(
            output_file,
            media_type="text/plain",
            filename=filename
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

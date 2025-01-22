from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import pathlib
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import tempfile
import logging
from typing import List, Optional
import aiofiles

app = FastAPI(title="File Concatenator", description="Concatenates files respecting .gitignore rules")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileConcatenator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = pathlib.Path(base_dir).resolve()
        self.gitignore_spec = self._load_gitignore()

    def _load_gitignore(self) -> PathSpec:
        """Load .gitignore patterns if the file exists."""
        gitignore_path = self.base_dir / ".gitignore"
        patterns = []
        try:
            if gitignore_path.exists():
                with open(gitignore_path, "r") as f:
                    patterns = [line.strip() for line in f if line.strip() 
                              and not line.startswith("#")]
        except Exception as e:
            logger.warning(f"Error reading .gitignore: {e}")
        
        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    async def concatenate_files(self) -> str:
        """Concatenate all files in directory respecting .gitignore rules."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt")
        try:
            async with aiofiles.open(temp_file.name, mode="w") as outfile:
                for file_path in self._walk_directory():
                    try:
                        if file_path.is_file() and not file_path.is_symlink():
                            rel_path = file_path.relative_to(self.base_dir)
                            await outfile.write(f"\n{'='*80}\n")
                            await outfile.write(f"File: {rel_path}\n")
                            await outfile.write(f"{'='*80}\n")
                            
                            async with aiofiles.open(file_path, "r", errors="replace") as infile:
                                content = await infile.read()
                                await outfile.write(content)
                                await outfile.write("\n")
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
            
            return temp_file.name
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise HTTPException(status_code=500, detail=str(e))

    def _walk_directory(self) -> List[pathlib.Path]:
        """Walk directory tree respecting .gitignore rules."""
        files = []
        try:
            for root, dirs, filenames in os.walk(self.base_dir):
                root_path = pathlib.Path(root)
                
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
                
                # Filter and collect non-ignored files
                for filename in filenames:
                    file_path = root_path / filename
                    if not self._is_ignored(file_path):
                        files.append(file_path)
        except Exception as e:
            logger.error(f"Error walking directory: {e}")
        
        return sorted(files)

    def _is_ignored(self, path: pathlib.Path) -> bool:
        """Check if path should be ignored based on .gitignore rules."""
        try:
            rel_path = str(path.relative_to(self.base_dir))
            return self.gitignore_spec.match_file(rel_path)
        except Exception:
            return False

@app.post("/concatenate")
async def concatenate_files(directory: Optional[str] = "."):
    """
    Concatenate all files in the specified directory and its subdirectories,
    respecting .gitignore rules.
    """
    try:
        concatenator = FileConcatenator(directory)
        output_file = await concatenator.concatenate_files()
        return FileResponse(
            output_file,
            media_type="text/plain",
            filename="concatenated_files.txt",
            background=lambda: os.unlink(output_file)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

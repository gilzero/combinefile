import pathlib
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import logging
import aiofiles
from typing import List
from datetime import datetime

from app.models.schemas import (
    ConcatenationStats,
    FileConcatenationError
)

logger = logging.getLogger(__name__)

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
            self.stats = ConcatenationStats()
            
            # Load gitignore patterns and combine with additional ignores
            self.gitignore_patterns = self._load_gitignore()
            all_patterns = self.gitignore_patterns + self.additional_ignores
            self.gitignore_spec = PathSpec.from_lines(GitWildMatchPattern, all_patterns)
            
            # Create output directory if it doesn't exist
            self.output_dir = pathlib.Path(__file__).parent.parent.parent / "output"
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
        file_type = file_path.suffix.lower() or 'no extension'
        if file_type.startswith('.'):
            file_type = file_type[1:]  # Remove the leading dot
        self.stats.file_stats.file_types[file_type] = \
            self.stats.file_stats.file_types.get(file_type, 0) + 1

        # Update size stats
        file_size = file_path.stat().st_size
        self.stats.file_stats.total_size += file_size
        if file_size > self.stats.file_stats.largest_file["size"]:
            self.stats.file_stats.largest_file = {
                'path': str(file_path.relative_to(self.base_dir)),
                'size': file_size
            }

        # Update line stats
        lines = content.splitlines()
        self.stats.file_stats.total_lines += len(lines)
        self.stats.file_stats.empty_lines += sum(1 for line in lines if not line.strip())
        self.stats.file_stats.comment_lines += sum(1 for line in lines if self._is_comment_line(line))

    def _update_dir_stats(self, current_path: pathlib.Path, files_count: int):
        """Update directory statistics."""
        self.stats.dir_stats.total_dirs += 1
        
        # Update depth stats
        relative_path = current_path.relative_to(self.base_dir)
        depth = len(relative_path.parts)
        self.stats.dir_stats.max_depth = max(self.stats.dir_stats.max_depth, depth)
        
        # Update directory with most files
        if files_count > self.stats.dir_stats.dirs_with_most_files["count"]:
            self.stats.dir_stats.dirs_with_most_files = {
                'path': str(relative_path),
                'count': files_count
            }
        
        # Update empty directory count
        if files_count == 0:
            self.stats.dir_stats.empty_dirs += 1

    def _update_filter_stats(self, file_path: pathlib.Path, is_gitignore: bool):
        """Update filter statistics when a file is ignored."""
        rel_path = str(file_path.relative_to(self.base_dir))
        
        if is_gitignore:
            self.stats.filter_stats.gitignore_filtered += 1
            # Check which gitignore pattern matched
            for pattern in self.gitignore_patterns:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self.stats.filter_stats.pattern_matches[pattern] = \
                        self.stats.filter_stats.pattern_matches.get(pattern, 0) + 1
        else:
            self.stats.filter_stats.custom_filtered += 1
            # Check which custom pattern matched
            for pattern in self.additional_ignores:
                if PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(rel_path):
                    self.stats.filter_stats.pattern_matches[pattern] = \
                        self.stats.filter_stats.pattern_matches.get(pattern, 0) + 1

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
            logger.error(f"Error checking ignore status for {path}: {e}")
            return True

    async def concatenate_files(self) -> str:
        """Concatenate all files in the directory respecting .gitignore rules."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"output_{timestamp}.txt"
            
            files = self._walk_directory()
            self.stats.file_stats.total_files = len(files)
            
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as outfile:
                for file_path in files:
                    try:
                        if self._is_ignored(file_path):
                            self.stats.file_stats.skipped_files += 1
                            continue
                        
                        logger.info(f"Processing file: {file_path}")
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as infile:
                            content = await infile.read()
                            
                            # Write file header
                            await outfile.write(f"\n{'='*80}\n")
                            await outfile.write(f"File: {file_path.relative_to(self.base_dir)}\n")
                            await outfile.write(f"{'='*80}\n\n")
                            
                            # Write file content
                            await outfile.write(content)
                            await outfile.write("\n")
                            
                            self._update_file_stats(file_path, content)
                            self.stats.file_stats.processed_files += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        continue
            
            logger.info(f"Concatenation complete. Output saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Concatenation failed: {e}")
            raise FileConcatenationError(f"Concatenation error: {str(e)}")

    def _walk_directory(self) -> List[pathlib.Path]:
        """Walk through directory and collect all files."""
        files = []
        try:
            for current_path in self.base_dir.rglob("*"):
                if current_path.is_file():
                    files.append(current_path)
                elif current_path.is_dir():
                    # Count files in this directory for stats
                    dir_files = list(current_path.glob("*"))
                    self._update_dir_stats(current_path, len([f for f in dir_files if f.is_file()]))
            
            return sorted(files)
        except Exception as e:
            logger.error(f"Error walking directory: {e}")
            return [] 
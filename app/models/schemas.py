from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Any, Type
import pathlib

class ConcatenateRequest(BaseModel):
    """Request model for file concatenation."""
    directory: str = "."
    additional_ignores: List[str] = []

class FileStats(BaseModel):
    """Model for file statistics."""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    file_types: Dict[str, int] = {}
    largest_file: Dict[str, Union[str, int, None]] = {"path": None, "size": 0}
    total_size: int = 0
    total_lines: int = 0
    empty_lines: int = 0
    comment_lines: int = 0

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            pathlib.Path: str
        }
        allow_population_by_field_name = True

    @property
    def avg_lines_per_file(self) -> float:
        """Calculate average lines per file."""
        if not self.processed_files or not self.total_lines:
            return 0.0
        return round(self.total_lines / self.processed_files, 2)

    def dict(self, *args, **kwargs):
        """Custom dict method to include computed properties."""
        d = super().dict(*args, **kwargs)
        d['avg_lines_per_file'] = self.avg_lines_per_file
        # Include file_types under both names for compatibility
        d['by_type'] = self.file_types
        return d

    class Config:
        """Additional configuration for JSON serialization."""
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type['FileStats']) -> None:
            """Add computed properties to the schema."""
            schema['properties']['by_type'] = {
                'title': 'By Type',
                'description': 'File statistics grouped by file type',
                'type': 'object',
                'additionalProperties': {'type': 'integer'}
            }

class TreeNode(BaseModel):
    """Model for directory tree visualization."""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    children: List['TreeNode'] = []
    metadata: Dict[str, Any] = {}

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            pathlib.Path: str
        }

class DirectoryStats(BaseModel):
    """Model for directory statistics."""
    total_dirs: int = 0
    max_depth: int = 0
    dirs_with_most_files: Dict[str, Union[str, int, None]] = {"path": None, "count": 0}
    empty_dirs: int = 0
    tree: Optional[TreeNode] = None  # Add tree to DirectoryStats

class FilterStats(BaseModel):
    """Model for filter statistics."""
    gitignore_filtered: int = 0
    custom_filtered: int = 0
    pattern_matches: Dict[str, int] = {}

    @property
    def most_effective_patterns(self) -> List[Dict[str, Union[str, int]]]:
        """Get the most effective patterns sorted by number of files filtered."""
        return [
            {"pattern": pattern, "files_filtered": count}
            for pattern, count in sorted(
                self.pattern_matches.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Return top 5 most effective patterns
        ]

    def dict(self, *args, **kwargs):
        """Custom dict method to include computed properties."""
        d = super().dict(*args, **kwargs)
        d['most_effective_patterns'] = self.most_effective_patterns
        return d

class ConcatenationStats(BaseModel):
    """Model for overall concatenation statistics."""
    file_stats: FileStats = FileStats()
    dir_stats: DirectoryStats = DirectoryStats()
    filter_stats: FilterStats = FilterStats()

class FileConcatenationError(Exception):
    """Custom exception for file concatenation errors."""
    pass 
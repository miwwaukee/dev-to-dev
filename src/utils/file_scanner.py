"""File scanning utilities."""

from pathlib import Path
from typing import List, Optional


def get_files_by_extension(
    directory: str,
    extensions: List[str],
    max_depth: Optional[int] = None
) -> List[Path]:
    """
    Get all files with specified extensions in directory.
    
    Args:
        directory: Root directory to scan
        extensions: List of extensions to include (e.g., [".py", ".js"])
        max_depth: Maximum directory depth (None for unlimited)
    
    Returns:
        List of Path objects matching criteria
    """
    root = Path(directory)
    files = []
    
    if not root.exists():
        return files
    
    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            # Check depth if specified
            if max_depth is not None:
                depth = len(file_path.relative_to(root).parts) - 1
                if depth > max_depth:
                    continue
            files.append(file_path)
    
    return files


def is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file."""
    text_extensions = {
        ".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h",
        ".rb", ".php", ".swift", ".kt", ".scala", ".cs", ".fs",
        ".html", ".css", ".scss", ".less", ".xml", ".json", ".yaml", ".yml",
        ".md", ".txt", ".rst", ".adoc",
        ".sql", ".sh", ".bash", ".zsh", ".fish",
        ".dockerfile", ".toml", ".ini", ".cfg", ".conf"
    }
    return file_path.suffix.lower() in text_extensions

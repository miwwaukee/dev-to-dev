"""
Tech Debt Finder Tool.

Scans codebase for TODO/FIXME/HACK/XXX/BUG comments and prioritizes them.
"""

import os
import re
from typing import List, Dict, Any
from pathlib import Path


# Priority keywords for classification
PRIORITY_PATTERNS = {
    "high": [
        r"\bFIXME\b",
        r"\bBUG\b",
        r"\bCRITICAL\b",
        r"\bSECURITY\b",
        r"\bAUTH\b",
        r"\bPASSWORD\b",
        r"\bTOKEN\b",
        r"\bVULNERABILITY\b"
    ],
    "medium": [
        r"\bTODO\b",
        r"\bHACK\b",
        r"\bXXX\b",
        r"\bREFACTOR\b",
        r"\bOPTIMIZE\b"
    ],
    "low": [
        r"\bLATER\b",
        r"\bSOMEDAY\b",
        r"\bNICE[- ]TO[- ]HAVE\b",
        r"\bOPTIONAL\b"
    ]
}

# Comment patterns for different languages
COMMENT_PATTERNS = [
    r"#\s*(TODO|FIXME|HACK|XXX|BUG)[:\s]*(.*)$",  # Python, Ruby, Shell
    r"//\s*(TODO|FIXME|HACK|XXX|BUG)[:\s]*(.*)$",  # JavaScript, Java, Go, C++
    r"/\*\s*(TODO|FIXME|HACK|XXX|BUG)[:\s]*(.*?)\*/",  # Multi-line comments
    r"--\s*(TODO|FIXME|HACK|XXX|BUG)[:\s]*(.*)$",  # SQL, Lua
]


def determine_priority(comment_type: str, message: str) -> str:
    """Determine priority based on comment type and message content."""
    combined = f"{comment_type} {message}".upper()
    
    # Check high priority patterns
    for pattern in PRIORITY_PATTERNS["high"]:
        if re.search(pattern, combined, re.IGNORECASE):
            return "high"
    
    # Check medium priority patterns
    for pattern in PRIORITY_PATTERNS["medium"]:
        if re.search(pattern, combined, re.IGNORECASE):
            return "medium"
    
    # Check low priority patterns
    for pattern in PRIORITY_PATTERNS["low"]:
        if re.search(pattern, combined, re.IGNORECASE):
            return "low"
    
    # Default priority based on comment type
    if comment_type.upper() in ["FIXME", "BUG"]:
        return "high"
    elif comment_type.upper() in ["HACK", "XXX"]:
        return "medium"
    else:
        return "low"


def scan_file(file_path: str) -> List[Dict[str, Any]]:
    """Scan a single file for tech debt comments."""
    items = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in COMMENT_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE | re.MULTILINE)
                if match:
                    comment_type = match.group(1).upper()
                    message = match.group(2).strip() if match.group(2) else ""
                    
                    priority = determine_priority(comment_type, message)
                    
                    # Get context (surrounding lines)
                    start_ctx = max(0, line_num - 2)
                    end_ctx = min(len(lines), line_num + 1)
                    context = ''.join(lines[start_ctx:end_ctx]).strip()
                    
                    items.append({
                        "file": file_path,
                        "line": line_num,
                        "type": comment_type,
                        "message": message,
                        "priority": priority,
                        "context": context[:200]  # Limit context length
                    })
                    break  # Only match once per line
    
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return items


def find_tech_debt(
    path: str = ".",
    extensions: List[str] = None,
    min_priority: str = "low"
) -> Dict[str, Any]:
    """
    Scan directory for tech debt comments.
    
    Args:
        path: Directory path to scan
        extensions: List of file extensions to scan (e.g., [".py", ".js"])
        min_priority: Minimum priority level to include (low/medium/high)
    
    Returns:
        Dictionary with items list and summary statistics
    """
    if extensions is None:
        extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]
    
    priority_order = {"low": 0, "medium": 1, "high": 2}
    min_priority_level = priority_order.get(min_priority, 0)
    
    all_items = []
    files_scanned = 0
    
    # Walk through directory
    root_path = Path(path)
    if not root_path.exists():
        return {
            "error": f"Path does not exist: {path}",
            "items": [],
            "summary": {"total": 0, "high": 0, "medium": 0, "low": 0, "files_scanned": 0}
        }
    
    for file_path in root_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            files_scanned += 1
            items = scan_file(str(file_path))
            all_items.extend(items)
    
    # Filter by priority
    filtered_items = [
        item for item in all_items
        if priority_order.get(item["priority"], 0) >= min_priority_level
    ]
    
    # Calculate summary
    summary = {
        "total": len(filtered_items),
        "high": sum(1 for item in filtered_items if item["priority"] == "high"),
        "medium": sum(1 for item in filtered_items if item["priority"] == "medium"),
        "low": sum(1 for item in filtered_items if item["priority"] == "low"),
        "files_scanned": files_scanned
    }
    
    return {
        "items": filtered_items,
        "summary": summary
    }

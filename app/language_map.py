import os

def get_language_by_extension(ext):
    ext = ext.lower()
    lang_map = {
        # C/C++
        ".c": "c", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c++": "cpp",
        ".h": "cpp", ".hpp": "cpp", ".hxx": "cpp",
        
        # Java
        ".java": "java",
        
        # C#
        ".cs": "csharp",
        
        # Objective-C
        ".m": "objectivec", ".mm": "objectivec",
        
        # Swift
        ".swift": "swift",
        
        # Python
        ".py": "python", ".pyx": "python", ".pyd": "python", ".pyi": "python",
        
        # JavaScript/TypeScript
        ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".d.ts": "typescript",
        ".cts": "typescript", ".mts": "typescript",
        
        # Ruby
        ".rb": "ruby", ".rake": "ruby", ".gemspec": "ruby",
        
        # Scala
        ".scala": "scala",
        
        # Go
        ".go": "go",
        
        # Kotlin
        ".kt": "kotlin", ".kts": "kotlin",
        
        # Rust
        ".rs": "rust",
        
        # Dart
        ".dart": "dart",
        
        # Lua
        ".lua": "lua",
        
        # Web
        ".html": "html", ".htm": "html", ".xhtml": "html",
        ".css": "css", ".scss": "css", ".sass": "css", ".less": "css",
        ".json": "json", ".jsonc": "json",
        ".xml": "xml", ".svg": "xml",
        
        # Config files
        ".yml": "yaml", ".yaml": "yaml",
        ".toml": "toml",
        ".ini": "ini", ".cfg": "ini", ".conf": "ini",
        ".md": "markdown", ".mdx": "markdown",
        ".sh": "bash", ".bash": "bash", ".zsh": "bash",
        ".bat": "batch", ".cmd": "batch",
        ".ps1": "powershell",
    }
    return lang_map.get(ext, None)
    
# Function to check if a file should be analyzed
def should_analyze_file(file_path):
    """
    Determines if a file should be analyzed based on its extension and path.
    Returns True if the file should be analyzed, False otherwise.
    """
    # Skip binary files and certain file types that don't need analysis
    skip_extensions = {
        # Binary files
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp',
        '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.exe', '.dll', '.so', '.dylib', '.class',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.ttf', '.otf', '.woff', '.woff2',
        
        # Lock files
        '.lock',
        
        # Generated files
        '.min.js', '.min.css',
    }
    
    # Skip certain directories
    skip_dirs = {
        '.git', 'node_modules', 'dist', 'build', 'target',
        'vendor', 'bin', 'obj', 'out', 'venv', 'env',
        '__pycache__', '.idea', '.vscode', '.vs',
    }
    
    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext in skip_extensions:
        return False
    
    # Check if file is in a directory that should be skipped
    path_parts = file_path.lower().split(os.sep)
    for part in path_parts:
        if part in skip_dirs:
            return False
    
    # Special handling for Flutter/Dart projects
    if 'ios/Runner.xcworkspace' in file_path:
        return False
    
    # Check if the file has a supported language
    return get_language_by_extension(ext) is not None

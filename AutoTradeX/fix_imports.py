#!/usr/bin/env python3
"""
Script to fix import statements in the AutoTradeX codebase
Replaces 'autotradex' imports with 'backend' imports
"""

import os
import re
import sys
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file has autotradex imports
    if 'from autotradex' in content or 'import backend' in content:
        print(f"Fixing imports in {file_path}")
        
        # Add sys.path modification if not already present
        sys_path_code = """import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
"""
        
        if 'sys.path.insert' not in content:
            # Find the last import statement
            import_pattern = re.compile(r'^(?:from|import)\s+\w+', re.MULTILINE)
            matches = list(import_pattern.finditer(content))
            
            if matches:
                last_import = matches[-1]
                last_import_end = last_import.end()
                content = content[:last_import_end] + "\n\n" + sys_path_code + content[last_import_end:]
        
        # Replace autotradex imports with backend imports
        content = re.sub(r'from autotradex\.', 'from backend.', content)
        content = re.sub(r'import backend\.', 'import backend.', content)
        content = re.sub(r'import backend', 'import backend', content)
        
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def fix_imports_in_directory(directory):
    """Recursively fix imports in all Python files in a directory"""
    fixed_count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    return fixed_count

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fixed_count = fix_imports_in_directory(base_dir)
    print(f"Fixed imports in {fixed_count} files")

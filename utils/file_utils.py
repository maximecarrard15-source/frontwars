"""
File utilities for Frontwars
"""

import os
import json
import pickle
import gzip
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def ensure_directory(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)


def file_exists(path: str) -> bool:
    """Check if file exists"""
    return os.path.exists(path)


def read_text_file(path: str) -> str:
    """Read text file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text_file(path: str, content: str):
    """Write text file"""
    ensure_directory(os.path.dirname(path) or '.')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def read_json_file(path: str) -> Dict[str, Any]:
    """Read JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(path: str, data: Dict[str, Any], indent: int = 2):
    """Write JSON file"""
    ensure_directory(os.path.dirname(path) or '.')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)


def read_pickle_file(path: str) -> Any:
    """Read pickle file"""
    with open(path, 'rb') as f:
        return pickle.load(f)


def write_pickle_file(path: str, data: Any):
    """Write pickle file"""
    ensure_directory(os.path.dirname(path) or '.')
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def read_gzip_file(path: str) -> bytes:
    """Read gzip file"""
    with gzip.open(path, 'rb') as f:
        return f.read()


def write_gzip_file(path: str, data: bytes):
    """Write gzip file"""
    ensure_directory(os.path.dirname(path) or '.')
    with gzip.open(path, 'wb') as f:
        f.write(data)


def get_file_size(path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(path)


def get_file_extension(path: str) -> str:
    """Get file extension"""
    return os.path.splitext(path)[1].lower()


def get_filename_without_extension(path: str) -> str:
    """Get filename without extension"""
    return os.path.splitext(os.path.basename(path))[0]


def list_files(directory: str, extension: str = None) -> List[str]:
    """List files in directory"""
    files = []
    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)
        if os.path.isfile(filepath):
            if extension is None or file.endswith(extension):
                files.append(filepath)
    return files


def list_directories(directory: str) -> List[str]:
    """List directories in directory"""
    return [os.path.join(directory, d) for d in os.listdir(directory) 
            if os.path.isdir(os.path.join(directory, d))]


def copy_file(source: str, destination: str):
    """Copy file"""
    ensure_directory(os.path.dirname(destination) or '.')
    import shutil
    shutil.copy2(source, destination)


def move_file(source: str, destination: str):
    """Move file"""
    ensure_directory(os.path.dirname(destination) or '.')
    import shutil
    shutil.move(source, destination)


def delete_file(path: str):
    """Delete file"""
    if os.path.exists(path):
        os.remove(path)


def delete_directory(path: str):
    """Delete directory recursively"""
    import shutil
    if os.path.exists(path):
        shutil.rmtree(path)


def get_relative_path(path: str, relative_to: str = None) -> str:
    """Get relative path"""
    if relative_to is None:
        relative_to = os.getcwd()
    return os.path.relpath(path, relative_to)


def get_absolute_path(path: str) -> str:
    """Get absolute path"""
    return os.path.abspath(path)


def is_path_inside(path: str, parent: str) -> bool:
    """Check if path is inside parent directory"""
    path = os.path.abspath(path)
    parent = os.path.abspath(parent)
    return path.startswith(parent + os.sep) or path == parent


def find_files(directory: str, pattern: str = None) -> List[str]:
    """Find files matching pattern"""
    import fnmatch
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if pattern is None or fnmatch.fnmatch(filename, pattern):
                files.append(os.path.join(root, filename))
    return files


def read_csv_file(path: str, delimiter: str = ',') -> List[List[str]]:
    """Read CSV file"""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(line.split(delimiter))
    return data


def write_csv_file(path: str, data: List[List[str]], delimiter: str = ','):
    """Write CSV file"""
    ensure_directory(os.path.dirname(path) or '.')
    with open(path, 'w', encoding='utf-8') as f:
        for row in data:
            f.write(delimiter.join(row) + '\n')

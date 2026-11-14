"""
Logging system for Frontwars
"""

import logging
import sys
import os
import time
from typing import Any, Dict, List, Optional, TextIO
from dataclasses import dataclass, field
from enum import Enum
import traceback
from datetime import datetime

from config import ASSETS_PATH


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """Single log entry"""
    timestamp: float
    level: LogLevel
    message: str
    tag: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        time_str = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S.%f")[:-3]
        level_str = self.level.name.ljust(8)
        tag_str = f"[{self.tag}]" if self.tag else ""
        return f"{time_str} {level_str} {tag_str} {self.message}"


class Logger:
    """Advanced logging system for Frontwars"""
    
    def __init__(self, name: str = "Frontwars"):
        self.name = name
        self.level = LogLevel.INFO
        self.handlers: List['LogHandler'] = []
        self.tags: Dict[str, bool] = {}
        self.logs: List[LogEntry] = []
        self.max_logs = 10000
        self.start_time = time.time()
        
        # Add default console handler
        self.add_handler(ConsoleHandler())
        
        # Add file handler
        log_dir = os.path.join(ASSETS_PATH, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"frontwars_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.add_handler(FileHandler(log_file))
    
    def set_level(self, level: LogLevel):
        """Set minimum log level"""
        self.level = level
    
    def add_handler(self, handler: 'LogHandler'):
        """Add log handler"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: 'LogHandler'):
        """Remove log handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def enable_tag(self, tag: str):
        """Enable logging for specific tag"""
        self.tags[tag] = True
    
    def disable_tag(self, tag: str):
        """Disable logging for specific tag"""
        self.tags[tag] = False
    
    def is_tag_enabled(self, tag: str) -> bool:
        """Check if tag is enabled"""
        return self.tags.get(tag, True)
    
    def log(self, level: LogLevel, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log a message"""
        if level.value < self.level.value:
            return
        
        if tag and not self.is_tag_enabled(tag):
            return
        
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            tag=tag,
            data=data or {}
        )
        
        # Store log entry
        self.logs.append(entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Send to handlers
        for handler in self.handlers:
            handler.handle(entry)
    
    def debug(self, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, tag, data)
    
    def info(self, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log info message"""
        self.log(LogLevel.INFO, message, tag, data)
    
    def warning(self, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, tag, data)
    
    def error(self, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log error message"""
        self.log(LogLevel.ERROR, message, tag, data)
    
    def critical(self, message: str, tag: str = "", data: Dict[str, Any] = None):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, tag, data)
    
    def exception(self, message: str = "Exception occurred", tag: str = "", 
                  data: Dict[str, Any] = None):
        """Log exception with traceback"""
        tb = traceback.format_exc()
        full_message = f"{message}\n{tb}"
        self.log(LogLevel.ERROR, full_message, tag, data)
    
    def get_logs(self, level: Optional[LogLevel] = None) -> List[LogEntry]:
        """Get all logs or filtered by level"""
        if level is None:
            return self.logs.copy()
        return [e for e in self.logs if e.level.value >= level.value]
    
    def clear_logs(self):
        """Clear stored logs"""
        self.logs.clear()
    
    def uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time


class LogHandler:
    """Base log handler"""
    
    def handle(self, entry: LogEntry):
        """Handle log entry"""
        raise NotImplementedError


class ConsoleHandler(LogHandler):
    """Console log handler"""
    
    def __init__(self, stream: TextIO = None):
        self.stream = stream or sys.stdout
        self.colors = {
            LogLevel.DEBUG: '\033[94m',    # Blue
            LogLevel.INFO: '\033[92m',     # Green
            LogLevel.WARNING: '\033[93m',  # Yellow
            LogLevel.ERROR: '\033[91m',    # Red
            LogLevel.CRITICAL: '\033[95m' # Magenta
        }
        self.reset_color = '\033[0m'
        self.use_colors = True
    
    def handle(self, entry: LogEntry):
        """Print to console"""
        if self.use_colors:
            color = self.colors.get(entry.level, '')
            reset = self.reset_color
            message = f"{color}{entry}{reset}"
        else:
            message = str(entry)
        
        self.stream.write(message + '\n')
        self.stream.flush()


class FileHandler(LogHandler):
    """File log handler"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = open(filename, 'a', encoding='utf-8')
    
    def handle(self, entry: LogEntry):
        """Write to file"""
        self.file.write(str(entry) + '\n')
        self.file.flush()
    
    def close(self):
        """Close file"""
        self.file.close()
    
    def __del__(self):
        self.close()


class MemoryHandler(LogHandler):
    """In-memory log handler (for UI display)"""
    
    def __init__(self, max_entries: int = 1000):
        self.entries: List[LogEntry] = []
        self.max_entries = max_entries
    
    def handle(self, entry: LogEntry):
        """Store in memory"""
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
    
    def get_entries(self) -> List[LogEntry]:
        """Get all entries"""
        return self.entries.copy()
    
    def clear(self):
        """Clear entries"""
        self.entries.clear()


# Global logger instance
logger = Logger("Frontwars")


# Convenience functions
def debug(message: str, tag: str = "", data: Dict[str, Any] = None):
    logger.debug(message, tag, data)


def info(message: str, tag: str = "", data: Dict[str, Any] = None):
    logger.info(message, tag, data)


def warning(message: str, tag: str = "", data: Dict[str, Any] = None):
    logger.warning(message, tag, data)


def error(message: str, tag: str = "", data: Dict[str, Any] = None):
    logger.error(message, tag, data)


def critical(message: str, tag: str = "", data: Dict[str, Any] = None):
    logger.critical(message, tag, data)


def exception(message: str = "Exception occurred", tag: str = "", 
               data: Dict[str, Any] = None):
    logger.exception(message, tag, data)

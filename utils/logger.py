import logging
import threading
from logging.handlers import RotatingFileHandler
import sys
from tkinter import END, N, S, E, W, Scrollbar, Text,ttk
import tkinter as tk 

# Define a custom handler for the ScrolledText widget
class LoggingHandlerFrame(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.config(state='disabled')

    def emit(self, record):
        log_entry = self.format(record)
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, log_entry + '\n')
        self.text_widget.yview(tk.END)
        self.text_widget.config(state='disabled')
        

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add color to log messages."""
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[41m' # Red background
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{super().format(record)}{self.RESET}"

# Define constants
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_level=logging.INFO, log_file='confluence_bot.log'):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Logger, cls).__new__(cls)
                    cls._instance._initialize_logger(log_level, log_file)
        return cls._instance

    def _initialize_logger(self, log_level, log_file):
        self.logger_instance = logging.getLogger(__name__)
        self.logger_instance.setLevel(log_level)

        # Create a rotating file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=30)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        self.logger_instance.addHandler(file_handler)

        # Create a stream handler for stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        stream_formatter = ColoredFormatter(LOG_FORMAT)
        stream_handler.setFormatter(stream_formatter)
        self.logger_instance.addHandler(stream_handler)

    def set_log_level(self, log_level):
        self.logger_instance.setLevel(log_level)
        for handler in self.logger_instance.handlers:
            handler.setLevel(log_level)

    def set_text_widget(self, text_widget):
        self.text_handler = LoggingHandlerFrame(text_widget)
        self.text_handler.setLevel(self.logger_instance.level)
        self.text_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.logger_instance.addHandler(self.text_handler)

    def debug(self, message):
        self.logger_instance.debug(message)
    
    def info(self, message):
        self.logger_instance.info(message)
    
    def warning(self, message):
        self.logger_instance.warning(message)
    
    def error(self, message):
        self.logger_instance.error(message)

    def critical(self, message):
        self.logger_instance.critical(message)

    def warn_tree_not_initialized(self,is_source:bool=True):
        if is_source:
            self.logger_instance.warning("Source Tree not initialized!")
        else:
            self.logger_instance.warning("Target Tree not initialized!")
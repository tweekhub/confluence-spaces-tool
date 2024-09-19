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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Create a rotating file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=30)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Create a stream handler for stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        stream_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        self.logger.addHandler(stream_handler)

    def set_log_level(self, log_level):
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)

    def set_text_widget(self, text_widget):
        self.text_handler = LoggingHandlerFrame(text_widget)
        self.text_handler.setLevel(self.logger.level)
        self.text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.text_handler)

    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

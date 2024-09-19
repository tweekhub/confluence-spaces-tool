from app import ConfluenceMigrationApp
from utils.logger import Logger
import tkinter as tk
from tkinter import ttk
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Confluence Space Migration Assistant")
    parser.add_argument("--config-file", default="./config.yaml", help="Specify the path to the configuration file")
    parser.add_argument("--api-config-file", default="./confluence-api.json", help="Specify the path to the API configuration file")
    parser.add_argument("--browser-config-file", default="./confluence-elements.json", help="Specify the path to the UI elements configuration file")
    parser.add_argument("--download-dir", default="downloads", type=str, help="Specify the directory to download files")

    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Set the logging levels")
    parser.add_argument("--log-file", default="confluence-migration.log", help="Specify the path to the log file for the migration process")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    return parser.parse_args()


def main():
    args = parse_arguments()
    # Convert args to a dictionary, excluding None values
    kwargs = {k: v for k, v in vars(args).items() if v is not None}
    logger = Logger(log_file=kwargs.pop('log_file'))
    logger.set_log_level(log_level=kwargs.pop('log_level').upper())

    root = tk.Tk()
    root.title("Confluence Migration Tool")
    window_width = 1345
    window_height = 915
    # Set the initial window size
    root.geometry(f"{window_width}x{window_height}")
    root.resizable(False, False)  # Allow resizing in both directions
    # # Open in full screen mode
    root.attributes('-fullscreen', False)

    # # Bind the Escape key to exit full screen
    # root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))
    
    # Create a style object
    style = ttk.Style()
    style.configure('TNotebook', background='#f0f0f0')  # Background color for notebook
    style.configure('TNotebook.Tab', background='#d0d0d0', foreground='black', padding=[10, 5], font=('Arial', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', '#a0a0a0')])  # Change background when selected

    app = ConfluenceMigrationApp(root,**kwargs)
    root.mainloop()

if __name__ == "__main__":
    main()
    

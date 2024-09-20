from app import ConfluenceSpacesApp
from utils.logger import Logger
import tkinter as tk
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Confluence Spaces Tool")
    parser.add_argument("--config-file", default="./configuration.yaml", help="Specify the path to the configuration file")
    parser.add_argument("--api-config-file", default="./confluence-api.json", help="Specify the path to the API configuration file")
    parser.add_argument("--browser-config-file", default="./confluence-elements.json", help="Specify the path to the UI elements configuration file")
    parser.add_argument("--download-dir", default="downloads", type=str, help="Specify the directory to download files")

    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Set the logging levels")
    parser.add_argument("--log-file", default="confluence-Spaces.log", help="Specify the path to the log file for the Spacesprocess")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    return parser.parse_args()

def show_about():
    messagebox.showinfo("About", "Confluence Spaces Tool\nVersion 1.0\nDeveloped by Your Name")


def main():
    args = parse_arguments()
    # Convert args to a dictionary, excluding None values
    kwargs = {k: v for k, v in vars(args).items() if v is not None}
    logger = Logger(log_file=kwargs.pop('log_file'))
    logger.set_log_level(log_level=kwargs.pop('log_level').upper())

    root = tk.Tk()
    root.title("Confluence Spaces Tool")
    # Set the initial window size
    window_width = 1260
    window_height = 915
    root.geometry(f"{window_width}x{window_height}")
    root.resizable(False, False)

    ConfluenceSpacesApp(root,**kwargs)
    root.mainloop()

if __name__ == "__main__":
    main()
    

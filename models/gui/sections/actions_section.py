from . import logger
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class ActionsSection:
    DEFAULT_ACTIONS = {
        "fetch_pages": {
            "text": "Fetch",
            "options": {
                "source": {"text": "Source Pages", "command": lambda: logger.info("Fetching Source Pages...")},
                "target": {"text": "Target Pages", "command": lambda: logger.info("Fetching Target Pages...")},
            },
            "description": "Fetch source or target pages."
        },
        "create_pages": {
            "text": "Create",
            "options": {
                "create_pages_only": {"text": "Pages", "command": lambda: logger.info("Creating Pages in target confluence space...")},
                "create_pages_with_attachments": {"text": "Pages with Attachments", "command": lambda: logger.info("Creating Pages with attachments in target confluence space...")},
            },
            "description": "Create or Copy Content to Target Space."
        },
        "copy_pages": {
            "text": "Copy",
            "options": {
                "copy_pages_source_mode": {"text": "Copy Content (Source View)", "command": lambda: logger.info("Visual Copy for Pages to target confluence space using Confluence Source View Module...")},
                "copy_pages_edit_mode": {"text": "Copy Content (Edit View)", "command": lambda: logger.info("Visual Copy for Pages to target confluence space  by editing view mode...")},
                "copy_attachments": {"text": "Copy Attachments", "command": lambda: logger.info("Copy Attachments to target confluence space...")},
            },
            "description": "Copy Content from Source to Target Space."
        },
        "save": {
            "text": "Save",
            "options": {
                "source": {"text": "Source Pages", "command": lambda: logger.info("Saving Source Pages...")},
                "target": {"text": "Target Pages", "command": lambda: logger.info("Saving Target Pages...")},
            },
            "description": "Save source or target pages to a file."
        },
        "download": {
            "text": "Download",
            "options": {
                "attachments": {"text": "Download Attachments", "command": lambda: logger.info("Downloading Attachments...")},
            },
            "description": "Download various files from the system."
        },
        "export":{
            "text": "Export",
            "options": {
                "pdf": {"text": "Export PDFs", "command": lambda: logger.info("Downloading PDFs...")},
                "word": {"text": "Export Docs", "command": lambda: logger.info("Downloading Word Docs...")},
            },
            "description": "Export pages as PDF or Word Docs."
        }
    }
    def __init__(self, parent, row=0, column=0, padx=5, pady=5, config=None, layout=None, sticky="nsew"):
        self.parent = parent
        self.row = row
        self.column = column
        self.padx = padx
        self.pady = pady
        self.sticky = sticky
        self.config = config or self.DEFAULT_ACTIONS
        self.layout = layout or {"orientation": "horizontal"}  # Default to horizontal layout
        self.buttons = {}
        self.create_section()

    def create_section(self):
        action_frame = ttk.LabelFrame(self.parent, text="Actions")
        action_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
        # Configure grid rows and columns for centering
        action_frame.grid_rowconfigure(0, weight=1)
        action_frame.grid_rowconfigure(1, weight=1)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        action_frame.grid_columnconfigure(2, weight=1)
        action_frame.grid_columnconfigure(3, weight=1)
        action_frame.grid_columnconfigure(4, weight=1)
        action_frame.grid_columnconfigure(5, weight=1)

        # First row of actions, centered
        self.create_combobox_with_button(action_frame, "fetch_pages", 0, 0)
        self.create_combobox_with_button(action_frame, "create_pages", 0, 3)
        self.create_combobox_with_button(action_frame, "copy_pages", 0, 6)

        # Second row of actions, centered
        self.create_combobox_with_button(action_frame, "save", 1, 0)
        self.create_combobox_with_button(action_frame, "download", 1, 3)
        self.create_combobox_with_button(action_frame, "export", 1, 6)

        # Log output section, placed below the action buttons and frame
        log_output = ScrolledText(self.parent, wrap=tk.WORD, height=20)
        log_output.grid(row=1, column=0, columnspan=9, padx=5, pady=5, sticky="nsew")

        # Configure the grid rows and columns to avoid overlap and allow resizing
        self.parent.grid_rowconfigure(1, weight=1)  # Row for log_output
        self.parent.grid_columnconfigure(0, weight=1)  # Adjust for proper resizing
        
        logger.set_text_widget(text_widget=log_output)

        self.update_button_state("create_pages", "disabled", "disabled")
        self.update_button_state("copy_pages", "disabled", "disabled")
        self.update_button_state("save", "disabled", "disabled")
        self.update_button_state("download", "disabled", "disabled")
        self.update_button_state("export", "disabled", "disabled")

    def create_combobox_with_button(self, parent, action_key, row, col):
        action = self.config.get(action_key)
        if not action:
            print(f"Action '{action_key}' not found in config.")
            return

        # Create a frame to group the label, combobox, and button
        group_frame = ttk.Frame(parent)
        group_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        # Label for the action
        label = ttk.Label(group_frame, text=action["text"])
        label.pack(side="left", padx=(0, 5))  # Padding to the right of the label

        # Combobox with the list of option texts
        option_texts = [option_data["text"] for option_data in action["options"].values()]
        combo = ttk.Combobox(group_frame, values=option_texts, state="readonly", width=20)
        combo.pack(side="left", padx=(0, 5))  # Padding to the right of the combobox

        # Execute button
        button = tk.Button(group_frame, text="Execute", command=lambda c=combo, k=action_key: self.execute_selected_option(c, k))
        button.pack(side="left")

        # Save the button and combobox reference
        self.buttons[action_key] = (combo, button)


    def execute_selected_option(self, combo, action_key):
        selected_text = combo.get()
        if selected_text and action_key in self.config:
            action_options = self.config[action_key]["options"]

            # Find the matching option key for the selected text
            selected_key = None
            for key, option in action_options.items():
                if option["text"] == selected_text:
                    selected_key = key
                    break

            if selected_key and selected_key in action_options:
                # Execute the command associated with the selected option's key
                action_options[selected_key]["command"]()
            else:
                print(f"Invalid option selected for {action_key}.")
        else:
            print(f"No valid option selected for {action_key}.")

    def update_action_command(self, action_name, option_key, new_command):
        if action_name in self.config:
            action = self.config[action_name]
            if "options" in action:
                # Check if the option_key exists in the options
                if option_key in action["options"]:
                    # Update the command for the matched option key
                    self.config[action_name]["options"][option_key]["command"] = new_command["command"]
                    # logger.info(f"Updated command for {option_key} in {action_name}")
                else:
                    logger.warning(f"Option '{option_key}' not found in '{action_name}'")
            else:
                logger.warning(f"No options found in action '{action_name}'")
        else:
            logger.warning(f"Action '{action_name}' not found in config.")

    def update_button_state(self, action_name, new_state_combobox:str="readonly",new_state_button:str="disabled"):
        if action_name in self.buttons:
            widget = self.buttons[action_name]
            if isinstance(widget, tuple):
                combobox, button = widget
                combobox.config(state=new_state_combobox)  # Update combobox state
                button.config(state=new_state_button)  # Update button state
            else:
                widget.config(state=new_state_button)
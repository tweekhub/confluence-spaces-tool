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
                "copy_pages_source_mode": {"text": "Copy Content (Source View)", "command": lambda: logger.info("Visual Copy for Pages to target confluence space using Confluence Source View Module...")},
                "copy_pages_edit_mode": {"text": "Copy Content (Edit View)", "command": lambda: logger.info("Visual Copy for Pages to target confluence space  by editing view mode...")},
                "copy_attachments": {"text": "Copy Attachments", "command": lambda: logger.info("Copy Attachments to target confluence space...")},
            },
            "description": "Create or Copy Content to Target Space."
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
                "pdf": {"text": "Export PDFs", "command": lambda: logger.info("Downloading PDFs...")},
                "word": {"text": "Export Docs", "command": lambda: logger.info("Downloading Word Docs...")},
                "attachments": {"text": "Download Attachments", "command": lambda: logger.info("Downloading Attachments...")},
            },
            "description": "Download various files from the system."
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
        action_frame = tk.LabelFrame(self.parent, text="Actions")
        action_frame.grid(row=self.row, column=self.column, padx=self.padx, pady=self.pady, sticky=self.sticky)

        # Use options from config to create comboboxes and buttons
        self.create_combobox_with_button(action_frame, "fetch_pages", 0, 0,"w")
        self.create_combobox_with_button(action_frame, "create_pages", 0, 3,"w")
        self.create_combobox_with_button(action_frame, "save", 0, 6,"e")
        self.create_combobox_with_button(action_frame, "download", 0, 9,"e")
        # Log output section
        log_output = ScrolledText(self.parent, wrap=tk.WORD, width=100, height=20)
        log_output.grid(row=2, column=0, columnspan=4, padx=5, pady=10, sticky="ew")
        logger.set_text_widget(text_widget=log_output)
        self.update_button_state("create_pages","disabled","disabled")
        self.update_button_state("save","disabled","disabled")
        self.update_button_state("download","disabled","disabled")


    def create_combobox_with_button(self, parent, action_key, row, col,sticky):
        action = self.config.get(action_key)
        if not action:
            print(f"Action '{action_key}' not found in config.")
            return

        # Label for the action
        label = ttk.Label(parent, text=action["text"])
        label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Combobox with the list of option texts
        option_texts = [option_data["text"] for option_data in action["options"].values()]
        combo = ttk.Combobox(parent, values=option_texts, state="readonly",width=17)
        combo.grid(row=row, column=col + 1, padx=5, pady=5, sticky="nsew")
        # Bind a tooltip to display the full text on hover
        def show_tooltip(event):
            item = combo.get()
            if item:
                tooltip_label.config(text=item)
                tooltip_label.place(x=event.x_root, y=event.y_root)
        
        def hide_tooltip(event):
            tooltip_label.place_forget()
        
        tooltip_label = tk.Label(parent, text="", background="yellow", relief="solid", borderwidth=1, padx=5, pady=2)
        combo.bind("<<Enter>>", show_tooltip)
        combo.bind("<<Leave>>", hide_tooltip)
        # Execute button
        button = tk.Button(parent, text="Execute", command=lambda c=combo, k=action_key: self.execute_selected_option(c, k))
        button.grid(row=row, column=col + 2, padx=5, pady=5, sticky="nsew")

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
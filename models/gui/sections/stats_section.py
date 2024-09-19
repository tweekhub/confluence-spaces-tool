import tkinter as tk
from tkinter import ttk

class StatsTable:
    DEFAULTS = {
        "root_page_title": "n/a",
        "root_page_id": "n/a",
        "space_key": "n/a",
        "space_id": "n/a",
        "current_user_email": "n/a",
        "current_user_groups": [],
        "total_attachments_created": "",
        "total_pages_created": "",
        "total_http_requests": "n/a",
        "successful_http_requests": "n/a",
        "failed_http_requests": "n/a",
    }

    def __init__(self, parent, title="Stats Table", row=0, column=0, padx=5, pady=5, sticky="nw", config=None):
        self.parent = parent
        self.title = title
        self.row = row
        self.column = column
        self.padx = padx
        self.pady = pady
        self.sticky = sticky
        self.config = config or self.DEFAULTS
        self.create_section()
        # if self.title.lower().startswith("source"):
        #     self.config.pop('total_attachments_created', None)
        #     self.config.pop('total_attachments_created', None)

    def create_section(self):
        self.frame = ttk.LabelFrame(self.parent, text=self.title, padding=5)
        self.frame.grid(row=self.row, column=self.column, padx=self.padx, pady=self.pady, sticky=self.sticky)

        self.labels = {}

        # Create a grid with proper column weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=2)
        self.frame.columnconfigure(2, weight=1)
        self.frame.columnconfigure(3, weight=2)
        self.frame.columnconfigure(4, weight=1)
        self.frame.columnconfigure(5, weight=1)

        # Create Labels and Values
        num_items = len(self.config) - 1  # Exclude current_user_groups
        midpoint = (num_items + 1) // 2  # Adjust midpoint to handle odd number of items

        for i, (key, value) in enumerate(self.config.items()):
            if key == "current_user_groups":
                continue

            # Convert underscored keys to display names with spaces
            display_name = key.replace('_', ' ').title()

            if i < midpoint:
                col = 0  # First column
                row = i  # Row index for first column
                sticky = "e"
            else:
                col = 2  # Second column (offset by 2 to create a gap between columns)
                row = i - midpoint  # Adjust row index for second column
                sticky = "e"

            # Create the label and value for the given key-value pair
            ttk.Label(self.frame, text=f"{display_name}:").grid(row=row, column=col, padx=5, pady=5, sticky=sticky)
            self.labels[key] = ttk.Label(self.frame, text=value)
            self.labels[key].grid(row=row, column=col+1, padx=5, pady=5, sticky="w")

        # Create Label and Listbox for user groups
        ttk.Label(self.frame, text="Current User Groups:").grid(row=0, column=5, padx=5, pady=5, sticky="nw")
        self.current_user_groups_listbox = tk.Listbox(self.frame, height=6, width=40)
        self.current_user_groups_listbox.grid(row=1, column=5, rowspan=max(len(self.config.get("current_user_groups", [])), 6), padx=5, pady=5, sticky="nsew")
        # Configure Listbox column to expand with the window
        self.frame.rowconfigure(1, weight=1)  # Ensure Listbox row expands
        # Populate the Listbox
        self.update_current_user_groups(self.config.get("current_user_groups", []))

    def update_stats(self, new_stats):
        for key, value in new_stats.items():
            if key in self.labels:
                self.labels[key].config(text=value)

    def update_current_user_groups(self, current_user_groups):
            self.current_user_groups_listbox.delete(0, tk.END)
            for group in current_user_groups:
                self.current_user_groups_listbox.insert(tk.END, group)
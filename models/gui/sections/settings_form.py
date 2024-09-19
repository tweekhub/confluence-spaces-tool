import re
import tkinter as tk
from tkinter import ttk, messagebox
from . import logger

class SettingsForm:
    DEFAULTS = {
        'name': "",
        'confluence_type': "server",
        'site_url': "",
        'home_path': "",
        'space_key': "",
        'root_page_id': "",
        'label': "",
        'fetch_pages_limit': "",
        'fetch_attachments_limit': "",
        'exclude_ids': [],
        'credentials' : {
            'email': "",
            'password': "",
            'show_password': False,
            'mfa_enabled': False,
            'mfa_secret_key': "",
            'api_token': "",
            'rest_auth_type': "basic_auth",
        }
    }
    REST_AUTH_TYPES = ["basic_auth", "cookies_auth", "header_auth"]

    def __init__(self, root, title="Confluence Configuration Form", row=0, column=0, padx=10, pady=10, sticky="w", config=None,update_config:dict=None):
        self.root = root
        self.title = title
        self.row = row
        self.column = column
        self.padx = padx
        self.pady = pady
        self.sticky = sticky
        self.config = config or self.DEFAULTS
        self.update_config = update_config
        self.edit_mode = False  # Indicates if the form is in edit mode
        self.create_section()

    def create_section(self):
        frame = ttk.LabelFrame(self.root, text=self.title, padding=15)
        frame.grid(row=self.row, column=self.column, padx=self.padx, pady=self.pady, sticky="nsew")

        # Helper function for consistent padding
        def create_label_entry(label_text, row, var_name, width=50, show=None, state="normal"):
            ttk.Label(frame, text=f'{label_text}: ').grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(frame, width=width, show=show, state=state)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            entry.insert(0, self.config.get(var_name, '') if isinstance(self.config.get(var_name, ''), str) else "")
            return entry

        # Error Label Helper Function
        def create_error_label(row):
            label = tk.Label(frame, text="", fg="red", font=("Arial", 8))
            label.grid(row=row, column=2, padx=5, pady=5)
            return label

        # Name Field
        self.name_entry = create_label_entry('Name', 0, 'name')
        self.name_error_label = create_error_label(0)

        # Confluence Type
        ttk.Label(frame, text="Confluence Type:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.confluence_type = tk.StringVar(value=self.config.get('confluence_type', 'server'))
        self.confluence_type_combobox = ttk.Combobox(frame, textvariable=self.confluence_type, values=["server", "cloud"], state="readonly", width=48)
        self.confluence_type_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.confluence_type_combobox.bind("<<ComboboxSelected>>", self.update_api_token_visibility)

        # Site URL, Home Path, Space Key, Root Page ID, Include Label, Exclude IDs
        self.site_entry = create_label_entry('Site URL', 2, 'site_url')
        self.site_error_label = create_error_label(2)

        self.home_path_entry = create_label_entry('Homepage Path', 3, 'home_path')
        self.space_key_entry = create_label_entry('Space Key', 4, 'space_key')
        self.root_page_id_entry = create_label_entry('Root Page ID', 5, 'root_page_id')
        self.label_entry = create_label_entry('Include Label' if self.title.lower().startswith('source') else "Automation Label", 6, 'label')

        ttk.Label(frame, text="Exclude IDs:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        self.exclude_ids_entry = ttk.Entry(frame, width=50)
        self.exclude_ids_entry.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        self.exclude_ids_entry.insert(0, ', '.join(map(str, self.config.get('exclude_ids', []))))

        # Fetch Pages Limit
        ttk.Label(frame, text="Fetch Pages Limit:").grid(row=8, column=0, sticky="e", padx=5, pady=5)
        self.fetch_pages_limit_entry = ttk.Entry(frame, width=50)
        self.fetch_pages_limit_entry.insert(0, self.config.get('fetch_pages_limit', ''))
        self.fetch_pages_limit_entry.grid(row=8, column=1, padx=5, pady=5)

        # Fetch Attachments Limit
        ttk.Label(frame, text="Fetch Attachments Limit:").grid(row=9, column=0, sticky="e", padx=5, pady=5)
        self.fetch_attachments_limit_entry = ttk.Entry(frame, width=50)
        self.fetch_attachments_limit_entry.insert(0, self.config.get('fetch_attachments_limit', ''))
        self.fetch_attachments_limit_entry.grid(row=9, column=1, padx=5, pady=5)

        # Credentials Section
        ttk.Label(frame, text="Email:").grid(row=10, column=0, sticky="e", padx=5, pady=5)
        self.email_entry = ttk.Entry(frame, width=50)
        self.email_entry.grid(row=10, column=1, padx=5, pady=5, sticky="w")
        self.email_entry.insert(0, self.config['credentials']['email'])
        self.email_error_label = create_error_label(10)

        # Password
        ttk.Label(frame, text="Password:").grid(row=11, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = ttk.Entry(frame, width=50, show="*" if not self.config['credentials']['show_password'] else "")
        self.password_entry.grid(row=11, column=1, padx=5, pady=5, sticky="w")
        self.password_entry.insert(0, self.config['credentials']['password'])
        self.show_password_checkbox_var = tk.BooleanVar(value=self.config['credentials']['show_password'])
        self.show_password_checkbox = ttk.Checkbutton(frame, text="Show Password", variable=self.show_password_checkbox_var, command=self.toggle_password_visibility)
        self.show_password_checkbox.grid(row=12, column=1, padx=5, pady=5, sticky="w")

        # MFA Secret Key
        ttk.Label(frame, text="MFA Secret Key:").grid(row=13, column=0, sticky="e", padx=5, pady=5)
        self.mfa_entry = ttk.Entry(frame, width=50)
        self.mfa_entry.grid(row=13, column=1, padx=5, pady=5, sticky="w")
        self.mfa_entry.insert(0, self.config['credentials']['mfa_secret_key'])
        self.mfa_entry.config(state='normal' if self.config['credentials']['mfa_enabled'] else 'disabled')
        self.mfa_checkbox_var = tk.BooleanVar(value=self.config['credentials']['mfa_enabled'])
        self.mfa_checkbox = ttk.Checkbutton(frame, text="Enable MFA", variable=self.mfa_checkbox_var, command=self.update_mfa_visibility)
        self.mfa_checkbox.grid(row=14, column=1, padx=5, pady=5, sticky="nsew")

        # REST Auth Type
        ttk.Label(frame, text="REST Auth Type:").grid(row=15, column=0, sticky="e", padx=5, pady=5)
        self.rest_auth_type = tk.StringVar(value=self.config['credentials']['rest_auth_type'])
        self.rest_auth_type_combobox = ttk.Combobox(frame, textvariable=self.rest_auth_type, values=self.REST_AUTH_TYPES, state="readonly")
        self.rest_auth_type_combobox.grid(row=15, column=1, padx=5, pady=5, sticky="w")
        self.rest_auth_type_combobox.bind("<<ComboboxSelected>>", self.update_api_token_visibility)
        self.update_rest_auth_types()

        # API Token
        ttk.Label(frame, text="API Token:").grid(row=16, column=0, sticky="e", padx=5, pady=5)
        self.api_token_entry = ttk.Entry(frame, width=50)
        self.api_token_entry.grid(row=16, column=1, padx=5, pady=5, sticky="w")
        self.api_token_entry.insert(0, self.config['credentials']['api_token'])
        self.api_token_entry.config(state='normal' if self.rest_auth_type.get() == "header_auth" else 'disabled')

        # Save and Edit Buttons
        self.save_button = ttk.Button(frame, text="Save", command=self.save_config, state="disabled")
        self.save_button.grid(row=17, column=1, padx=5, pady=5, sticky="w")

        self.edit_button = ttk.Button(frame, text="Edit", command=self.enable_editing)
        self.edit_button.grid(row=17, column=0, padx=5, pady=5, sticky="e")

        self.set_edit_mode(False)


    def validate_fields(self):
        valid = True
        self.clear_error_labels()

        # Validate Name
        name = self.name_entry.get().strip()
        cleaned_name = re.sub(r'[^a-zA-Z0-9]', '', name)  # Remove special characters and spaces
        if not cleaned_name:
            self.name_error_label.config(text="Name is required.")
            valid = False

        # Validate Site URL
        site_url = self.site_entry.get().strip()
        if not site_url:
            self.site_error_label.config(text="Site URL is required.")
            valid = False
        elif not self.validate_url(site_url):
            self.site_error_label.config(text="Invalid URL format.")
            valid = False

        # Validate Path
        path = self.home_path_entry.get().strip()
        if not path:
            self.path_error_label.config(text="Path is required.")
            valid = False
        elif not self.validate_path(path):
            self.path_error_label.config(text="Invalid path format.")
            valid = False

        # Validate Space Key
        space_key = self.space_key_entry.get().strip()
        if not space_key or not space_key.isalnum():
            self.space_key_error_label.config(text="Space Key must be alphanumeric.")
            valid = False

        # Validate Root Page ID
        root_page_id = self.root_page_id_entry.get().strip()
        if not root_page_id or not root_page_id.isdigit():
            self.root_page_id_error_label.config(text="Root Page ID must be a multi-digit number.")
            valid = False

        # Validate Exclude IDs
        exclude_ids = self.exclude_ids_entry.get().strip()
        if exclude_ids and not self.validate_exclude_ids(exclude_ids):
            self.exclude_ids_error_label.config(text="Exclude IDs must be a list of digits separated by commas.")
            valid = False

        # Validate Email
        email = self.email_entry.get().strip()
        if not email:
            self.email_error_label.config(text="Email is required.")
            valid = False
        elif not self.validate_email(email):
            self.email_error_label.config(text="Invalid email format.")
            valid = False

        return valid

    def validate_url(self, url):
        # Regex for validating URL with a TLD
        url_regex = r"^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[\w\.-]*)?$"
        return re.match(url_regex, url) is not None

    def validate_path(self, path):
        # Regex for validating a path with optional query parameters
        path_regex = r"^/[\w/.-]*(?:\?[;\w=&]*)?$"
        return re.match(path_regex, path) is not None

    def validate_email(self, email):
        # Regex for validating email addresses
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    def validate_exclude_ids(self, exclude_ids):
        # Regex for validating a list of digits separated by commas
        exclude_ids_regex = r'^(\d+)(,\d+)*$'
        return re.match(exclude_ids_regex, exclude_ids) is not None

    def clear_error_labels(self):
        self.name_error_label.config(text="")
        self.site_error_label.config(text="")
        self.email_error_label.config(text="")

    def set_edit_mode(self, edit_mode):
        self.edit_mode = edit_mode
        state = "normal" if edit_mode else "disabled"
        self.save_button.config(state="normal" if edit_mode else "disabled")
        self.name_entry.config(state=state)
        self.confluence_type_combobox.config(state="readonly" if edit_mode else "disabled")
        self.site_entry.config(state=state)
        self.home_path_entry.config(state=state)
        self.space_key_entry.config(state=state)
        self.root_page_id_entry.config(state=state)
        self.label_entry.config(state=state)
        self.exclude_ids_entry.config(state=state)
        self.fetch_pages_limit_entry.config(state=state)
        self.fetch_attachments_limit_entry.config(state=state)
        self.email_entry.config(state=state)
        self.password_entry.config(state=state)
        self.show_password_checkbox.config(state=state)
        self.mfa_checkbox.config(state=state)
        self.mfa_entry.config(state=state if self.mfa_checkbox_var.get() else "disabled" )
        self.rest_auth_type_combobox.config(state="readonly" if edit_mode else "disabled")
        self.api_token_entry.config(state=state)

    def toggle_password_visibility(self):
        if self.show_password_checkbox_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def update_rest_auth_types(self):
        if self.confluence_type.get() == "cloud":
            filtered_rest_auth_types = [auth_type for auth_type in self.REST_AUTH_TYPES if auth_type != "cookies_auth"]
            self.rest_auth_type_combobox['values'] = filtered_rest_auth_types
            if self.rest_auth_type.get() == "cookies_auth":
                self.rest_auth_type.set(filtered_rest_auth_types[0])  # Set to a valid default if current selection is removed
        else:
            self.rest_auth_type_combobox['values'] = self.REST_AUTH_TYPES

    def update_api_token_visibility(self, *args):
        self.update_rest_auth_types()
        # If rest_auth_type is "header_auth", enable the API token field
        if self.rest_auth_type.get() == "header_auth":
            self.api_token_entry.config(state='normal')
        # If rest_auth_type is "basic_auth" AND confluence_type is "cloud", enable the API token field
        elif self.rest_auth_type.get() == "basic_auth" and self.confluence_type.get() == "cloud":
            self.api_token_entry.config(state='normal')
        # In all other cases, disable the API token field
        else:
            self.api_token_entry.config(state='disabled')

    def update_mfa_visibility(self, *args):
        if self.mfa_checkbox_var.get():
            self.mfa_entry.config(state='normal')
        else:
            self.mfa_entry.config(state='disabled')

    def get_selected_values(self):
        return {
            'name': self.name_entry.get(),
            'confluence_type': self.confluence_type.get(),
            'site_url': self.site_entry.get(),
            'home_path': self.home_path_entry.get(),
            'space_key': self.space_key_entry.get(),
            'root_page_id': self.root_page_id_entry.get(),
            'label': self.label_entry.get(),
            'exclude_ids': self.exclude_ids_entry.get().split(', '),
            'fetch_pages_limit':self.fetch_pages_limit_entry.get(),
            'fetch_attachments_limit':self.fetch_attachments_limit_entry.get(),
            'credentials':{
                "email": self.email_entry.get(),
                "password": self.password_entry.get(),
                "show_password": self.show_password_checkbox_var.get(),
                "mfa_enabled": self.mfa_checkbox_var.get(),
                "mfa_secret_key": self.mfa_entry.get(),
                "api_token": self.api_token_entry.get(),
                "rest_auth_type": self.rest_auth_type.get()
            }
        }

    def masked_config(self):
        config = self.get_selected_values()
        masked_config = {
            **config,
            'credentials': {
                **config['credentials'],
                'password': '*' * len(config['credentials']['password']) if config['credentials']['password'] else None,
                'mfa_secret_key': '*' * len(config['credentials']['mfa_secret_key']) if config['credentials']['mfa_secret_key'] else None
            }
        }
        return masked_config

    def save_config(self):
        if self.validate_fields():
            config = self.masked_config()
            logger.debug(f"{config.get('name','')} Config Saved: {config}")
            self.set_edit_mode(False)
            self.update_config()
        else:
            messagebox.showerror("Validation Error", "Please fix the errors in the form before saving.")

    def enable_editing(self):
        self.set_edit_mode(True)

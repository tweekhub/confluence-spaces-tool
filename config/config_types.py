from typing import Dict, Any
import re

class UIElement:
    def __init__(self, element_data: Dict[str, str]):
        self.element_type: str = element_data.get('element_type', '')
        self.selector_type: str = element_data.get('selector_type', '')
        self.selector_value: str = element_data.get('selector_value', '')
        self.action: str = element_data.get('action', '')
        self.post_action: str = element_data.get('post_action', '')

    def to_dict(self) -> Dict[str, str]:
        return {
            'element_type': self.element_type,
            'selector_type': self.selector_type,
            'selector_value': self.selector_value,
            'action': self.action,
            'post_action': self.post_action,
        }

class ConfluenceCredential:
    def __init__(self, config_data: Dict[str, str]):
        self.email: str = config_data.get('email', '')
        self.password: str = config_data.get('password', '')
        self.show_password: bool = config_data.get('show_password', False)
        self.mfa_enabled: bool = config_data.get('mfa_enabled', False)
        self.mfa_secret_key: str = config_data.get('mfa_secret_key', '')
        self.api_token: str = config_data.get('api_token', '')
        self.rest_auth_type: str = config_data.get('rest_auth_type', '')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'password': self.password,
            'show_password': self.show_password,
            'mfa_enabled': self.mfa_enabled,
            'mfa_secret_key': self.mfa_secret_key,
            'api_token': self.api_token,
            'rest_auth_type': self.rest_auth_type,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Update instance only if the new value differs from the current one."""
        if data.get('email') != self.email:
            self.email = data['email']
        if data.get('password') != self.password:
            self.password = data['password']
        if data.get('show_password') != self.show_password:
            self.show_password = data['show_password']
        if data.get('mfa_enabled') != self.mfa_enabled:
            self.mfa_enabled = data['mfa_enabled']
        if data.get('mfa_secret_key') != self.mfa_secret_key:
            self.mfa_secret_key = data['mfa_secret_key']
        if data.get('api_token') != self.api_token:
            self.api_token = data['api_token']
        if data.get('rest_auth_type') != self.rest_auth_type:
            self.rest_auth_type = data['rest_auth_type']

class ConfluenceInstance:
    def __init__(self, config_data: Dict[str, str]):
        self.name: str = config_data.get('name', '')
        self.confluence_type: str = self.validate_confluence_type(config_data.get('confluence_type', ''))
        self.site_url: str = config_data.get('site_url', '')
        self.home_path: str = config_data.get('home_path', '')
        self.space_key: str = config_data.get('space_key', '')
        self.root_page_id: str = config_data.get('root_page_id', '')
        self.label: str = config_data.get('label', '')
        self.exclude_ids: str = config_data.get('exclude_ids', [])
        self.fetch_pages_limit: int = config_data.get('fetch_pages_limit', '')
        self.fetch_attachments_limit: int = config_data.get('fetch_attachments_limit', '')
        self.credentials: ConfluenceCredential = ConfluenceCredential(config_data=config_data.get('credentials',{}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'confluence_type': self.validate_confluence_type(self.confluence_type),
            'site_url': self.site_url,
            'home_path': self.home_path,
            'space_key': self.space_key,
            'root_page_id': self.root_page_id,
            'label': self.label,
            'fetch_pages_limit':self.fetch_pages_limit,
            'fetch_attachments_limit':self.fetch_attachments_limit,
            'exclude_ids': self.exclude_ids,
            'credentials': self.credentials.to_dict(),  # Convert credentials to dict
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Update instance only if the new value differs from the current one."""
        if data.get('name') != self.name:
            self.name = data['name']
        if data.get('confluence_type') and self.validate_confluence_type(data['confluence_type']) != self.confluence_type:
            self.confluence_type = self.validate_confluence_type(data['confluence_type'])
        if data.get('site_url') != self.site_url:
            self.site_url = data['site_url']
        if data.get('home_path') != self.home_path:
            self.home_path = data['home_path']
        if data.get('space_key') != self.space_key:
            self.space_key = data['space_key']
        if data.get('root_page_id') != self.root_page_id:
            self.root_page_id = data['root_page_id']
        if data.get('label') != self.label:
            self.label = data['label']
        if data.get('exclude_ids') != self.exclude_ids:
            self.exclude_ids = data['exclude_ids']
        if data.get('fetch_pages_limit') != self.fetch_pages_limit:
            self.fetch_pages_limit = data['fetch_pages_limit']
        if data.get('fetch_attachments_limit') != self.fetch_attachments_limit:
            self.fetch_attachments_limit = data['fetch_attachments_limit']
        if 'credentials' in data:
            self.credentials.from_dict(data['credentials'])

    def validate_confluence_type(self, input_str: str) -> str:
        processed_str = re.sub(r'\W+', '', input_str).lower()
        if processed_str in ["confluenceserver", "server"]:
            return "server"
        elif processed_str in ["confluencecloud", "cloud"]:
            return "cloud"
        else:
            raise ValueError(f"Invalid Confluence type: {input_str}")
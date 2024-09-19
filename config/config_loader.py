from . import logger
import yaml
from pathlib import Path
import re
from config.config_types import UIElement, ConfluenceInstance
from typing import Dict, Any, List
import json

class ConfluenceConfig:
    def __init__(self, config_file: str,api_config_file:str,browser_config_file:str):
        self.config_data = self._load_config(config_file)
        self.browser_config_data = self._load_elements_config(browser_config_file)
        self.api_config_data = self._load_api_config(api_config_file)
        # Load source and target instances
        self.source_instance = self._load_confluence_instance(self.config_data.get('source'))
        self.target_instance = self._load_confluence_instance(self.config_data.get('target'))

    def _load_config(self, config_file: str) -> dict:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        with open(config_path, 'r') as file:
            try:
                config = yaml.safe_load(file)
                logger.debug(f"Successfully loaded configuration from {config_file}")
                return config
            except yaml.YAMLError as e:
                raise Exception(f"Error parsing YAML file: {e}")

    def _load_elements_config(self, config_file: str) -> Dict[str, Any]:
        try:
            with open(config_file, 'r') as f:
                config: Dict[str, Any] = json.load(f)
            logger.debug(f"Successfully loaded Browser config from {config_file}")
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"{config_file} file not found")
        except json.JSONDecodeError:
            raise json.JSONDecodeError(f"Error decoding {config_file}")

    def _load_api_config(self, config_file: str) -> Dict[str, Any]:
        try:
            with open(config_file, 'r') as f:
                config: Dict[str, Any] = json.load(f)
            logger.debug(f"Successfully loaded API Config from {config_file}")
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"{config_file} file not found")
        except json.JSONDecodeError:
            raise json.JSONDecodeError(f"Error decoding {config_file}")

    def _load_confluence_instance(self, instance_data: dict) -> ConfluenceInstance:
        """Helper method to load Confluence instance data from the config."""
        if not instance_data:
            raise ValueError("Missing Confluence instance data in the configuration.")
        logger.debug(f"Loading Confluence instance: {instance_data['name']}")
        return ConfluenceInstance(config_data=instance_data)

    def find_instance_by_key(self, key: str) -> ConfluenceInstance:
        """Finds an instance (source/target) by key."""
        valid_keys = ['source', 'target']
        if key not in valid_keys:
            raise ValueError(f"Invalid key '{key}'. Valid keys are: {valid_keys}")
        instance_data = self.config_data.get(key)
        if not instance_data:
            raise ValueError(f"No instance data found for key '{key}' in the configuration.")

        # logger.debug(f"Found instance for key '{key}': {instance_data['name']}")
        return ConfluenceInstance(config_data=instance_data)

    def get_auth_credentials(self, instance_key: str) -> dict:
        """Returns the authentication credentials based on the instance's authentication type."""
        instance = self.find_instance_by_key(instance_key)
        credentials = instance.credentials

        if credentials.rest_auth_type == 'basic_auth':
            return {
                'username': credentials.email,
                'password': credentials.api_token if instance.confluence_type == 'cloud' else credentials.password
            }
        elif credentials.rest_auth_type == 'cookies_auth':
            return {
                'username': credentials.email,
                'password': credentials.password,
                'mfa_enabled': credentials.mfa_enabled,
                'mfa_secret_key': credentials.mfa_secret_key
            }
        elif credentials.rest_auth_type == 'header_auth':
            return {
                'username': credentials.email,
                'api_token': credentials.api_token
            }
        else:
            raise ValueError(f"Unsupported authentication method: {credentials.rest_auth_type}")

    def get_elements_list(self, instance_type: str, page_type: str) -> List[UIElement]:
        """Returns a list of UI elements for a specific instance and page type."""
        try:
            elements_data = self.browser_config_data['confluence'][instance_type][page_type]
        except KeyError:
            logger.warning(f"No elements found for page type '{page_type}' in instance '{instance_type}'")
            return []
        ui_elements = []
        for element_data in elements_data:
            try:
                ui_element = UIElement(element_data)
                ui_elements.append(ui_element)
            except KeyError as e:
                logger.error(f"Missing required key in element data: {e}")
        return ui_elements

    def get_element(self, instance_type: str, page_type: str, element_type: str) -> UIElement:
        """Fetch a specific UI element by type."""
        try:
            elements_data = self.browser_config_data['confluence'][instance_type][page_type]
        except KeyError:
            logger.warning(f"No elements found for page type '{page_type}' in instance '{instance_type}'")
            return None
        for element_data in elements_data:
            if element_data['element_type'] == element_type:
                return UIElement(element_data)
        return None

    def get_endpoint(self, instance_type: str, category: str, action: str, api_version: str = "v1") -> str:
        """Returns the API endpoint based on instance type, category, and action."""
        return self.api_config_data.get(instance_type, {}).get(api_version, {}).get(category, {}).get(action, '')


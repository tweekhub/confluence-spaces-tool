from . import logger
import yaml
from pathlib import Path
from config.config_types import UIElement, ConfluenceInstance
from typing import Dict, Any, List, Optional
import json

class ConfluenceConfig:
    def __init__(self, config_file: str,api_config_file:str,browser_config_file:str):
        self.config_file = config_file
        self.config_data = self._load_config(self.config_file)
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
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    def _load_elements_config(self, config_file: str) -> Dict[str, Any]:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        with open(config_path, 'r') as file:
            try:
                config: Dict[str, Any] = json.load(file)
                logger.debug(f"Successfully loaded Browser config from {config_file}")
                return config
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Error decoding JSON file: {e}")

    def _load_api_config(self, config_file: str) -> Dict[str, Any]:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        with open(config_path, 'r') as file:
            try:
                config: Dict[str, Any] = json.load(file)
                logger.debug(f"Successfully loaded API Config from {config_file}")
                return config
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Error decoding JSON file: {e}")

    def _load_confluence_instance(self, instance_data: dict):
        if not instance_data:
            raise ValueError("Missing Confluence instance data in the configuration.")
        logger.debug(f"Loading Confluence instance: {instance_data['name']}")
        return ConfluenceInstance(config_data=instance_data)
    
    def find_instance_by_key(self, key: str):
        valid_keys = ['source', 'target']
        if key not in valid_keys:
            raise ValueError(f"Invalid key '{key}'. Valid keys are: {valid_keys}")
        instance_data = self.config_data.get(key)
        if not instance_data:
            raise ValueError(f"No instance data found for key '{key}' in the configuration.")
        return ConfluenceInstance(config_data=instance_data)

    def get_auth_credentials(self, instance_key: str):
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
        try:
            elements_data = self.browser_config_data['confluence'][instance_type][page_type]
        except KeyError:
            logger.warning(f"No elements found for page type '{page_type}' in instance '{instance_type}'")
            return UIElement({"element_type": "default", "name": "default_element"})
        for element_data in elements_data:
            if element_data['element_type'] == element_type:
                return UIElement(element_data)
        return UIElement({"element_type": "default", "name": "default_element"})

    def get_endpoint(self, instance_type: str, category: str, action: str, api_version: str = "v1") -> str:
        return self.api_config_data.get(instance_type, {}).get(api_version, {}).get(category, {}).get(action, '')

    def update_config(self, updated_config: Dict[str, Any]) -> None:
        if not isinstance(updated_config, dict):
            raise ValueError("updated_config must be a dictionary")

        self.config_data = self._merge_dicts(self.config_data, updated_config)
        
        with open(self.config_file, 'w') as file:
            try:
                yaml.dump(self.config_data, file, default_flow_style=False, sort_keys=False)
                logger.debug(f"Configuration successfully updated and written to {self.config_file}")
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error writing updated configuration to YAML file: {e}")

    def _merge_dicts(self, original: dict, updates: dict) -> dict:
        for key, value in updates.items():
            if isinstance(value, dict) and key in original:
                original[key] = self._merge_dicts(original[key], value)
            else:
                original[key] = value
        return original

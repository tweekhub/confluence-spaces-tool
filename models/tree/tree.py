from typing import List, Optional
from .page_node import ConfluencePageNode
from .attachment_node import ConfluenceAttachmentNode
from api.client import ConfluenceAPIClient
from . import logger
import json

class ConfluencePagesTree:
    def __init__(self, root: 'ConfluencePageNode', api_client: 'ConfluenceAPIClient'):
        self.root = root
        self.api_client = api_client
        self.tree_file = f"tree_{self.api_client.instance_config.name}_{self.api_client.instance_config.root_page_id}.txt"
        self.tree_file_json = f"tree_{self.api_client.instance_config.name}_{self.api_client.instance_config.root_page_id}.json"
        self.logs_prefix = f"{self.api_client.instance_config.name} {self.api_client.instance_config.confluence_type}> "
        self.total_nodes = 0 

    def _print_node(self, node: 'ConfluencePageNode', level: int, to_file: bool = False):
        indent = "    " * level
        info_str = f"{indent}- {node.title} (ID: {node.id}, Labels: {node.labels}, Children: {len(node.children)}, Macros: {set(node.macros)})"
        if to_file:
            with open(self.tree_file, "a") as file:
                file.write(info_str + "\n")
        else:
            logger.info(info_str)

    def print_pages(self, node: Optional['ConfluencePageNode'] = None, level: int = 0):
        current_node = node or self.root
        self._print_node(current_node, level)
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                self.print_pages(child, level + 1)

    def save_tree_to_file_as_json(self, node: Optional['ConfluencePageNode'] = None):
        current_node = node or self.root
        tree_dict = self._node_to_dict(current_node)
        with open(self.tree_file_json, "w") as file:
            json.dump(tree_dict, file, indent=4)

    def _node_to_dict(self, node: 'ConfluencePageNode'):
        return {
            "title": node.title,
            "id": node.id,
            "labels": node.labels,
            "attachments": [attachment.id for attachment in node.child_attachments],
            "children": [self._node_to_dict(child) for child in node.children],
            "macros": list(set(node.macros))
        }

    def traverse_tree(self, node: Optional['ConfluencePageNode'] = None) -> List['ConfluencePageNode']:
        current_node = node or self.root
        nodes = [current_node]
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                nodes.extend(self.traverse_tree(child))
        return nodes

    def rearrange_trees(self, target_node: 'ConfluencePageNode', node: Optional['ConfluencePageNode'] = None):
        current_node = node or self.root
        target_children = {child.title: child for child in target_node.children if isinstance(child, ConfluencePageNode)}
        new_children = []

        for original_child in current_node.children:
            if isinstance(original_child, ConfluencePageNode):
                if original_child.title in target_children:
                    new_children.append(target_children[original_child.title])
                    self.rearrange_trees(target_children[original_child.title], original_child)
                else:
                    logger.warning(f"{self.logs_prefix} Warning: No matching node found in target tree for '{original_child.title}'")

        target_node.children = [child for child in target_node.children if not isinstance(child, ConfluencePageNode)] + new_children

    def fetch_pages(self, node: Optional['ConfluencePageNode'] = None, confluence_type: str = '', from_label: str = "", exclude_page_ids: list = []):
        current_node = node or self.root
        logger.debug(f"Fetching pages for node: {current_node.title}, excluding pages with IDs: {exclude_page_ids}")
        
        child_pages = self.api_client.get_child_pages(current_node.id)
        
        for page_data in child_pages:
            page = ConfluencePageNode.from_api_response(page_data, confluence_type)

            if str(page.id) in map(str, exclude_page_ids):
                logger.warning(f"Skipping page {page.title} (ID: {page.id}) with all sub pages, due to exclude_page_id match")
                continue
            
            if from_label and (not page.labels or from_label not in page.labels):
                logger.warning(f"Skipping page {page.title} (ID: {page.id}) with all sub pages, due to label filtering")
                continue

            page.labels = [label['name'] for label in self.api_client.get_labels(page.id)]
            logger.debug(f"Adding page {page.title} (ID: {page.id}) with labels: {page.labels}")
            page.set_body(self.api_client.get_content(page.id).json().get("body",{}).get("storage",{}).get("value",""))
            page.macros = page.get_macros_list()
            current_node.add_child(page)
            self.fetch_pages(page, confluence_type, from_label, exclude_page_ids)

    def fetch_attachments(self, node: Optional['ConfluencePageNode'] = None):
        current_node = node or self.root
        logger.debug(f"Fetching attachments for node: {current_node.title}")
        response = self.api_client.get_content(current_node.id)
        
        for attachment_data in response.json()['children']['attachment']['results']:
            attachment = ConfluenceAttachmentNode.from_api_response(attachment_data)
            current_node.add_child_attachment(attachment)
            logger.debug(f"{self.logs_prefix} Added attachment: {attachment.title}")

    def build_tree(self, confluence_type: str, from_label: str = "", exclude_page_ids: list = []):
        logger.info(f"{self.logs_prefix} Building the Confluence pages tree...")
        root_page_data = self.api_client.get_content(self.root.id)  # Ensure root is a valid ConfluencePageNode
        self.root = ConfluencePageNode.from_api_response(root_page_data.json(), confluence_type)  # Convert to ConfluencePageNode
        self.fetch_pages(confluence_type=confluence_type, from_label=from_label, exclude_page_ids=exclude_page_ids)
        
        logger.info(f"{self.logs_prefix} ConfluencePagesTree with root {self.root.title} with total of {self.total_nodes} nodes is ready...")

    def count_children(self, node: ConfluencePageNode = None) -> int:
        current_node = node or self.root
        count = len(current_node.children)
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                count += self.count_children(child)
        return count
    
    def fetch_total_nodes(self) -> int:
        self.total_nodes = 0
        child_nodes = self.count_children()
        self.total_nodes += child_nodes + 1
        return self.total_nodes
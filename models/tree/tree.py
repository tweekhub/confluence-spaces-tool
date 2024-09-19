from typing import List, Optional
from .page_node import ConfluencePageNode
from .attachment_node import ConfluenceAttachmentNode
from api.client import ConfluenceAPIClient
from . import logger
import re
import json

class ConfluencePagesTree:
    def __init__(self, root: ConfluencePageNode, api_client: ConfluenceAPIClient):
        self.root = root
        self.api_client = api_client
        self.tree_file = f"tree_{self.api_client.instance_config.name}_{self.api_client.instance_config.root_page_id}.txt"
        self.tree_file_json = f"tree_{self.api_client.instance_config.name}_{self.api_client.instance_config.root_page_id}.json"
        logger.debug(f"Initialized ConfluencePagesTree with root node: {root.title}")

    def print_pages(self, node: Optional[ConfluencePageNode] = None, level: int = 0):
        current_node = node or self.root
        indent = "    " * level
        logger.info(f"{indent}- {current_node.title} (ID: {current_node.id}, Labels: {current_node.labels}, Children: {len(current_node.child_pages)}, Macros: {set(current_node.macros)})")
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                self.print_pages(child, level + 1)

    def print_pages_to_file(self, node: Optional[ConfluencePageNode] = None, level: int = 0):
        current_node = node or self.root
        indent = "    " * level
        with open(self.tree_file, "a") as file:
            file.write(f"{indent}- {current_node.title} (ID: {current_node.id}, Labels: {current_node.labels}, Children: {len(current_node.child_pages)}, Macros: {set(current_node.macros)})\n")
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                self.print_pages_to_file(child, level + 1)
        
    def save_tree_to_file_as_json(self, node: Optional[ConfluencePageNode] = None):
        current_node = node or self.root
        def node_to_dict(node: ConfluencePageNode):
            return {
                "title": node.title,
                "id": node.id,
                "labels": node.labels,
                "attachments": [attachment.id for attachment in node.child_attachments],
                "children": [node_to_dict(child) for child in node.children],
                "macros": list(set(node.macros))
            }
        tree_dict = node_to_dict(current_node)
        with open(self.tree_file_json, "w") as file:
            json.dump(tree_dict, file, indent=4)

    def traverse_tree(self, node: Optional[ConfluencePageNode] = None) -> List[ConfluencePageNode]:
        current_node = node or self.root
        nodes = [current_node]
        for child in current_node.children:
            if isinstance(child, ConfluencePageNode):
                nodes.extend(self.traverse_tree(child))
        return nodes

    def rearrange_trees(self, target_node: ConfluencePageNode, node: Optional[ConfluencePageNode] = None):
        try:
            current_node = node or self.root
            target_children = {child.title: child for child in target_node.children if isinstance(child, ConfluencePageNode)}
            new_target_children = []
            for original_child in current_node.children:
                if isinstance(original_child, ConfluencePageNode):
                    title = original_child.title
                    if title in target_children:
                        new_target_children.append(target_children[title])
                        self.rearrange_trees(target_children[title], original_child)
                    else:
                        logger.warning(f"Warning: No matching node found in target tree for '{title}'")
            target_node.children = [child for child in target_node.children if not isinstance(child, ConfluencePageNode)] + new_target_children
        except Exception as e:
            logger.error(f"Error in rearrange_trees: {str(e)}")
            raise

    def fetch_pages(self, node: Optional[ConfluencePageNode] = None, confluence_type: str = '', from_label: str = "", exclude_page_ids: list = []):
        current_node = node or self.root
        logger.debug(f"Fetching pages for node: {current_node.title}, excluding pages with IDs: {exclude_page_ids[0]}")

        child_pages = self.api_client.get_child_pages(current_node.id)
        current_node.child_pages = child_pages
        for page_data in child_pages:
            page = ConfluencePageNode.from_api_response(page_data, confluence_type)
            response = self.api_client.get_content(page.id)
            page.set_body(response.json()['body']['storage']['value'])
            # self.fetch_attachments(page)

            # Skip the page if it's in the exclude_page_ids list
            if str(page.id) in exclude_page_ids:
                logger.warning(f"Skipping page {page.title} (ID: {page.id}) and its children due to exclude_page_id match")
                continue  # Skip this page and its children but continue processing siblings

            # Fetch and assign labels
            page.labels = [label['name'] for label in self.api_client.get_labels(page.id)]

            # Apply label-based filtering if 'from_label' is provided
            if from_label:
                if not page.labels:
                    logger.warning(f"Skipping page {page.title} (ID: {page.id}) as it has no labels")
                    continue

                if from_label not in page.labels:
                    logger.warning(f"Skipping page {page.title} (ID: {page.id}) due to missing label: {from_label}")
                    continue

            # Log page details and add it to the current node
            logger.debug(f"Adding page {page.title} (ID: {page.id}) with labels: {page.labels}")
            current_node.add_child(page)

            # Recursively fetch child pages of this page (only if it's not excluded)
            self.fetch_pages(page, confluence_type, from_label, exclude_page_ids)

    def fetch_attachments(self, node: Optional[ConfluencePageNode] = None):
        current_node = node or self.root
        logger.debug(f"Fetching attachments for node: {current_node.title}")
        response = self.api_client.get_content(current_node.id)
        for attachment_data in response.json()['children']['attachment']['results']:
            attachment = ConfluenceAttachmentNode.from_api_response(attachment_data)
            current_node.add_child_attachment(attachment)
            # logger.debug(f"Added attachment: {attachment.title}")

    def build_tree(self, confluence_type: str, from_label: str = "", exclude_page_ids: list = []):
        logger.info("Building the Confluence pages tree...")
        self.fetch_pages(confluence_type=confluence_type, from_label=from_label, exclude_page_ids=exclude_page_ids)

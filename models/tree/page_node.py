import re
from urllib.parse import urlparse, urlunparse
from typing import List, Optional
from . import logger
from . import logger

class ConfluencePageNode:
    def __init__(self, page_id: str, title: str, page_type: str="", status: str="", edit_link: str="", webui_link: str="", 
                 labels: Optional[List[str]] = None, child_pages: Optional[List[dict]] = None, 
                 child_attachments: Optional[List['ConfluenceAttachmentNode']] = None, parent: Optional['ConfluencePage'] = None):
        self.id = int(page_id)
        self.type = page_type
        self.status = status
        self.title = title
        self.labels = labels or []
        self.child_pages = child_pages or []
        self.child_attachments = child_attachments or []
        self.webui_link = webui_link
        self.edit_link = edit_link
        self.parent = parent
        self.body: Optional[str] = None
        self.macros: List[str] = []
        self.children = []
        self.parent = parent
        
    def add_child(self, child):
        self.children.append(child)
    
    def remove_child(self, child):
        self.children.remove(child)

    def add_parent(self, parent):
        self.parent = parent
    
    def remove_parent(self):
        self.parent = None

    def __str__(self) -> str:
        return f"ConfluencePage(id={self.id}, title={self.title})"

    def __repr__(self) -> str:
        return self.__str__()

    def add_child_page(self, child_page: 'ConfluencePage') -> None:
        self.child_pages.append(child_page)

    def add_child_attachment(self, child_attachment: dict) -> None:
        self.child_attachments.append(child_attachment)

    def set_body(self, body: str) -> None:
        self.body = body
        self.macros = self._get_macros_list()
    
    @classmethod
    def from_api_response(cls, response: dict, confluence_type: str) -> 'ConfluencePageNode':
        page = cls(
            page_id=str(response['id']),
            page_type=response['type'],
            status=response['status'],
            title=response['title'],
            edit_link=response['_links']['editui'] if confluence_type == 'cloud' else response['_links']['edit'],
            webui_link=response['_links']['webui']
        )

        # if 'metadata' in response and 'labels' in response['metadata']:
        #     page.labels = [label['name'] for label in response['metadata']['labels'].get('results', [])]
        
        # if 'children' in response:
        #     if 'page' in response['children']:
        #         page.child_pages = [cls.from_api_response(child, confluence_type) for child in response['children']['page'].get('results', [])]
        #     if 'attachment' in response['children']:
        #         page.child_attachments = response['children']['attachment'].get('results', [])
        
        return page
    
    @classmethod
    def from_api_responses(cls, responses: List[dict], confluence_type: str) -> List['ConfluencePageNode']:
        return [cls.from_api_response(response, confluence_type) for response in responses]
    
    def _get_macros_list(self) -> List[str]:
        if not self.body:
            return []
        pattern = r'ac:name=\"(.*?)\"'
        return re.findall(pattern, self.body)

    def replace_body(self, source_domain, target_domain, new_width=550, id_mapping=None) -> str:
        if self.body is None:
            raise ValueError("Body is missing")
        
        # Ensure the source and target domains have no trailing slashes
        source_domain = source_domain.rstrip('/')
        target_domain = target_domain.rstrip('/')

        # Define regex pattern to match URLs with source domain and capture the path, ID (if any), and remove query params
        url_pattern = re.escape('https://' + source_domain) + r'(/(?:download/attachments|rest/documentConversion|plugins/servlet/confluence)/([^"?]+))(?:\?[^"]*)?'

        def replace_url(match):
            url_path = match.group(1)
            # Check if the ID is in the second capture group (only for download/attachments)
            old_id = match.group(2).split('/')[0] if 'download/attachments' in url_path else None

            # Replace the ID if a mapping is provided, only for /download/attachments paths
            if old_id and id_mapping and old_id in id_mapping:
                new_id = id_mapping[old_id]
                url_path = url_path.replace(old_id, new_id)

            # Construct the new URL, replacing the domain and ID, and removing query parameters
            return f'https://{target_domain}{url_path}'

        # Replace all URLs with target domain, updated ID (if provided), and remove query params
        modified_html = re.sub(url_pattern, replace_url, str(self.body))

        # Replace all image widths with new width (550 in this case)
        width_pattern = r'ac:width="\d+"'
        width_replacement = f'ac:width="{new_width}"'
        modified_html = re.sub(width_pattern, width_replacement, modified_html)

        return modified_html

    def replace_body(self, source_url: str, target_url: str) -> str:
        if self.body is None:
            raise ValueError("Body is missing")
        
        # Extract domain from source_url
        domain_pattern = r'https://([a-zA-Z0-9.-]+)'
        match = re.match(domain_pattern, source_url)
        if not match:
            raise ValueError("Invalid source_url format")
        
        domain = match.group(1)
        
        # Define the regex pattern to match the URL and capture parts
        pattern = rf'https://{re.escape(domain)}/download/attachments/(\d+)/([^"?]+)(?:\?[^"]*)?'
        
        # Define the replacement pattern, replacing domain and URL with target_url
        replacement = fr'https://{re.escape(target_url)}/wiki/download/attachments/{self.id}/\2'
        
        # Use re.sub to replace all occurrences of the URL pattern with the new format
        modified_html = str(self.body).replace(pattern,replacement)

        # Replace width attribute
        width_pattern = r'ac:width="250"'
        width_replacement = r'ac:width="450"'
        
        modified_size = modified_html.replace(width_pattern, width_replacement)
        
        return modified_size

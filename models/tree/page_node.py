import re
from typing import List, Optional
from . import logger

class ConfluencePageNode:
    def __init__(self, page_id: str, title: str, page_type: str = "", status: str = "", edit_link: str = "", webui_link: str = "", 
                 labels: Optional[List[str]] = None, child_pages: Optional[List[dict]] = None, 
                 child_attachments: Optional[List['ConfluenceAttachmentNode']] = None, parent: Optional['ConfluencePageNode'] = None):
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

    def add_child(self, child: 'ConfluencePageNode'):
        self.children.append(child)

    def add_child_attachment(self, child_attachment: 'ConfluenceAttachmentNode'):
        self.child_attachments.append(child_attachment)

    def set_body(self, body: str):
        self.body = body
        self.macros = self._get_macros_list()

    @classmethod
    def from_api_response(cls, response: dict, confluence_type: str) -> 'ConfluencePageNode':
        return cls(
            page_id=str(response['id']),
            page_type=response['type'],
            status=response['status'],
            title=response['title'],
            edit_link=response['_links']['editui'] if confluence_type == 'cloud' else response['_links']['edit'],
            webui_link=response['_links']['webui']
        )

    def _get_macros_list(self) -> List[str]:
        if not self.body:
            return []
        return re.findall(r'ac:name="(.*?)"', self.body)

import re
from urllib.parse import urlparse, urlunparse
from typing import List, Optional
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
        return page
    
    @classmethod
    def from_api_responses(cls, responses: List[dict], confluence_type: str) -> List['ConfluencePageNode']:
        return [cls.from_api_response(response, confluence_type) for response in responses]
    
    def _get_macros_list(self) -> List[str]:
        if not self.body:
            return []
        pattern = r'ac:name=\"(.*?)\"'
        return re.findall(pattern, self.body)

    def update_macros(self)->str:
        if self.body is None:
            logger.error("Body is missing")
        logger.debug("Starting to update macros in the body.")
        # Regex pattern to handle <ac:image> tags with various attributes
        image_macros_pattern = re.compile(
            r'<ac:image[^>]*ac:src="([^"]+)"[^>]*?(?:ac:original-width="([^"]+)"[^>]*?)?(?:ac:original-height="([^"]+)"[^>]*?)?(?:ac:width="([^"]+)"[^>]*?)?(?:ac:height="([^"]+)"[^>]*?)?[^>]*?>'
        )
        # Regex pattern to handle <ac:emoticon> tags
        emoticon_macros_pattern = re.compile(
            r'<ac:emoticon[^>]*ac:name="([^"]+)"[^>]*?ac:emoji-shortname="([^"]+)"[^>]*?ac:emoji-id="([^"]+)"[^>]*?ac:emoji-fallback="([^"]+)"[^>]*?/>'
        )
        # Replace <ac:image> tags
        updated_html = re.sub(image_macros_pattern, self._replace_image_tag, self.body)
        # Replace <ac:emoticon> tags (if needed)
        updated_html = re.sub(emoticon_macros_pattern, self._replace_emoticon_tag, updated_html)
        self.set_body(updated_html)
        
        logger.debug("Completed updating macros in the body.")
        return updated_html

    def _replace_image_tag(self, match):
        ac_src = match.group(1)  # Extract the ac:src value (URL)
        ac_original_width = match.group(2)  # Extract the ac:original-width value, if available
        ac_original_height = match.group(3)  # Extract the ac:original-height value, if available
        ac_width = match.group(4)  # Extract the ac:width value, if available
        ac_height = match.group(5)  # Extract the ac:height value, if available

        # Use available width and height values
        width = ac_original_width if ac_original_width else ac_width
        height = ac_original_height if ac_original_height else ac_height

        # Extract the filename from the URL (everything after the last '/')
        filename = ac_src.split('/')[-1].split('?')[0]
        # Replacement string with the extracted filename, width, and height
        replacement = f'<ac:image ac:width="{width}" ac:height="{height}">\n<ri:attachment ri:filename="{filename}" />\n</ac:image>'
        logger.debug(f"Replaced image tag with filename: {filename}, width: {width}, height: {height}")

        return replacement

    def _replace_emoticon_tag(self, match):
        ac_name = match.group(1)
        ac_shortname = match.group(2)
        ac_emoji_id = match.group(3)
        ac_fallback = match.group(4)

        # If needed, you can handle emoticons differently or just leave them unchanged
        replacement = f'<ac:emoticon ac:name="{ac_name}" ac:emoji-shortname="{ac_shortname}" ac:emoji-id="{ac_emoji_id}" ac:emoji-fallback="{ac_fallback}" />'
        logger.debug(f"Replaced emoticon tag with name: {ac_name}, shortname: {ac_shortname}, id: {ac_emoji_id}, fallback: {ac_fallback}")

        return replacement

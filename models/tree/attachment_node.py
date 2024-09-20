# No imports needed

class ConfluenceAttachmentNode:
    def __init__(self, id: str, type: str, status: str, title: str, mediatype: str, file_size: int = 0,
                 media_type_description: str = "", download_link: str = "", webui_link: str = ""):
        self.id = id
        self.type = type
        self.status = status
        self.title = title
        self.mediatype = mediatype
        self.file_size = file_size
        self.media_type_description = media_type_description
        self.download_link = download_link
        self.webui_link = webui_link

    @classmethod
    def from_api_response(cls, response: dict) -> 'ConfluenceAttachmentNode':
        return cls(
            id=response['id'],
            type=response['type'],
            status=response['status'],
            title=response['title'],
            mediatype=response['metadata']['mediaType'],
            file_size=response['extensions'].get('fileSize', 0),
            media_type_description=response['extensions'].get('mediaTypeDescription', ''),
            download_link=response['_links'].get('download', ''),
            webui_link=response['_links'].get('webui', ''),
        )

    def __str__(self) -> str:
        return f
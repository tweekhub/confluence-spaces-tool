from . import logger
from config.config_types import ConfluenceInstance
from requests.auth import HTTPBasicAuth
from selenium import webdriver
import requests
import re
import json
import os
from pathlib import Path
import urllib.parse
import base64

class ConfluenceAPIClient:
    def __init__(self, instance_config: ConfluenceInstance,api_config:dict):
        self.instance_config = instance_config
        self.api_config = api_config
        self.current_user_memberships = []
        self.session = requests.Session()
        self.total_success = 0
        self.total_failed = 0
        self.total_requests = 0
        self.total_pages_created = 0
        self.total_attachments_created = 0
        self.total_pdfs_download = 0
        self.total_attachments_download = 0
        self.total_docs_download = 0
        self.use_v2_for_cloud = "v2" if self.instance_config.confluence_type == "cloud" else "v1"
        self.rest_api_path = "/wiki/rest/api/content" if self.instance_config.confluence_type == "cloud" else "/rest/api/content"
        self.logs_prefix = f"{self.instance_config.name} {self.instance_config.confluence_type}>"

    def get_endpoint(self, category: str, action: str, api_version: str = "v1") -> str:
        return self.api_config.get(self.instance_config.confluence_type, {}).get(api_version, {}).get(category, {}).get(action, '')

    def requests_stats(self):
        logger.info(f"{self.logs_prefix} Total requests: {self.total_requests}, Total success: {self.total_success}, Total failed: {self.total_failed}")
        logger.info(f"{self.logs_prefix} Success rate: {self.total_success / self.total_requests * 100:.2f}%")
    
    def update_request_stats(self,is_successful: bool=True,created_attachment: bool=False,created_page: bool=False,download_pdf:bool=False,download_doc:bool=False,download_attachment:bool=False):
        if created_page:
            self.total_pages_created +=1
        if created_attachment:
            self.total_attachments_created += 1
        if download_pdf:
            self.total_pdfs_download +=1
        if download_doc:
            self.total_docs_download +=1
        if download_attachment:
            self.total_attachments_download +=1
        if is_successful:
            self.total_success += 1
        else:
            self.total_failed += 1
        self.total_requests += 1

    def initialize_session(self,cookies:list=[]):
        self.session = requests.Session()
        self.session.headers.update({'X-Atlassian-Token': 'no-check','Accept': 'application/json'})

        auth_type = self.instance_config.credentials.rest_auth_type
        confluence_type = self.instance_config.confluence_type
        email = self.instance_config.credentials.email
        api_token = self.instance_config.credentials.api_token
        password = self.instance_config.credentials.password

        if auth_type == 'basic_auth':
            self.session.auth = HTTPBasicAuth(email,api_token if confluence_type == "cloud" else password)
            logger.debug(f"{self.logs_prefix} Using Basic Authentication username: {email}")
        elif auth_type == 'cookies_auth':
            for cookie in cookies:
                self.session.cookies.set(name=cookie.get('name', ''),value=cookie.get('value', ''),domain=cookie.get('domain', ''),path=cookie.get('path', '/'),secure=cookie.get('secure', False))
            logger.debug(f"{self.logs_prefix} Using {len(cookies)} Cookies from Browser to requests session.")
        elif auth_type == 'header_auth':
            if confluence_type == "cloud":
                # Encode email and API token for Confluence Cloud
                credentials = f"{email}:{api_token}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                self.session.headers.update({'Authorization': f"Basic {encoded_credentials}"})
            else:
                # Encode email and API token for Confluence Server
                self.session.headers.update({'Authorization': f"Bearer {api_token}"})
            logger.debug(f"{self.logs_prefix} Using Authorization header: {'*' * len(self.session.headers.get('Authorization', ''))}")
        else:
            raise ValueError(f"{self.logs_prefix} Invalid Authentication Method: {auth_type}")

    def api_request(self, method, category, action, api_version="v1", **kwargs):
        url = self.build_url(category, action, api_version, kwargs.get('path_params', {}))
        request_kwargs = self.build_request_kwargs(kwargs)

        logger.debug(f"{self.logs_prefix} HTTP_REQ {method} URL: {url} {str(request_kwargs)[:150]}")
        response = self.session.request(method, url, **request_kwargs)

        self.handle_response(response, category, action)

        return response

    def build_url(self, category, action, api_version, path_params):
        url = f"{self.instance_config.site_url}{self.get_endpoint(category, action, api_version)}"
        for key, value in path_params.items():
            url = url.replace(f"{{{key}}}", str(value))
        return url

    def build_request_kwargs(self, kwargs):
        request_kwargs = {}
        if 'data' in kwargs:
            request_kwargs['json'] = kwargs['data']
        if 'params' in kwargs:
            request_kwargs['params'] = kwargs['params']
        if 'files' in kwargs:
            request_kwargs['files'] = kwargs['files']
        if 'allow_redirects' in kwargs:
            request_kwargs['allow_redirects'] = kwargs['allow_redirects']
        return request_kwargs

    def handle_response(self, response, category, action):
        if response.status_code >= 200 and response.status_code < 300:
            self.update_request_stats(
                is_successful=True,
                created_page=(category == 'content' and action == 'create'),
                download_pdf=(category == 'export' and action == 'pdf'),
                download_doc=(category == 'export' and action == 'word'),
                download_attachment=(category == 'attachment' and action == 'download')
            )
            if action != "export":
                logger.debug(f"{self.logs_prefix} HTTP_RES {response.status_code} MESSAGE: {response.text[:150]}...")
        else:
            self.update_request_stats(is_successful=False)
            if action != "export":
                logger.warning(f"{self.logs_prefix} HTTP_RES {response.status_code} MESSAGE: {response.text[:250]}...")


    def get_space_id(self, space_key) -> dict:
        return self.api_request('GET', 'space', 'get', 'v1', path_params={'spaceKey': space_key}).json().get("id","")

    def get_content(self, content_id, expand=True) -> dict:
        params = {
            'limit': self.instance_config.fetch_pages_limit
        }
        if expand:
            params['expand'] = 'body.storage,children.attachment'
        return self.api_request('GET', 'content', 'get', 'v1', path_params={'contentId': content_id}, params=params)

    def get_page_title(self, content_id) -> dict:
        return self.api_request('GET', 'content', 'get', 'v1', path_params={'contentId': content_id}).json().get("title","")

    def get_page_id(self, title: str,space_key: str):
        params = {
            'title': title,
            'spaceKey': space_key
        }
        return self.api_request('GET','rest','base','v1', params=params).json().get("results",{})[0].get("id","")

    def create_content(self, data,space_key:str=None) -> dict:
        response = self.api_request('POST', 'content', 'create', self.use_v2_for_cloud, data=data)
        if response.status_code == 400:
            logger.warning(f"{self.logs_prefix} Error Creating Page '{data['title']}' Reason: {response.json()['errors'][0]['title']}")
            return self.get_page_id(title=data['title'],space_key=space_key)
        return response.json()['id']

    def get_content_version(self,content_id):
        return self.api_request('GET', 'content', 'get', self.use_v2_for_cloud, path_params={'contentId': content_id}).json().get("version",{}).get("number","")

    def update_content(self,content_id,content_title,body_data,confluence_type):
        body_field = {
            "storage": {
                "value": body_data,
                "representation": "storage"
            }
        } if confluence_type == 'server' else {
            "representation": "storage",
            "value": body_data
        }
        increment_version = self.get_content_version(content_id=content_id)
        increment_version += 1
        payload = {
            "id": content_id,
            "title": content_title,
            "status": "current",
            "body": body_field,
            "version": {
                "number": increment_version
            }
        }
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.api_request('PUT', 'content', 'update', self.use_v2_for_cloud, path_params={'contentId': content_id}, data=payload)
        self.session.headers.pop("Content-Type","")
        return response
 
    def get_labels(self, content_id):
        return self.api_request('GET', 'label', 'get', 'v1', path_params={'contentId': content_id}).json()['results']
    
    def add_labels(self, content_id, labels):
        data = [{"prefix":"global","name": label} for label in labels]
        return self.api_request('POST', 'label', 'add', 'v1', path_params={'contentId': content_id}, data=data)

    def add_automation_label(self, content_id:str,automation_label: str):
        data = [{"prefix":"global","name": automation_label}]
        return self.api_request('POST', 'label', 'add', 'v1', path_params={'contentId': content_id}, data=data)

    def get_child_pages(self, parent_id):
        params = {
            'limit': self.instance_config.fetch_pages_limit
        }
        return self.api_request('GET', 'child', 'get', 'v1', path_params={'parentId': parent_id}, params=params).json()['results']

    def get_attachments(self, content_id) -> dict:
        return self.api_request('GET','attachment','get','v1',path_params={'contentId':content_id})
    
    def get_user_groups(self):
        response = self.api_request('GET', 'user', 'groups', 'v1', params={'limit': '100'})
        self.current_user_memberships = [group['name'] for group in response.json()['results']]
        return self.current_user_memberships

    def get_page_restrictions(self, page_id):
        try:
            username = self.instance_config.credentials.email
            if username is None:
                raise ValueError(f"{self.logs_prefix} Cannot find username in {self.instance_config.preferred_auth}")
            
            response = self.api_request('GET', 'content', 'restrictions', 'v1', path_params={'contentId': page_id})
            read_access_emails = [user['username'] for user in response.json()['read']['restrictions']['user']['results']]
            read_access_groups = [group['name'] for group in response.json()['read']['restrictions']['group']['results']]
            edit_access_emails = [user['username'] for user in response.json()['update']['restrictions']['user']['results']]
            edit_access_groups = [group['name'] for group in response.json()['update']['restrictions']['group']['results']]
            
            if read_access_emails or read_access_groups:
                logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} Read Access Users: {read_access_emails} Groups: {read_access_groups}")
            if edit_access_emails or edit_access_groups:
                logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} Edit Access Users: {edit_access_emails} Groups: {edit_access_groups}")

            if username in read_access_emails or len(read_access_emails) == 0:
                # logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} User {username} has read access")
                return True
            elif username in edit_access_emails or len(edit_access_emails) == 0:
                # logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} User {username} has edit access")
                return True
            elif any(group in read_access_groups for group in self.current_user_memberships) or len(read_access_groups) == 0:
                # logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} User {username} has read access through group membership")
                return True
            elif any(group in edit_access_groups for group in self.current_user_memberships) or len(edit_access_groups) == 0:
                # logger.debug(f"{self.logs_prefix} PAGE_ID: {page_id} User {username} has edit access through group membership")
                return True
            else:
                logger.warning(f"{self.logs_prefix} PAGE_ID: {page_id} User {username} does not have read or edit access")
                return False
        except KeyError as ke:
            raise ValueError(f"Expected key not found in API response for page {page_id}: {ke}")

    def create_attachment(self, content_id: str, attachment_name: str, file_path: str) -> dict:
        upload_response = None
        try:
            upload_url = f"{self.instance_config.site_url}{self.get_endpoint('rest','base')}/{content_id}/child/attachment"
            logger.debug(f"{self.logs_prefix} Uploading Attachment {file_path} to {upload_url}")
            with open(file_path, 'rb') as f:
                files = {
                    'file': (attachment_name, f, 'multipart/form-data')
                }
                upload_response = self.session.post(upload_url,files=files)
            if upload_response.status_code in [200, 201]:
                self.update_request_stats(is_successful=True,created_attachment=True)
                logger.info(f"{self.logs_prefix} Successfully Uploaded Attachment Title: '{attachment_name}'")
        except requests.exceptions.HTTPError as e:
            self.update_request_stats(is_successful=False)
            logger.error(f"{self.logs_prefix} Attachment Upload Failed Status: {upload_response.status_code} Title: '{attachment_name}'")
            logger.error(f"{self.logs_prefix} Response: {upload_response.text[:200]} Reason: {e.response.json()['data']['message'][:200]}") 
        finally:
            os.remove(file_path)
            logger.debug(f"Deleted Attachment from path {file_path}")

    def download_attachment(self, content_id, file_name, download_dir) -> str:
        response = self.api_request('GET', 'attachment', 'download', 'v1', path_params={'contentId': content_id, 'fileName': urllib.parse.quote(file_name)})
        file_path = self._save_file(response.content, file_name, download_dir=download_dir)
        logger.debug(f"{self.logs_prefix} Downloaded Attachment at {file_path}")
        return file_path

    def download_pdf(self, content_id, content_name, download_dir):
        logger.info(f"{content_name} {download_dir}")

        # Safely create the filename and directory path
        filename = f"{self.safe_name(content_name)}.pdf"
        download_path = Path(download_dir) / "pdf" / filename
        download_path.parent.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        params = {
            'pageId': content_id
        }
        # Perform the API request
        response = self.api_request('GET', 'export', 'pdf', 'v1', params=params)
        # Check if the response is successful
        if response.status_code == 200:
            # Write the response content to a file
            with open(download_path, 'wb') as pdf_file:
                pdf_file.write(response.content)
            logger.debug(f"{self.logs_prefix} '{content_name}' PDF document downloaded at: {download_path}")
        else:
            logger.error(f"Failed to download PDF for '{content_name}'. Status code: {response.status_code}")

    def download_word(self, content_id, content_name, download_dir):
        filename = f"{self.safe_name(content_name)}.doc"
        # Create the download path correctly
        download_path = Path(download_dir) / "word" / filename
        download_path.parent.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        params = {
            'pageId': content_id
        }
        # Perform the API request
        response = self.api_request('GET', 'export', 'word', 'v1', params=params)
        # Check if the response is successful
        if response.status_code == 200:
            # Write the response content to a file
            with open(download_path, 'wb') as word_file:
                word_file.write(response.content)
            logger.debug(f"{self.logs_prefix} '{content_name}' Word document downloaded at: {download_path}")
        else:
            logger.error(f"Failed to download Word document for '{content_name}'. Status code: {response.status_code}")

    def safe_name(self,actual_name: str)-> str:
        # logger.debug(f"{self.logs_prefix} Actual FileName: {actual_name}")
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', actual_name).strip('_')  # Replace non-alphanumeric characters with underscores, remove leading/trailing underscores
        safe_name = safe_name[:64]  # Trim to the first 32 characters
        # logger.debug(f"{self.logs_prefix} Safe FileName: {safe_name}")
        return safe_name

    def _save_file(self, content, filename, download_dir):
        file_path = ""
        try:
            # Separate the filename into name and extension
            name, ext = os.path.splitext(filename)
            # logger.debug(f"Original filename: {filename} ext: {ext}")
            # Sanitize the name part and Recombine with the original extension
            safe_filename = f"{self.safe_name(name)}{ext}"
            # Determine the file path and save the file
            cwd = os.getcwd()
            file_path = os.path.join(cwd, download_dir, safe_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return file_path
        except Exception as e:
            raise ValueError(f"Failed to save file {file_path}: {e}")

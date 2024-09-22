from utils.logger import Logger
from typing import Optional
from api.client import ConfluenceAPIClient
from browser.selenium_driver import ConfluenceBrowserClient
from config.config_loader import ConfluenceConfig
from config.config_types import ConfluenceInstance
from models.gui.sections.actions_section import ActionsSection
from models.gui.sections.stats_section import StatsTable
from models.gui.sections.settings_form import SettingsForm
from models.tree.tree import ConfluencePagesTree
from models.tree.page_node import ConfluencePageNode
from models.tree.attachment_node import ConfluenceAttachmentNode
from tkinter import ttk
import threading
import time
logger = Logger()

class ConfluenceSpacesApp:
    def __init__(self, root, **kwargs):
        self.root = root
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')
        self.download_dir = kwargs.pop('download_dir','')
        self.app_config = ConfluenceConfig(config_file=kwargs.pop('config_file', ''),api_config_file=kwargs.pop('api_config_file', ''),browser_config_file=kwargs.pop('browser_config_file', ''))
        ## Logs Tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="> Home")
        self.actions_section = ActionsSection(parent=self.logs_frame, row=0, column=0, layout={"orientation": "horizontal"},sticky="nsew")
        ## Settings Tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="> Settings")

        # Source 
        self.source_space_id = None
        self.source_tree: ConfluencePagesTree = Optional[ConfluencePagesTree]
        self.source_instance = self.app_config.find_instance_by_key("source")
        self.source_api_client = ConfluenceAPIClient(instance_config=self.source_instance,api_config=self.app_config.api_config_data)
        self.source_form = SettingsForm(self.settings_frame,title="Source Confluence",row=1,column=0,sticky="w",config=self.source_instance.to_dict(),update_config=lambda: threading.Thread(target=self.update_source_instance).start())
        self.source_stats = StatsTable(parent=self.logs_frame, title="Source Space Details",row=4, column=0, padx=5, pady=5, sticky="nsew")
        self.source_stats.update_stats({"space_key": self.source_instance.space_key,"root_page_id": self.source_instance.root_page_id,"current_user_email": self.source_instance.credentials.email})

        # Target
        self.target_space_id = None
        self.target_tree: ConfluencePagesTree = Optional[ConfluencePagesTree]
        self.target_instance = self.app_config.find_instance_by_key("target")
        self.target_api_client = ConfluenceAPIClient(instance_config=self.target_instance,api_config=self.app_config.api_config_data)
        self.target_form = SettingsForm(self.settings_frame,title="Target Confluence", row=1,column=1,sticky="e",config=self.target_instance.to_dict(),update_config=lambda: threading.Thread(target=self.update_target_instance).start())
        self.target_stats = StatsTable(parent=self.logs_frame, title="Target Space Details", row=5, column=0, padx=5, pady=5, sticky="nsew")
        self.target_stats.update_stats({"space_key": self.target_instance.space_key,"root_page_id": self.target_instance.root_page_id,"current_user_email": self.target_instance.credentials.email})

        self.actions_section.update_action_command("fetch_pages","source",{"command": lambda: threading.Thread(target=self.fetch_source_tree).start()})
        self.actions_section.update_action_command("fetch_pages","target",{"command": lambda: threading.Thread(target=self.fetch_target_tree).start()})
        self.actions_section.update_action_command("save","source",{"command": lambda: threading.Thread(target=self.source_tree.save_tree_to_file_as_json()).start()})
        self.actions_section.update_action_command("save","target",{"command": lambda: threading.Thread(target=self.target_tree.save_tree_to_file_as_json()).start()})
        self.actions_section.update_action_command("create_pages","create_pages_only",{"command": lambda: threading.Thread(target=self.create_pages).start()})
        self.actions_section.update_action_command("create_pages","create_pages_with_attachments",{"command": lambda: threading.Thread(target=self.create_pages, kwargs={'with_attachments': True}).start()})
        self.actions_section.update_action_command("copy_pages","copy_pages_source_mode",{"command": lambda: threading.Thread(target=self.copy_pages).start()})
        self.actions_section.update_action_command("copy_pages","copy_pages_edit_mode",{"command": lambda: threading.Thread(target=self.copy_pages, kwargs={'edit_mode': True}).start()})
        self.actions_section.update_action_command("copy_pages","copy_attachments",{"command": lambda: threading.Thread(target=self.copy_attachments).start()})
        self.actions_section.update_action_command("export","pdf",{"command": lambda: threading.Thread(target=self.download_pdfs).start()})
        self.actions_section.update_action_command("export","word",{"command": lambda: threading.Thread(target=self.download_words).start()})
        self.actions_section.update_action_command("download","attachments",{"command": lambda: threading.Thread(target=self.download_attachments).start()})
        self.is_source_cookies_logged_in = False
        self.total_pages_copied = 0

    def update_source_instance(self):
        updated_data = self.source_form.get_selected_values()
        self.source_instance.from_dict(updated_data)
        self.app_config.update_config({"source": self.source_instance.to_dict()})
        logger.info(f"{self.source_instance.name} {self.source_instance.confluence_type}> Using {self.source_instance.credentials.rest_auth_type.title()}")
        if self.source_instance.credentials.rest_auth_type != "cookies_auth":
            self.source_api_client.initialize_session()
        else:
            self._initialize_browser_and_login(self.source_instance, self.source_api_client)
            self.is_source_cookies_logged_in = True
        self.source_space_id = self.source_api_client.get_space_id(self.source_instance.space_key)
        self.source_stats.update_current_user_groups(self.source_api_client.get_user_groups())
        self.source_stats.update_stats({"space_id": self.source_instance.space_key, "root_page_title": self.source_api_client.get_page_title(self.source_instance.root_page_id)})
        self.source_stats.update_stats({"space_key": self.source_instance.space_key,"root_page_id": self.source_instance.root_page_id,"current_user_email": self.source_instance.credentials.email})
        self._update_req_stats()

    def update_target_instance(self):
        updated_data = self.target_form.get_selected_values()
        self.target_instance.from_dict(updated_data)
        self.app_config.update_config({"target": self.target_instance.to_dict()})
        logger.info(f"{self.target_instance.name} {self.target_instance.confluence_type}> Using {self.target_instance.credentials.rest_auth_type.title()}")
        if self.target_instance.credentials.rest_auth_type != "cookies_auth":
            self.target_api_client.initialize_session()
        else:
            self._initialize_browser_and_login(self.target_instance, self.target_api_client)
        self.target_space_id = self.target_api_client.get_space_id(self.target_instance.space_key)
        self.target_stats.update_current_user_groups(self.target_api_client.get_user_groups())
        self.target_stats.update_stats({"space_id": self.target_instance.space_key, "root_page_title": self.target_api_client.get_page_title(self.target_instance.root_page_id)})
        self.target_stats.update_stats({"space_key": self.target_instance.space_key,"root_page_id": self.target_instance.root_page_id,"current_user_email": self.target_instance.credentials.email})
        self._update_req_stats()

    def fetch_source_tree(self):
        if not self.source_api_client.logged_in:
            logger.info(f"{self.source_instance.name} {self.source_instance.confluence_type}> Logging In {self.source_instance.credentials.rest_auth_type.title()}")
            if self.source_instance.credentials.rest_auth_type != "cookies_auth":
                self.source_api_client.initialize_session()
            else:
                self._initialize_browser_and_login(self.source_instance, self.source_api_client)
                self.is_source_cookies_logged_in = True
        root_page = self.source_api_client.get_content(self.source_instance.root_page_id)
        root_node = ConfluencePageNode.from_api_response(root_page.json(), self.source_instance.confluence_type)
        self.source_tree = ConfluencePagesTree(root_node, self.source_api_client)
        self.source_tree.build_tree(self.source_instance.confluence_type, from_label=self.source_instance.label, exclude_page_ids=self.source_instance.exclude_ids)
        self.source_tree.print_pages()
        self.source_space_id = self.source_api_client.get_space_id(self.source_instance.space_key)
        self.source_stats.update_current_user_groups(self.source_api_client.get_user_groups())
        self.source_stats.update_stats({"space_id": self.source_instance.space_key, "root_page_title": self.source_api_client.get_page_title(self.source_instance.root_page_id),"total_pages": self.source_tree.fetch_total_nodes()})
        self.actions_section.update_button_state("save", "readonly", "normal")
        self.actions_section.update_button_state("create_pages", "readonly", "normal")
        self.actions_section.update_button_state("copy_pages", "readonly", "normal")
        self.actions_section.update_button_state("download", "readonly", "normal")
        if self.is_source_cookies_logged_in:
            self.actions_section.update_button_state("export", "readonly", "normal")
        self._update_req_stats()

    def fetch_target_tree(self):
        if not self.target_api_client.logged_in:
            logger.info(f"{self.target_instance.name} {self.target_instance.confluence_type}> Logging In {self.target_instance.credentials.rest_auth_type.title()}")
            if self.target_instance.credentials.rest_auth_type != "cookies_auth":
                self.target_api_client.initialize_session()
            else:
                self._initialize_browser_and_login(self.target_instance, self.target_api_client)
        root_page = self.target_api_client.get_content(self.target_instance.root_page_id)
        root_node = ConfluencePageNode.from_api_response(root_page.json(), self.target_instance.confluence_type)
        self.target_tree = ConfluencePagesTree(root_node, self.target_api_client)
        self.target_tree.build_tree(self.target_instance.confluence_type, from_label=self.target_instance.label, exclude_page_ids=self.target_instance.exclude_ids)
        self.target_tree.print_pages()
        self.target_space_id = self.target_api_client.get_space_id(self.target_instance.space_key)
        self.target_stats.update_current_user_groups(self.target_api_client.get_user_groups())
        self.target_stats.update_stats({"space_id": self.target_instance.space_key, "root_page_title": self.target_api_client.get_page_title(self.target_instance.root_page_id),"total_pages": self.target_tree.fetch_total_nodes()})
        self.actions_section.update_button_state("save", "readonly", "normal")
        self._update_req_stats()

    def _initialize_browser_and_login(self, instance, api_client: ConfluenceAPIClient):
        browser = ConfluenceBrowserClient()
        browser.initialize_driver()
        self._login_to_instance(browser, instance, same_tab=True)
        api_client.initialize_session(cookies=browser.driver.get_cookies())
        browser.close_driver()

    def execute_with_stats_update(self, func, *args, **kwargs):
        stop_event = threading.Event()  # Event to signal when to stop the stats thread
        stats_thread = threading.Thread(target=self._update_stats_realtime, args=(stop_event,))
        stats_thread.start()
        
        try:
            # Call the function with provided arguments
            result = func(*args, **kwargs)
        finally:
            # Stop the real-time stats update once the function execution is done
            stop_event.set()  # Signal the stats thread to stop
            stats_thread.join()  # Wait for the stats thread to finish
        
        # Final update of the stats after the execution
        self.target_stats.update_stats({
            "total_pages_created": self.target_api_client.total_pages_created,
            "total_attachments_created": self.target_api_client.total_attachments_created
        })
        self._update_req_stats()  # Final stats update
        return result

    def create_pages(self, with_attachments: bool = False):
        # Start the real-time stats update in a separate thread
        stop_event = threading.Event()  # Event to signal when to stop the stats thread
        stats_thread = threading.Thread(target=self._update_stats_realtime, args=(stop_event,))
        stats_thread.start()
        try: # Create pages in order, which can take time
            self.target_tree = None
            root_page = self.target_api_client.get_content(self.target_instance.root_page_id)
            root_node = ConfluencePageNode.from_api_response(root_page.json(), self.target_instance.confluence_type)
            self.target_tree = ConfluencePagesTree(root_node, self.target_api_client)
            self.create_pages_in_order(self.source_tree.root, self.target_instance.root_page_id, with_attachments)
        finally:
            # Stop the real-time stats update once page creation is done
            stop_event.set()  # Signal the stats thread to stop
            stats_thread.join()  # Wait for the stats thread to finish
        # Final update of the stats after the creation process
        self.target_stats.update_stats({
            "total_pages_created": self.target_api_client.total_pages_created,
            "total_attachments_created": self.target_api_client.total_attachments_created
        })
        self._update_req_stats()  # Final stats update
        
    def _create_page(self,parent_id,source_node: ConfluencePageNode,with_attachments: bool = False):
        self._update_req_stats()
        payload = {
            "title": str(source_node.title),
            "spaceId": str(self.target_space_id),
            "body": {
                "storage": {
                    "value": "Text will follow soon!",
                    "representation": "storage"
                }
            }
        }
        if parent_id:
            payload["parentId"] = parent_id
        created_page_id = self.target_api_client.create_content(payload,self.target_instance.space_key)
        self.target_api_client.add_automation_label(content_id=created_page_id,automation_label=self.target_instance.label)
        if len(source_node.labels) > 0:
            self.target_api_client.add_labels(created_page_id, source_node.labels)
        if with_attachments:
            self.download_and_upload_attachments(source_node, created_page_id)
        return created_page_id

    def create_pages_in_order(self, node: Optional[ConfluencePageNode] = None, parent_id: Optional[str] = None, with_attachments: bool = False):
        self._update_req_stats()
        if node is None:
            node = self.source_tree.root
        try:
            logger.info(f"Creating page '{node.title}'")
            node.labels = [label['name'] for label in self.source_api_client.get_labels(node.id)]
            node.child_pages = self.source_api_client.get_child_pages(node.id)
            created_page_id = self._create_page(parent_id=parent_id, source_node=node, with_attachments=with_attachments)
            for child_node in node.child_pages:
                self.create_pages_in_order(child_node, created_page_id, with_attachments)
        except Exception as e:
            logger.error(f"Error Creating Page with title: '{node.title}' Reason: {str(e)}")

    def download_and_upload_attachments(self,source_node: ConfluencePageNode, target_page_id:str):
        self.source_tree.fetch_attachments(source_node)
        if len(source_node.child_attachments) > 0:
            for attachment in source_node.child_attachments:
                logger.info(f"Downloading attachment '{attachment.title}' from page '{source_node.title}'")
                file_path = self.source_api_client.download_attachment(source_node.id, attachment.title,f"{self.download_dir}/{self.source_instance.name}")
                logger.info(f"Uploading attachment '{attachment.title}' to target page '{target_page_id}'")
                self.target_api_client.create_attachment(content_id=target_page_id, attachment_name=attachment.title, file_path=file_path)
        else:
            logger.warning(f"No attachments Found for '{source_node.title}'")
        self._update_req_stats()

    def copy_pages(self, edit_mode: bool = False, **kwargs):
        if self.target_tree is None:
            logger.warn_tree_not_initialized(is_source=False)
            return

        def copy_logic():
            browser = ConfluenceBrowserClient()
            browser.initialize_driver()
            self._login_to_instances(browser)

            self.target_tree.rearrange_trees(self.source_tree.root)
            for source_node, new_node in zip(self.source_tree.traverse_tree(), self.target_tree.traverse_tree()):
                if edit_mode and not self._is_page_editable(source_node):
                    continue
                if source_node.title == new_node.title:
                    self._perform_copy_paste(browser, source_node, new_node, edit_mode)
                    self.total_pages_copied += 1
                else:
                    logger.warning(f"Warning: Titles do not match. Original: '{source_node.title}', Target: '{new_node.title}'")
            browser.close_driver()
        return self.execute_with_stats_update(copy_logic, **kwargs)

    def _login_to_instances(self, browser):
        self._login_to_instance(browser, self.source_instance, same_tab=True)
        self._login_to_instance(browser, self.target_instance, same_tab=False)

    def _login_to_instance(self, browser, instance, same_tab):
        if same_tab:
            browser.open_page_in_same_tab(instance.site_url + instance.home_path)
        else:
            browser.open_new_tab(instance.site_url + instance.home_path)
        browser.set_credentials(instance.credentials.email, instance.credentials.password, instance.credentials.mfa_secret_key)
        browser.process_elements_chain(self.app_config.get_elements_list(instance.confluence_type, 'login_page'))

    def _is_page_editable(self, source_node):
        if not self.source_api_client.get_page_restrictions(source_node.id):
            logger.warning(f"Page '{source_node.title}' is not editable, skipping.")
            return False
        return True

    def _perform_copy_paste(self, browser, source_node, new_node, edit_mode):
        logger.info(f"Copying page '{source_node.title}' to '{new_node.title}'")
        if edit_mode:
            source_url = self._get_edit_url(self.source_instance.confluence_type, self.source_instance.site_url, source_node.edit_link, self.source_instance.space_key, source_node.id)
        else:
            source_url = f"{self.source_instance.site_url}{self.app_config.get_endpoint(self.source_instance.confluence_type, 'source', 'view')}?pageId={source_node.id}"
        browser.perform_copy_paste(
            source={
                'tab_index': 0,
                'url': source_url,
                'element_selector_value': self.app_config.get_element(self.source_instance.confluence_type, 'edit_page', 'content').selector_value,
                'element_selector_type': self.app_config.get_element(self.source_instance.confluence_type, 'edit_page', 'content').selector_type,
                'discard_selector_value': self.app_config.get_element(self.source_instance.confluence_type, 'edit_page', 'discard_button').selector_value,
                'discard_selector_type': self.app_config.get_element(self.source_instance.confluence_type, 'edit_page', 'discard_button').selector_type,
            },
            target={
                'tab_index': 1,
                'url': self._get_edit_url(self.target_instance.confluence_type, self.target_instance.site_url, new_node.edit_link, self.target_instance.space_key, new_node.id),
                'element_selector_value': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'content').selector_value,
                'element_selector_type': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'content').selector_type,
                'save_button_selector_value': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'save_button').selector_value,
                'save_button_selector_type': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'save_button').selector_type,
                'page_width_button_selector_value': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'page_width_button').selector_value,
                'page_width_button_selector_type': self.app_config.get_element(self.target_instance.confluence_type, 'edit_page', 'page_width_button').selector_type,
            },
            edit_mode=edit_mode
        )

    def copy_attachments(self):
        def copy_logic():
            if self.target_tree == None:
                logger.warn_tree_not_initialized(is_source=False)
                return 
            logger.info("Copying Attachments to target pages...")
            self.target_tree.rearrange_trees(self.source_tree.root)
            for source_node, new_node in zip(self.source_tree.traverse_tree(), self.target_tree.traverse_tree()):
                if source_node.title == new_node.title:
                    logger.info(f"Copying attachments from page '{source_node.title}'")
                    self.download_and_upload_attachments(source_node, new_node.id)
            self._update_req_stats()
        return self.execute_with_stats_update(copy_logic, **kwargs)

    def download_pdfs(self):
        if self.source_tree == None:
            logger.warn_tree_not_initialized(is_source=True)
            return 
        for page in self.source_tree.traverse_tree():
            logger.info(f"Exporting pdf from page '{page.title}'")
            self.source_api_client.download_pdf(content_id=page.id, content_name=page.title, download_dir=f"{self.download_dir}/{self.source_instance.name}")
            self._update_req_stats()

    def download_words(self):
        if self.source_tree == None:
            logger.warn_tree_not_initialized(is_source=True)
            return 
        for page in self.source_tree.traverse_tree():
            logger.info(f"Exporting word doc from page '{page.title}'")
            self.source_api_client.download_word(content_id=page.id, content_name=page.title, download_dir=f"{self.download_dir}/{self.source_instance.name}")
        self._update_req_stats()

    def download_attachments(self):
        if self.source_tree == None:
            logger.warn_tree_not_initialized(is_source=True)
            return 
        for page in self.source_tree.traverse_tree():
            self.source_tree.fetch_attachments(page)
            if len(page.child_attachments) > 0:
                for attachment in page.child_attachments:
                    logger.info(f"Downloading attachment '{attachment.title}' from page '{page.title}'")
                    file_path = self.source_api_client.download_attachment(page.id, attachment.title,f"{self.download_dir}/attachments/{self.source_api_client.safe_name(page.title)}")
                    logger.debug(f"Downloaded attachment to {file_path}")
        self._update_req_stats()

    def _update_stats_realtime(self, stop_event):
        #Continuously updates the stats until the stop_event is set. param stop_event: Event to signal when to stop updating stats.
        while not stop_event.is_set():
            # Update the stats at regular intervals (e.g., every 2 seconds)
            self.target_stats.update_stats({
                "total_pages_created": self.target_api_client.total_pages_created,
                "total_attachments_created": self.target_api_client.total_attachments_created,
                "total_pages_copied": self.total_pages_copied,
            })
            self._update_req_stats()
            # Wait for a short interval before updating again
            time.sleep(1)  # Adjust the sleep time as needed for real-time updates
            
    def _get_edit_url(self,confluence_type, site_url:str="", edit_url:str="", space_key:str="", page_id:str=""):
        if confluence_type == 'cloud':
            return f"{site_url}/wiki/spaces/{space_key}/pages/edit-v2/{page_id}"
        elif confluence_type == 'server':
            return f"{site_url}{edit_url}"

    def _update_req_stats(self):
        threading.Thread(target=self.source_stats.update_stats({
            "total_http_requests": self.source_api_client.total_requests,
            "successful_http_requests": self.source_api_client.total_success,
            "failed_http_requests": self.source_api_client.total_failed
        })).start()
        threading.Thread(target=self.target_stats.update_stats({
            "total_http_requests": self.target_api_client.total_requests,
            "successful_http_requests": self.target_api_client.total_success,
            "failed_http_requests": self.target_api_client.total_failed
        })).start()
        self.source_api_client.requests_stats()
        self.target_api_client.requests_stats()
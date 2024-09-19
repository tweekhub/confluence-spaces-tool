from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException,TimeoutException, NoSuchElementException, StaleElementReferenceException
import pyotp
from . import logger
import time
from config.config_types import UIElement
from typing import List

class ConfluenceBrowserClient:
    def __init__(self, username:str="", password:str="", mfa_secret_key:str="", timeout_after: int = 10, max_retries: int = 3,browser_headless:bool=False,is_experimental:bool=True):
        self.username = username
        self.password = password
        self.mfa_secret_key = mfa_secret_key
        self.driver = None
        self.initial_window_handle = None
        self.timeout_after = timeout_after
        self.max_retries = max_retries
        self.browser_headless = browser_headless
        self.is_experimental = is_experimental

    def initialize_driver(self):
        logger.debug(f"Using username={self.username}, timeout_after={self.timeout_after}, max_retries={self.max_retries}, browser_headless={self.browser_headless}, is_experimental={self.is_experimental}")
        options = self._configure_chrome_options()
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.initial_window_handle = self.driver.current_window_handle
            logger.debug(f"Successfully Initialized Chrome Browser with Initial Window Handle: {self.initial_window_handle}")
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome browser: {error} ")
            logger.error("For Ubuntu/Debian Linux run the install script for chrome i.e. ./install_browser.sh")

    def _configure_chrome_options(self) -> Options:
        options = Options()
        if self.browser_headless:
            options.add_argument("--headless")
            logger.debug("Headless mode enabled")

        default_arguments = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1450,860",
            "--password-store=basic"
            # Options for undetectable capabilities
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        ]
        # Experimental options for undetectable capabilities
        experimental_options = [
            ("excludeSwitches", ["enable-automation"]),
            ("useAutomationExtension", False),
            ("prefs",{"credentials_enable_service": False,"profile.password_manager_enabled": False})
        ]
        if self.is_experimental:
            for option, value in experimental_options:
                options.add_experimental_option(option, value)
            logger.debug("Experimental options added")
        for arg in default_arguments:
            options.add_argument(arg)
        logger.debug(f"Chrome configured with options: {options.arguments}")
        return options

    def get_driver(self)-> webdriver.Chrome:
        logger.debug("Retrieving Chrome driver")
        return self.driver

    def set_credentials(self,username:str="",password:str="",mfa_secret_key:str=""):
        self.username = username
        self.password = password
        self.mfa_secret_key = mfa_secret_key
        logger.debug(f"Using Credentials for username={username}, password={'*' * len(password) if password else None}, mfa_secret_key={'*' * len(mfa_secret_key) if mfa_secret_key else None}")

    def open_new_tab(self, url: str):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(url)
        logger.debug(f"Opening New Tab for URL: {url} Total Tabs: {len(self.driver.window_handles)} ")

    def switch_to_tab(self, index: int):
        logger.debug(f"Switching to tab index: {index}")
        if index < len(self.driver.window_handles):
            self.driver.switch_to.window(self.driver.window_handles[index])
            logger.debug(f"Switched to tab with handle: {self.driver.current_window_handle}")
        else:
            logger.warning(f"Tab index {index} is out of range. Total tabs: {len(self.driver.window_handles)}")

    def open_page_in_same_tab(self, url: str):
        logger.debug(f"Navigating to {url}")
        try:
            self.driver.get(url)
            logger.debug(f"Successfully Navigated to {url} ")
        except Exception as e:
            logger.error(f"Failed to Navigate to {url}: {e}")

    def perform_copy_paste(self, source: dict, target: dict,edit_mode:bool=False):
        logger.debug(f"Copying from {source['url']} to {target['url']}...")
        self.switch_to_tab(source['tab_index'])
        self.open_page_in_same_tab(source['url'])
        if edit_mode:
            content_area = self.wait_and_find_element(source['element_selector_value'], source['element_selector_type'])
            content_area.click()
            logger.debug(f"CLICKED! name={content_area.accessible_name}, tag={content_area.tag_name}")

        time.sleep(1)
        self.select_all_and_copy()
        time.sleep(1)

        if edit_mode:
            discard_button = self.wait_and_find_element(source['discard_selector_value'], source['discard_selector_type'])
            discard_button.click()
            logger.debug(f"CLICKED! name={discard_button.accessible_name}, tag={discard_button.tag_name}")

        self.switch_to_tab(target['tab_index'])
        self.open_page_in_same_tab(target['url'])

        target_element = self.wait_and_find_element(target['element_selector_value'], target['element_selector_type'])
        target_element.click()
        logger.debug(f"CLICKED! name={target_element.accessible_name}, tag={target_element.tag_name}")

        time.sleep(1)
        self.select_all_and_paste()
        time.sleep(1)

        # if target['page_width_button_selector_value'] and target['page_width_button_selector_type']:
        #     page_width_button = self.wait_and_find_element(target['page_width_button_selector_value'], target['page_width_button_selector_type'])
        #     # self.driver.execute_script("arguments[0].click();", page_width_button)
        #     page_width_button.click()
        #     logger.debug(f"CLICKED! name={page_width_button.accessible_name}, tag={page_width_button.tag_name}")

        save_button = self.wait_and_find_element(target['save_button_selector_value'], target['save_button_selector_type'])
        save_button.click()

    def located_element(self, selector_value: str, selector_type: str):
        locator = self._get_by_selector(selector_type), selector_value
        return CachedWebElement(locator)

    def process_elements_chain(self, elements: List[UIElement]):
        logger.info(f"Processing {len(elements)} Elements Chain")
        for element in elements:
            self.process_element(element, self.max_retries)

    def process_element(self, element: UIElement, retries: int):
        logger.debug(f"Element type={element.element_type} selector_type={element.selector_type} selector_value={element.selector_value} action={element.action} post_action={element.post_action}")
        try:
            found_element = self.wait_and_find_element(element.selector_value, element.selector_type)
            found_element = self.scroll_to_element(found_element)
            found_element = self._perform_action(element, found_element)
            if element.post_action:
                found_element = self._perform_post_action(element, found_element)
            time.sleep(1)
            logger.debug(f"Successfully Processed UIElement {element.element_type}")
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            if retries > 0:
                logger.warning(f"Error interacting with UIElement '{element.element_type}': {str(e)}. Retrying {retries} more times.")
                self.process_element(element, retries - 1)
            else:
                logger.error(f"Failed to process UIElement with selector '{element.element_type}' after multiple retries: {e}")
        except Exception as e:
            logger.error(f"Failed to process UIElement with selector '{element.element_type}': {e}")

    def wait_and_find_element(self, selector_value: str, selector_type: str) -> WebElement:
        logger.debug(f"Waiting {self.timeout_after} seconds to find WebElement using UIElement: {selector_value}")
        WebDriverWait(self.driver, self.timeout_after).until(EC.presence_of_element_located((self._get_by_selector(selector_type), selector_value)))
        element = self.driver.find_element(self._get_by_selector(selector_type), selector_value)
        logger.debug(f"Found WebElement! name={element.accessible_name}, tag={element.tag_name}")
        return element

    def scroll_to_element(self, element: WebElement)-> WebElement:
        logger.debug(f"Scrolling to name={element.accessible_name}, tag={element.tag_name}")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        logger.debug(f"Scrolled Successfully!")
        return element

    def select_all_and_copy(self):
        logger.debug("Selecting All and Copy Page Content")
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()

    def select_all_and_paste(self):
        logger.debug("Selecting All and Pasting Page Content")
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACK_SPACE).perform()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

    def _get_by_selector(self, selector: str):
        logger.debug(f"Getting By selector for: {selector}")
        if selector.lower().startswith("css"):
            return By.CSS_SELECTOR
        elif selector.lower().startswith("xpath"):
            return By.XPATH
        elif selector.lower().startswith("id"):
            return By.ID
        elif selector.lower().startswith("name"):
            return By.NAME
        elif selector.lower().startswith("class"):
            return By.CLASS_NAME
        elif selector.lower().startswith("tag"):
            return By.TAG_NAME
        elif selector.lower().startswith("link"):
            return By.LINK_TEXT
        elif selector.lower().startswith("partial"):
            return By.PARTIAL_LINK_TEXT
        else:
            return By.NAME
 
    def _get_action_value(self, action: str):
        logger.debug(f"Getting action value for: {action}")
        if action == 'USE_EMAIL':
            return self.username
        elif action == 'USE_PASSWORD':
            return self.password
        elif action == 'GENERATE_MFA':
            return pyotp.TOTP(self.mfa_secret_key).now()
        else:
            return ""

    def _perform_action(self, element: UIElement, found_element: WebElement)-> WebElement:
        logger.debug(f"Performing action={element.action} on UIElement={element.selector_value}")
        if element.action == 'click':
            found_element.click()
        elif element.action in ['USE_EMAIL', 'USE_PASSWORD', 'GENERATE_MFA']:
            value = self._get_action_value(element.action)
            found_element.send_keys(value)
        elif element.action == 'USE_SCRIPT':
            self.driver.execute_script("arguments[0].click();", found_element)
        logger.debug(f"Action {element.action} performed successfully")
        return found_element

    def _perform_post_action(self, element: UIElement, found_element: WebElement)-> WebElement:
        logger.debug(f"Performing post-action={element.post_action} on UIElement={element.selector_value}")
        if element.post_action == 'submit':
            found_element.submit()
        logger.debug(f"Post-action {element.post_action} performed successfully")
        return found_element
            
    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.initial_window_handle = None
            logger.info("Chrome Browser closed successfully!")
        else:
            logger.warning("Driver is not initialized!")
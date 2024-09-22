# Confluence Spaces Tool 

[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=atonomic_confluence-spaces-tool&metric=bugs)](https://sonarcloud.io/summary/new_code?id=atonomic_confluence-spaces-tool)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=atonomic_confluence-spaces-tool&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=atonomic_confluence-spaces-tool)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=atonomic_confluence-spaces-tool&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=atonomic_confluence-spaces-tool)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=atonomic_confluence-spaces-tool&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=atonomic_confluence-spaces-tool)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=atonomic_confluence-spaces-tool&metric=coverage)](https://sonarcloud.io/summary/new_code?id=atonomic_confluence-spaces-tool)

### Not Admin? Not a problem, Be the Super User for your Confluence Space!
## Preface
The Confluence Spaces Tool is a powerful utility designed to automate the copying of spaces between different Confluence instances. It supports both Confluence Server and Cloud versions and can perform various tasks such as fetching, creating, and updating pages, managing attachments, and synchronizing content between Confluence spaces. This tool is particularly useful for teams aiming to streamline documentation processes or migrate content between instances.

![image](https://github.com/user-attachments/assets/a787f681-5671-4fc8-b93c-74a20bd5051a)


### Key Functionalities:
- Build a hierarchical structure of pages, including details like page ID, title, labels, attachments, and child page IDs. The root page of this structure will be determined by an ID provided via the GUI settings or the `config.yaml` file.
- Retrieve and store the names of macros used in the source pages.
- Save this structure in both JSON and text file formats.
- Create pages, along with their attachments and subpages, in a Confluence Space on a different Confluence instance.
- Copy page content by visually transferring it from the source to the target Confluence space.
   * The tool can open the page in edit mode. (Check if a page can be opened in edit mode before execution; if not, log a warning.)
   * It can also open the page in source view mode and copy content to the target page in another Confluence instance.
- Transfer attachments between source and destination Confluence page trees.
- Include source pages that match a specific label.
- Exclude specific source pages by providing a list of Page IDs, which will be ignored along with their subpages.
- Add an automation label to pages created in the destination Confluence space for tracking.
   - This label allows future tool executions to check if a page in the destination has been created automatically.
- Implement logging and error handling for a smooth Spacesprocess.
- Supports rest api v1 and v2 for confluence Cloud and rest api v1 for confluence servers.
   * currently this tool uses rest api v2 to get,create or update pages in confluence cloud versions, all other requests uses rest api v1 for cloud as well as for server versions.

This tool was tested by copying several thousand pages and attachments from a space in conflunce server to a space in confluence cloud. 

## Known Issues

* `cookies_auth` is not supported with Confluence Cloud. This authentication method is used for downloading/exporting Confluence pages as PDF or Word documents.
* The `Copy Content (Source View)` method cannot be used if the source view plugin is disabled in your Confluence instance.
* The `Copy Content (Edit View)` method cannot copy all sections from the source tree properly,if the source pages utilize sections view.
* When creating pages, if a page with the same title already exists in the target space, the tool will fetch the page ID from the existing page of target space and continue creating or copying pages under the existing page, even if it is outside the target tree. This may result in inconsistencies if you require pages to be created strictly within the target tree.

## Configuration

You can configure the credentials, source and destination details in the gui of the app as well. Alternatively you can define a `config.yaml` file to load the settings from the file. 

1. Copy the `configuration.yaml` file to `config.yaml`:
   ```bash
   cp configuration.yaml config.yaml
   ```
   This creates a private configuration file that won't be tracked by version control.

2. Edit `config.yaml` to include your Confluence site URL and authentication information.
   This step is crucial for the tool to access your Confluence instances.

3. If the tool can not properly click the desired elements in the chrome browser, then you could alter its configuration json file.
      * if login is failing, alter the list of `login_page` elements from the file `confluence-elements.json`. the sequence of elements in the json array must be aligned with the actual login process.
      ```
      allowed selector types: css, xpath, id, name, class, tag, link, partial
      allowed actions: USE_EMAIL, USE_PASSWORD, GENERATE_MFA, USE_SCRIPT or click
      allowed post actions: submit
        {
            "element_type": "textfield", # 
            "selector_type": "ID", 
            "selector_value": "os_username",
            "action": "USE_EMAIL", 
            "post_action": ""
          }
      ```
      * similarly, the copy command to visually copy and paste page contents between confluence instances, you can edit the `edit_page` list of elements defined in the `confluence-elements.json` file. 

4. if the api endpoints are deprecated or replaced with new paths in Confluence Server or Cloud Instances then update them accordingly in `confluence-api.json`

## Usage

The Confluence SpacesTool can be run with various command-line arguments to control its behavior. Here's the basic usage:

```bash
    python3 main.py [options]
```

### Common Options:
- `--download-dir`: Specify the directory to download files to (default: "downloads")
- `--config-file`: Specify the path to the configuration file (default: "./config.yaml")
- `--api-config-file`: Specify the path to the API configuration file (default: "./confluence-api.json")
- `--browser-config-file`: Specify the path to the UI elements configuration file (default: "./confluence-elements.json")
- `--log-level`: Set the logging level for the Spacesprocess (choices: "debug", "info", "warning", "error") (default: "info")
- `--log-file`: Specify the path to the log file for the Spacesprocess (default: "confluence-Spaces.log")
- `--version`: Prints out the version for this confluence Spacestool. 

### Examples:
1. Create pages in the target confluence space, by reading the source tree first and then executing the create pages action.
   * Pages can be created with or without attachments, depends which action you select from the dropdown menu.
   * This action will create empty pages, 
2. To copy the content of pages, you need to execute one of the following action i.e. `Copy Content (Edit View)` or `Copy Content (Source View)` 
3. If you have changed the settings then re-read the source and target trees before proceeding.
4. Save the fetched pages tree structure to file as txt or json by executing the `save` action on either `source` or `target`
5. Download files from the source confluence such as pdf,docs or attachments 
   * Exporting `pdf` or `doc` form of confluence pages requires the usage of `cookies_auth`, this however is not compatible with confluence cloud versions.
   * However downloading attachments work with confluence server as well as confluence cloud. 


## Logging

The Spacestool logs its activities to both the console and a file. By default, the log file is named `confluence-Spaces.log`, but this can be changed using the `--log-file` option. The logging level can be adjusted using the `--log-level` option, with available choices being "debug", "info", "warning", and "error". The default log level is "info".

For example, to set a custom log file and increase the verbosity to debug level:

```bash
   python3 main.py --log-level debug
```

## Contributing

If you find bugs or missing features, then please open a issue so i could implement a fix for that.
Alternatively, You can also setup a developer environment for this tool by following the installation guide below.

### Developer Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/atonomic/confluence-spaces-tool.git
   cd confluence-spaces-tool
   ```
   This step downloads the tool's source code to your local machine.

2. Ensure you have Python 3.10 or later installed on your system.
   Python 3.10+ is required due to some of the advanced features used in the tool.

3. Install Google Chrome (if not already installed) and ensure it is accessible in your shell:
   ```bash
      # install browser if required
      chmod +x ./scripts/install_browser.sh
      .
   ```
   Chrome is used for web automation tasks in the tool.

4. Create a virtual environment and activate it:
   ```bash
   # install python virtual env lib if missing
   # apt-get install python3-venv
   python3 -m venv .pyenv
   source .pyenv/bin/activate
   ```
   A virtual environment helps isolate the tool's dependencies from your system-wide Python installation.

5. Install the required dependencies:
   ```
   pip3 install -r requirements.txt
   ```
   This installs all the necessary Python libraries for the tool to function.

or you can also run the gui app via docker

```bash
   sudo apt install x11-xserver-utils xorg
   # allow from anywhere to connect (used for opening gui from within Container)
   xhost +

   docker build -t test-gui . -f Dockerfile
   docker run -e DISPLAY=$DISPLAY -e CONFIG_FILE=./configuration.yaml -v ./configuration.yaml:/app/configuration.yaml -v ./downloads:/app/downloads -v /tmp/.X11-unix:/tmp/.X11-unix test-gui:latest
```

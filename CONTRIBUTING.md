# Contributing to Confluence SpacesTool

Thank you for your interest in contributing to Confluence SpacesTool! We welcome all people who want to contribute in a healthy and constructive manner within our community. To help us create a safe and positive community experience for all, we require all participants to adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).

This document is a guide to help you through the process of contributing to Confluence SpacesTool.

## Become a contributor

You can contribute to Confluence SpacesTool in several ways. Here are some examples:

- Contribute to the Confluence SpacesTool codebase.
- Report and triage bugs.
- Write technical documentation and blog posts, for users and contributors.
- [Help others by answering questions about Confluence SpacesTool.](https://github.com/orgs/community/discussions/139070)

For more ways to contribute, check out the [Open Source Guides](https://opensource.guide/how-to-contribute/).

### Report bugs

Before submitting a new issue, try to make sure someone hasn't already reported the problem. Look through the [existing issues](https://github.com/atonomic/confluence-spaces-tool/issues) for similar issues.

Report a bug by submitting a [bug report](https://github.com/atonomic/confluence-spaces-tool/issues/new?labels=type%3A+bug&template=0-bug_report.md). Make sure that you provide as much information as possible on how to reproduce the bug.

Follow the issue template and add additional information that will help us replicate the problem.

### Suggest enhancements

If you have an idea of how to improve Confluence SpacesTool, submit a [feature request](https://github.com/atonomic/confluence-spaces-tool/issues/new?assignees=&labels=type%2Ffeature-request&projects=&template=1-feature_requests.md).

### Write documentation

Once the bug is fixed, or the feature is added, then document it accordingly in the [Readme File](README.md).

### Answering questions

If you have a question and you can't find the answer in the [Readme File](README.md), the next step is to ask it on the [community discussions](https://github.com/orgs/community/discussions/139070).

It's important to us to help these users, and we'd love your help. Sign up to GitHub, and start helping other Confluence SpacesTool users by answering their questions.

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
      chmod +x ./install_browser.sh
      ./install_browser.sh
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

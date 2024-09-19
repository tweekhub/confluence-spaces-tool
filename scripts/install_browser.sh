#!/usr/bin/env bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Google Chrome
install_chrome() {
    echo "Google Chrome not found. Installing Google Chrome..."
    
    # Download the latest Google Chrome .deb package
    wget -q -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    
    # Install the .deb package
    sudo dpkg -i /tmp/google-chrome-stable_current_amd64.deb
    
    # Fix any dependency issues
    sudo apt-get install -f -y
    
    # Remove the downloaded .deb file
    rm /tmp/google-chrome-stable_current_amd64.deb
    
    echo "Google Chrome installed successfully."
}

# Check if Google Chrome is installed
if command_exists google-chrome; then
    echo "Google Chrome is already installed."
else
    install_chrome
fi

# Function to check and set up GUI-related configurations
check_gui_configuration() {
    echo "Checking GUI configuration for running Chrome..."

    # Check if 'xvfb' is installed (Virtual Framebuffer for headless display)
    if ! dpkg -l | grep -q xvfb; then
        echo "Installing xvfb..."
        sudo apt-get install -y xvfb
    else
        echo "xvfb is already installed."
    fi

    # Set DISPLAY environment variable if not already set
    if [ -z "$DISPLAY" ]; then
        export DISPLAY=:0
        echo "DISPLAY environment variable set to :0"
    else
        echo "DISPLAY environment variable is already set to $DISPLAY"
    fi

    # Allow X server connections from any host (use cautiously)
    if xhost | grep -q "access control enabled"; then
        echo "Disabling access control for X server..."
        xhost +
    fi

    # Check if 'google-chrome.desktop' file exists to run Chrome as GUI app
    if [ ! -f /usr/share/applications/google-chrome.desktop ]; then
        echo "Creating a desktop entry for Google Chrome..."
        
        # Create a desktop entry
        sudo bash -c 'cat <<EOF > /usr/share/applications/google-chrome.desktop
[Desktop Entry]
Version=1.0
Name=Google Chrome
Comment=Access the Internet
Exec=/usr/bin/google-chrome-stable %U
Terminal=false
Icon=google-chrome
Type=Application
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;
EOF'
        echo "Desktop entry for Google Chrome created."
    else
        echo "Google Chrome desktop entry already exists."
    fi
}

# Ensure that the GUI configuration is correct
check_gui_configuration

echo "Setup complete. You can now run Google Chrome from the terminal or GUI menu."

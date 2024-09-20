#!/bin/bash

# Create the browsers directory if it doesn't exist
mkdir -p browsers

# Declare an array of Chrome URLs
chrome_urls=(
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/linux64/chrome-linux64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/mac-arm64/chrome-mac-arm64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/mac-x64/chrome-mac-x64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/win32/chrome-win32.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/win64/chrome-win64.zip"
)

# Declare an array of ChromeDriver URLs
chromedriver_urls=(
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/linux64/chromedriver-linux64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/mac-arm64/chromedriver-mac-arm64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/mac-x64/chromedriver-mac-x64.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/win32/chromedriver-win32.zip"
    "https://storage.googleapis.com/chrome-for-testing-public/131.0.6724.0/win64/chromedriver-win64.zip"
)

# Download Chrome files
for url in "${chrome_urls[@]}"; do
    echo "Downloading Chrome from $url..."
    curl -L "$url" -o "browsers/$(basename $url)"
done

# Download ChromeDriver files
for url in "${chromedriver_urls[@]}"; do
    echo "Downloading ChromeDriver from $url..."
    curl -L "$url" -o "browsers/$(basename $url)"
done

echo "All downloads completed."

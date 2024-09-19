# Use Alpine as base image
FROM python:3.10-alpine

ENV CONFIG_FILE=config.yaml
ENV API_CONFIG_FILE=confluence-api.json
ENV BROWSER_CONFIG_FILE=confluence-elements.json
ENV DOWNLOAD_DIR=/app/downloads
ENV LOG_LEVEL=info
ENV LOG_FILE=confluence-app.log
LABEL org.opencontainers.image.source=https://github.com/atonomic/confluence-spaces-tool
LABEL org.opencontainers.image.description="A tool to manage your confluence pages across confluence instances"
LABEL org.opencontainers.image.licenses=Apache

# Install necessary packages
RUN apk update && apk add --no-cache \
    bash \
    build-base \
    chromium \
    libffi-dev \
    tcl \
    tk \
    ttf-dejavu \
    wget \
    xvfb \
    && apk add --no-cache --virtual .build-deps gcc musl-dev python3-tkinter \
    && pip install --upgrade pip

# Copy your Python and config files to the container
COPY . /app
WORKDIR /app

# Make the install_browser.sh script executable
RUN sed -i 's/sudo //g' /app/scripts/install_browser.sh && \
    chmod +x /app/scripts/install_browser.sh && \
    /app/scripts/install_browser.sh && \
    pip install -r requirements.txt && \
    chown -R bot:bot /app

# Switch to the non-root user
USER bot

# Set DISPLAY environment variable
ENV DISPLAY=:99

CMD ["sh", "-c", "mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix && Xvfb :99 -screen 0 1024x768x16 & python3 main.py --config-file $CONFIG_FILE --api-config-file $API_CONFIG_FILE --browser-config-file $BROWSER_CONFIG_FILE --download-dir $DOWNLOAD_DIR --log-level $LOG_LEVEL --log-file $LOG_FILE"]

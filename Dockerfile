# Use Alpine as base image
FROM python:3.10-alpine

ENV CONFIG_FILE=config.yaml
ENV API_CONFIG_FILE=confluence-api.json
ENV BROWSER_CONFIG_FILE=confluence-elements.json
ENV DOWNLOAD_DIR=/app/downloads
ENV LOG_LEVEL=info
ENV LOG_FILE=confluence-app.log
ENV USER=bot
LABEL org.opencontainers.image.source=https://github.com/atonomic/confluence-spaces-tool
LABEL org.opencontainers.image.description="A tool to manage your confluence pages across confluence spaces"
LABEL org.opencontainers.image.licenses=Apache
LABEL org.opencontainers.image.vendor="Atonomic"
LABEL org.opencontainers.image.source=https://github.com/atonomic/confluence-spaces-tool
LABEL org.opencontainers.image.url=https://github.com/atonomic/confluence-spaces-tool
LABEL version="0.1.0"
LABEL org.opencontainers.image.licenses=Apache

RUN apk update && apk add --no-cache \
    bash build-base dbus-x11 libffi-dev py3-pip python3 shadow \
    tcl tcl-dev tk tk-dev ttf-dejavu wget xfce4 xfce4-terminal \
    xorg-server xvfb unzip chromium chromium-chromedriver nss \
    freetype harfbuzz ca-certificates ttf-freefont

RUN mkdir -p /app/chrome/browser && \
    ln -s /usr/bin/chromium-browser /app/chrome/browser/chrome && \
    ln -s /usr/bin/chromedriver /app/chrome/chromedriver

RUN apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install --upgrade pip && \
    pip install pipenv

WORKDIR /app

COPY . /app

RUN adduser -D -s /bin/bash "$USER" && \
    chown -R "$USER":"$USER" /app

USER "$USER"

RUN pipenv install --deploy

ENTRYPOINT ["pipenv", "run", "python", "main.py", "--config-file", "$CONFIG_FILE", "--api-config-file", "$API_CONFIG_FILE", "--browser-config-file", "$BROWSER_CONFIG_FILE", "--download-dir", "$DOWNLOAD_DIR", "--log-level", "$LOG_LEVEL", "--log-file", "$LOG_FILE"]

ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM $BUILD_FROM

RUN apk add --no-cache \
    python3 \
    py3-pip \
    iputils \
    bash \
    curl \
    sqlite

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages

COPY . /app
RUN chmod a+x /app/run.sh
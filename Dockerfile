ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip

# Copy data for add-on
COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

WORKDIR /app
COPY . /app

# Make run.sh executable
RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]
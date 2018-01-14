FROM python:3.6-alpine3.7

WORKDIR /app

# Download kindlegen, move to PATH and make executable
RUN wget -qO- http://kindlegen.s3.amazonaws.com/kindlegen_linux_2.6_i386_v2_9.tar.gz | tar -xzOf - kindlegen > /usr/local/bin/kindlegen
RUN chmod +x /usr/local/bin/kindlegen

# Install required system dependencies
RUN apk add --no-cache alpine-sdk openssl-dev libffi-dev libxml2-dev libxslt-dev

# Install python dependencies and copy scrapy config
COPY setup.py setup.cfg scrapy.cfg ./
RUN pip install -e .

# Install package again, now with actual code. No dependencies are installed this time, to enable fast docker builds when just the code has changed.
COPY safaribooks/ /app/safaribooks/
RUN pip install --no-index --no-deps -e .

VOLUME ["/app/converted"]

ENTRYPOINT ["safaribooks"]

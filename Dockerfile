FROM python:3.7.3-stretch

WORKDIR /app

COPY . /app

RUN python setup.py install

RUN mkdir /otmt-work

WORKDIR /otmt-work

# keep the container running so we can execute otmt commands
CMD ["tail", "-f", "/dev/null"]

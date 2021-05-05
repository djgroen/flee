FROM python:slim


RUN apt-get update &&\
	apt-get install -y --no-install-recommends git gcc libopenmpi-dev &&\
	apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}

RUN git clone --single-branch --branch=master https://github.com/djgroen/flee.git

WORKDIR flee

RUN pip install --no-cache-dir -r requirements.txt

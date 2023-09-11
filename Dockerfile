FROM python:3.9
COPY *py /usr/local/bin/
COPY *txt /usr/local/bin/
COPY *R /usr/local/bin/
### install python modules
RUN pip3 install -r /usr/local/bin/requirements.txt
#### install R
RUN apt-get update -y && \
    apt-get install -y r-base
#### install R libraries
RUN Rscript /usr/local/bin/install_packages.R
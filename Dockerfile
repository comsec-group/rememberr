FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install build-essential libpoppler-cpp-dev build-essential libpoppler-cpp-dev software-properties-common python3.8-dev libgl1 libglib2.0-0 software-properties-common git cm-super dvipng -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install python3.8 python3-pip python3-distutils python3-apt -y
RUN git clone https://github.com/comsec-group/rememberr.git
RUN pip3 install -r rememberr/requirements.txt
RUN cd rememberr && bash do_experiments.sh > experiments_stdout.log 2> experiments_stderr.log 
RUN cd rememberr && cat experiments_stdout.log | grep 'Number of Intel' > build/num_errata_intel.log
RUN cd rememberr && cat experiments_stdout.log | grep 'Number of AMD' > build/num_errata_amd.log
RUN cd rememberr && cat experiments_stdout.log | grep 'Blurry triggers' > build/num_blurry_triggers.log

FROM ubuntu:18.04
USER root
RUN apt-get update && apt-get install -y python3 python3-pip libclang1-6.0 g++ cmake && \
    pip3 install clang==6.0.0.2
RUN apt-get install -y git
RUN git clone  https://github.com/google/googletest && cd googletest && mkdir build && cd build && cmake .. && make -j$(nproc) install

# Use a base image with build tools installed
FROM buildpack-deps:buster

# Copy the entire project folder into the container
COPY ./ /app

# Set environment variables for Python builds
ENV PYTHON_36_VERSION 3.6.0
ENV PYTHON_311_VERSION 3.11.0
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/python3.6/lib
ENV PYTHONPATH /app/bpmn_python:$PYTHONPATH


RUN apt-get update && apt-get install -y \
  build-essential \
  libssl-dev \
  zlib1g-dev \
  curl

# Install Python 3.6.0
RUN set -ex \
  && wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_36_VERSION%%[a-z]*}/Python-$PYTHON_36_VERSION.tar.xz" \
  && mkdir -p /usr/src/python3.6 \
  && tar -xJC /usr/src/python3.6 --strip-components=1 -f python.tar.xz \
  && rm python.tar.xz \
  && cd /usr/src/python3.6 \
  && ./configure --enable-shared --prefix=/usr/local/python3.6 \
  && make -j$(nproc) \
  && make install \
  && curl https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py \
  && /usr/local/python3.6/bin/python3.6 get-pip.py
RUN /usr/local/python3.6/bin/pip install -r /app/requirements_3.6.txt

ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/python3.11/lib



# Install Python 3.11
RUN set -ex \
  && wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_311_VERSION%%[a-z]*}/Python-$PYTHON_311_VERSION.tar.xz" \
  && mkdir -p /usr/src/python3.11 \
  && tar -xJC /usr/src/python3.11 --strip-components=1 -f python.tar.xz \
  && rm python.tar.xz \
  && cd /usr/src/python3.11 \
  && ./configure --enable-shared --prefix=/usr/local/python3.11 \
  && make -j$(nproc) \
  && make install \
  && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
  && /usr/local/python3.11/bin/python3.11 get-pip.py
RUN /usr/local/python3.11/bin/pip install --upgrade pip setuptools wheel
RUN /usr/local/python3.11/bin/pip install -r /app/requirements_3.11.txt

RUN cd /


# Run the Python scripts
CMD /bin/bash -c "cd /app/3.6 && /usr/local/python3.6/bin/python3.6 /app/3.6/bpmnParsing.py"
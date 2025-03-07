# It's easier to use miniconda or we'll have to build python-boost manually.
FROM continuumio/miniconda3:24.9.2-0

ENV DELUGE_APP=/opt/deluge
ENV DELUGE_CONFIG_DIR=/var/lib/deluge
ENV DELUGE_DOWNLOAD_DIR=${DELUGE_CONFIG_DIR}/downloads
ENV DELUGE_TORRENTFILE_DIR=${DELUGE_CONFIG_DIR}/downloads
ENV DELUGE_PLUGINS_DIR=${DELUGE_CONFIG_DIR}/plugins

ENV DELUGE_RPC_PORT=6890
ENV DELUGE_LISTEN_PORTS=6891,6892
ENV DELUGE_DAEMON_USERNAME=user
ENV DELUGE_DAEMON_PASSWORD=password
ENV DELUGE_LOG_LEVEL=debug
ENV DELUGE_NODE_ID='unset'

RUN mkdir -p ${DELUGE_APP} ${DELUGE_CONFIG_DIR}
WORKDIR ${DELUGE_APP}

# SHELL modifies the shell form to a login shell so we
# can autoactivate the conda env at every RUN command.
SHELL ["/bin/bash", "--login", "-c"]

RUN conda create -y -n 'deluge' python=3.8

# Populates the .bashrc so that conda is initialized
# and the proper env is activated before every call to RUN.
RUN conda init bash
RUN echo "conda activate deluge" > ~/.bashrc

RUN if [ $(uname -m) = "aarch64" ]; then \
      conda install -y anaconda::py-boost \
        anaconda::gxx_linux-aarch64 \
        anaconda:openssl; \
    else \
      conda install -y anaconda::py-boost \
        anaconda::gxx_linux-64 \
        anaconda:openssl; \
    fi

COPY . ./

RUN git submodule update --init --recursive &&\
    cd vendor/libtorrent/bindings/python &&\
    python setup.py build_ext install

RUN pip install .

ENTRYPOINT ["bash", "--login", "-c", "${DELUGE_APP}/docker/bin/start.sh"]

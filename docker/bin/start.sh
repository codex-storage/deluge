#!/usr/bin/env bash
set -e

if [ -z "${DELUGE_EXTERNAL_IP}" ]; then
  echo "Warning: the listen IP address for the container has not been set."
  DELUGE_EXTERNAL_IP=$(hostname -i)
  echo "Using ${DELUGE_EXTERNAL_IP}"
  export DELUGE_EXTERNAL_IP
fi

cd "${DELUGE_APP}"
python ./docker/bin/create_config.py
python -m deluge.core.daemon_entry -c "${DELUGE_CONFIG_DIR}" -d -L "${DELUGE_LOG_LEVEL}"
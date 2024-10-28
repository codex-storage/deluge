# Simple wrapper on top of the Deluge config manager which allows us to generate
# an initial config file from env vars.
#
import copy
import os
import sys
from dataclasses import dataclass
from typing import Optional, Dict

from deluge.configmanager import ConfigManager, set_config_dir
from deluge.core.preferencesmanager import DEFAULT_PREFS


@dataclass
class ConfigOption:
    name: str
    description: str
    default: Optional[str] = None


OPTIONS = [
    ConfigOption(
        name='DELUGE_CONFIG_DIR',
        default='/var/lib/deluge',
        description='Directory where config files should be stored',
    ),
    ConfigOption(
        name='DELUGE_DOWNLOAD_DIR',
        default='/var/lib/deluge/downloads',
        description='Directory where download files should be stored after completion',
    ),
    ConfigOption(
        'DELUGE_TORRENTFILE_DIR',
        default='/var/lib/deluge/torrentfiles',
        description='Directory where known torrent files should be stored',
    ),
    ConfigOption(
        name='DELUGE_RPC_PORT',
        default='9889',
        description='Port on which to listen for RPC requests',
    ),
    ConfigOption(
        name='DELUGE_LISTEN_PORTS',
        default='6881,6891',
        description='Listen ports for DHT and transfer connections'
    ),
    ConfigOption(
        name='DELUGE_EXTERNAL_IP',
        description='IP on which to listen for connections',
    )
]


def read_options() -> Dict[str, str]:
    options = {}
    for opt in OPTIONS:
        if opt.name not in os.environ:
            if not opt.default:
                print(f'Required option missing {opt.name}: {opt.description}')
                sys.exit(1)
            value = opt.default
        else:
            value = os.environ[opt.name]

        options[opt.name] = value

    return options


def main():
    options = read_options()
    set_config_dir(options['DELUGE_CONFIG_DIR'])

    defaults = copy.deepcopy(DEFAULT_PREFS)

    defaults['random_port'] = False
    defaults['listen_random_port'] = None
    defaults['listen_interface'] = options['DELUGE_EXTERNAL_IP']
    defaults['outgoing_interface'] = options['DELUGE_EXTERNAL_IP']
    defaults['daemon_port'] = int(options['DELUGE_RPC_PORT'])
    defaults['download_location'] = options['DELUGE_DOWNLOAD_DIR']
    defaults['torrentfiles_location'] = options['DELUGE_TORRENTFILE_DIR']
    defaults['listen_ports'] = [int(p) for p in options['DELUGE_LISTEN_PORTS'].split(',')]

    manager = ConfigManager('core.conf', defaults=defaults)
    manager.save()


if __name__ == '__main__':
    main()

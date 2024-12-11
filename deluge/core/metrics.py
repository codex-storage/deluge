import json
import logging
import os
import re
from datetime import datetime, timezone

from prometheus_client import Counter

logger = logging.getLogger(__name__)

torrent_pieces_downloaded = Counter(
    name='deluge_torrent_pieces_downloaded',
    documentation='Number of pieces downloaded for a torrent',
    labelnames=['peer_id', 'torrent_name']
)

NID = re.compile(r'\(([a-zA-Z0-9]+)\)')


def metric_record(
        node: str,
        name: str,
        torrent_name: str,
        value: int,
):
    record = json.dumps({
        'entry_type': 'deluge_torrent_download',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'name': name,
        'value': value,
        'node': node,
        'torrent_name': torrent_name,
    })
    return f'>>{record}'


class Metrics:
    def __init__(self, core: 'deluge.core.Core'):
        # This is hack, we should add it to the deluge config.
        self.node_id = os.environ.get('DELUGE_NODE_ID', '<unset>')
        core.session.post_dht_stats()

    def handle_alert(self, alert):
        alert_type = alert.what()
        handler = getattr(self, f'_{alert_type}', lambda _: None)
        handler(alert)

    def _piece_finished(self, alert):
        logger.info(
            metric_record(
                node=self.node_id,
                name='deluge_piece_downloaded',
                torrent_name=alert.torrent_name,
                value=alert.piece_index,
            )
        )

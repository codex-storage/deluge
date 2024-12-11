import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Optional

from prometheus_client import Counter

logger = logging.getLogger(__name__)
for handler in logger.handlers:
    logger.removeHandler(handler)

logger.addHandler(logging.StreamHandler(sys.stdout))

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
        'node': node if node is not None else '',
        'torrent_name': torrent_name,
    })
    return f'>>{record}'

class Metrics:
    def __init__(self, core: 'deluge.core.Core'):
        self.peer_id: Optional[str] = None
        core.session.post_dht_stats()

    def handle_alert(self, alert):
        alert_type = alert.what()
        handler = getattr(self, f'_{alert_type}', lambda _: None)
        handler(alert)

    def _dht_stats(self, alert):
        # Since the node id is not exposed in the alert by libtorrent's Python binding,
        # we need to extract the digest from the string representation.
        result = NID.search(alert.message())
        if result is None:
            raise Exception('Could not extract node id from DHT stats alert')
        self.peer_id = result.group(1)

    def _piece_finished(self, alert):
        logger.info(
            metric_record(
                node=self.peer_id,
                name='deluge_piece_downloaded',
                torrent_name=alert.torrent_name,
                value=alert.piece_index,
            )
        )


import logging
import re
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO
from typing import Optional

from prometheus_client import Counter

logger = logging.getLogger('M')

torrent_pieces_downloaded = Counter(
    name='deluge_torrent_pieces_downloaded',
    documentation='Number of pieces downloaded for a torrent',
    labelnames=['peer_id', 'torrent_name']
)

NID = re.compile(r'\(([a-zA-Z0-9]+)\)')


class Metrics:
    def __init__(self, core: 'deluge.core.Core'):
        self.peer_id: Optional[str] = None
        self._buffer = StringIO()
        self.log_writer = DictWriter(
            f=self._buffer,
            fieldnames=['metric', 'timestamp', 'labels', 'value'],
        )
        self.log_writer.writeheader()
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
        labels = {
            'peer_id': self.peer_id if self.peer_id else '<unknown>',
            'torrent_name': alert.torrent_name,
        }

        torrent_pieces_downloaded.labels(**labels).inc(1)
        self.log_writer.writerow(
            dict({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metric': 'deluge_torrent_pieces_downloaded',
                'labels': ','.join(labels.values()),
                'value': alert.piece_index,
            })
        )

        logger.debug(self._buffer.getvalue())
        self._buffer.truncate(0)
        self._buffer.seek(0)

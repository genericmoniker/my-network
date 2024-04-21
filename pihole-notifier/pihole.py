"""Interface with Pi-Hole for monitoring blocked queries."""

import contextlib
from dataclasses import dataclass, field
import logging
import pathlib
import sqlite3
import time


# How often to poll the database for new blocked queries. FTL updates the
# database every minute by default. See https://docs.pi-hole.net/database/ftl/.
POLL_INTERVAL_SECONDS = 60

POLL_QUERY = """
    SELECT id, timestamp, status, domain, client
    FROM queries
    WHERE id >= ?
    AND status = 7  -- status 7 means blocked by upstream server.
    ORDER BY id DESC;
"""

LATEST_ENTRY_QUERY = """
    SELECT id
    FROM queries
    ORDER BY id DESC
    LIMIT 1;
"""

# Required fields here should match those selected in the POLL_QUERY.
@dataclass
class Entry:
    id: int
    timestamp: int
    status: int
    domain: str
    client: str
    categories: list[str] = field(default_factory=list)


logger = logging.getLogger(__name__)


class MonitorConfigError(Exception):
    """Raised when there is an error in the monitor configuration."""


def monitor(config, block_callback):
    """Monitor the Pi-Hole FTL database for blocked queries.

    Args:
        config (config.Config): The application configuration.
        block_callback (callable): A callback to invoke when a blocked query is
            detected. The callback should accept the configuration and a list of
            `Entry` named tuples.
    """
    if not config.FTL_DB_FILE:
        raise MonitorConfigError("FTL_DB_FILE config value not set.")

    db_path = pathlib.Path(config.FTL_DB_FILE)
    if not db_path.exists():
        raise MonitorConfigError(f"'{db_path}' not found.")

    logger.info("Monitoring Pi-Hole for blocks by the upstream DNS server...")

    while True:
        try:
            block_rows = _query_for_block_rows(db_path)
            if block_rows:
                entries = [Entry(*row) for row in block_rows]
                filtered_entries = []
                for entry in entries:
                    if entry.domain in config.WHITELIST:
                        logger.info("Skipping whitelisted domain: %s", entry.domain)
                        continue
                    filtered_entries.append(entry)
                if filtered_entries:
                    block_callback(config, filtered_entries)
        except Exception:
            logger.exception("Error in monitor loop.")


def _query_for_block_rows(db_path):
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            # Start by getting the last entry ID in the database, which is an
            # auto-increment field.
            cursor.execute(LATEST_ENTRY_QUERY)
            row = cursor.fetchone()
            logger.debug("Latest entry ID: %s", row)
            time.sleep(POLL_INTERVAL_SECONDS)
            if not row:
                return []
            # Now query for any blocked DNS queries with an ID greater than the
            # last one we saw.
            id_pos = row[0]
            cursor.execute(POLL_QUERY, (id_pos,))
            return cursor.fetchall()

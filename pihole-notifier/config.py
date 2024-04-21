import json
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


class Config:
    """Configuration for the Pi-Hole Notifier application.

    The configuration is loaded from secrets when available, with fallback to
    environment variables.
    """

    def __init__(self) -> None:
        # Load config from secrets, if possible.
        try:
            # The secret file is mounted in /run/secrets named after the secret
            # name (notifier_config), not the original name of the file
            # (notifier_config.json).
            secret_file = Path("/run/secrets/notifier_config")
            self._secret_conf = json.loads(secret_file.read_text())
            logger.info("Using config from secrets or environment.")
        except Exception as ex:
            self._secret_conf = {}
            logger.info("Using config from environment only. %s", ex)

        # Pi-Hole settings
        self.FTL_DB_FILE = self._get("FTL_DB_FILE")

        # Mail settings
        self.SMTP_HOST = self._get("SMTP_HOST")
        self.SMTP_PORT = self._get("SMTP_PORT")  # defaults to 465
        self.SMTP_USERNAME = self._get("SMTP_USERNAME")
        self.SMTP_PASSWORD = self._get("SMTP_PASSWORD")
        self.MAIL_SENDER = self._get("MAIL_SENDER")  # may be ignored by SMTP server
        self.MAIL_RECIPIENTS = self._get("MAIL_RECIPIENTS")

        # Don't send notifications for blocked domains listed here.
        raw = self._get("NOTIFIER_WHITELIST")
        self.WHITELIST = [d.strip() for d in raw.split(",")] if raw else []
        logger.debug("Whitelist: %s", self.WHITELIST)

        # Domain category lookup settings.
        self.CLOUDFLARE_API_KEY = self._get("CLOUDFLARE_API_KEY")
        self.CLOUDFLARE_ACCOUNT_ID = self._get("CLOUDFLARE_ACCOUNT_ID")

    def _get(self, key):
        """Get a config value.

        Tries to get the value from a secret file, otherwise from an environment
        variable. See https://docs.docker.com/compose/compose-file/#secrets
        """
        return self._secret_conf.get(key, os.getenv(key))

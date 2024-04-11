"""Main entry point for the Pi-Hole Notifier application."""
import logging
import sys

import config
import log
import notify
import pihole


logger = logging.getLogger(__name__)


def main():
    log.setup_logging(level=logging.INFO)
    logger.info("===== Pi-Hole Notifier Startup =====")

    conf = config.Config()

    try:
        pihole.monitor(conf, notify.notify)
    except pihole.MonitorConfigError as ex:
        logger.error(ex)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Device name lookup using an Eero router."""

import logging
from pathlib import Path
import eero


logger = logging.getLogger(__name__)


class _SessionStore(eero.SessionStorage):
    """Persistent storage for Eero session."""

    def __init__(self):
        self._cookie = None

    @property
    def cookie(self):
        if self._cookie is None:
            try:
                self._cookie = Path("/etc/eero/cookie").read_text()
            except FileNotFoundError:
                pass
        return self._cookie

    @cookie.setter
    def cookie(self, cookie):
        self._cookie = cookie
        Path("/etc/eero/cookie").write_text(cookie)


_session = _SessionStore()
_eero = eero.Eero(_session)


def get_device_name(ip_address: str) -> str:
    """Get a device name from an Eero router by IP address.

    For this to work, the Eero API must be authenticated. See the main
    function for how to do that.

    If the device is not found, return "unknown".
    """
    if _eero.needs_login():
        logger.warning("Unable to lookup name for %s. Eero needs login.", ip_address)
        return "unknown"

    try:
        account = _eero.account()
        for network in account["networks"]["data"]:
            devices = _eero.devices(network["url"])
            for device in devices:
                if device["ip"] == ip_address:
                    if device["nickname"]:
                        return device["nickname"]
                    if device["hostname"]:
                        return device["hostname"]
                    if device["display_name"]:
                        return device["display_name"]
                    logger.info("No good name found for %s.", ip_address)
                    return "unknown"
    except Exception:
        logger.exception("Error looking up device name for %s.", ip_address)

    return "unknown"


def main():
    """Log in to the Eero API and persist the session cookie.

    This allows the device name lookup to work when the notifier
    is running normally.

    In the case that this module is available in a Docker container,
    and the container has a volume mounted at /etc/eero,
    you can use a command something like this to run this script:

    docker exec -it pihole-notifier \
        /home/appuser/.venv/bin/python /home/appuser/lookup.py
    """
    try:
        identity = input("Eero email or phone: ").strip()
        token = _eero.login(identity)
        verification_code = input("Verification code from email or SMS: ").strip()
        _eero.login_verify(verification_code, token)
        print("Login successful.")
    except Exception as ex:
        print("Login failed.\n", ex)


if __name__ == "__main__":
    main()

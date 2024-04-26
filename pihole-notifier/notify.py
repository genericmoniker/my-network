"""Send notifications for blocked DNS lookups."""

import datetime
import http.client
import io
import json
import logging
import smtplib

import lookup
import mailer


logger = logging.getLogger(__name__)


def notify(config, entries):
    """Send a notification for each blocked domain."""
    if config.CLOUDFLARE_API_KEY and config.CLOUDFLARE_ACCOUNT_ID:
        _add_domain_categories(config, entries)

    for entry in entries:
        entry.client_name = lookup.get_device_name(entry.client)
        request_time = datetime.datetime.fromtimestamp(entry.timestamp)
        logger.info(
            "Upstream block at %s: %s (%s), client=%s (%s)",
            request_time,
            entry.domain,
            ", ".join(entry.categories) if entry.categories else "unknown",
            entry.client_name,
            entry.client,
        )

    try:
        with _configure_smtp(config) as client:
            mail = mailer.Mailer(client)
            mail.send_message(
                config.MAIL_RECIPIENTS,
                config.MAIL_SENDER,
                "DNS Block",
                _render_message_body(entries),
            )
    except Exception:
        logger.exception("Error sending mail.")


def _add_domain_categories(config, entries):
    """Add categories to each entry."""
    for entry in entries:
        categories = _lookup_domain_categories(config, entry.domain)
        entry.categories = categories


def _lookup_domain_categories(config, domain):
    """Lookup categories for a domain."""
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    url = f"/client/v4/accounts/{config.CLOUDFLARE_ACCOUNT_ID}/intel/domain?domain={domain}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.CLOUDFLARE_API_KEY}",
    }

    conn.request("GET", url=url, headers=headers)

    res = conn.getresponse()
    data = res.read().decode("utf-8")
    content = json.loads(data)
    if res.status != 200:
        logger.error("Error looking up domain categories: %s", content)
        return []
    if not content.get("success", False):
        logger.error("Error looking up domain categories: %s", content)
        return []
    categories = content.get("result", {}).get("content_categories", [])
    unique_categories = set(category["name"] for category in categories)
    return sorted(category for category in unique_categories)


def _configure_smtp(config):
    client = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT)
    client.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
    return client


def _render_message_body(entries):
    buffer = io.StringIO()
    print("DNS lookup(s) blocked by upstream sever:", file=buffer)
    print(file=buffer)
    for entry in entries:
        logger.debug("Entry: %s", entry)
        request_time = datetime.datetime.fromtimestamp(entry.timestamp)
        categories = f"{', '.join(entry.categories)}" if entry.categories else ""
        print(
            "-",
            request_time,
            entry.domain,
            f"(from {entry.client_name} {entry.client})",
            file=buffer,
        )
        print("  Categories:", categories, file=buffer)
    print(file=buffer, flush=True)
    body = buffer.getvalue()
    logger.debug("Message: %s", body)
    return body


# Entry point for testing notifications without running the main application:
if __name__ == "__main__":
    from config import Config
    from pihole import Entry

    config = Config()
    entry = Entry(1, 1250000, 7, "google.com", "1.2.3.4")
    notify(config, [entry])

# My network setup

- Pi-hole ad blocking
- Custom DNS block notifier
- WireGuard VPN
- Inadyn dynamic DNS updater
- etc.

First make sure that the mount directories (see docker-compose.yml) exist and
that your user owns them (and not root). For example:

```
sudo chown -R $USER ~/mounts
```

Secrets and other instance-specific settings go in `.env` at the project root.

Start/update:

```
ssh kylo
cd my-network
docker compose up --build --detach --pull always
```

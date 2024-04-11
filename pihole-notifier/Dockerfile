# notifier dockerfile

# I think pi-hole is using bullseye, so hopefully some shared layers.
FROM python:3.12-slim-bullseye

RUN useradd --create-home appuser
WORKDIR /home/appuser

RUN export DEBIAN_FRONTEND=noninteractive && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y --no-install-recommends tini && \
  apt-get -y clean && \
  rm -rf /var/lib/apt/lists/*

USER appuser
COPY --chown=appuser . .

ENTRYPOINT ["tini", "--", "python3", "main.py"]
# To debug the container: ENTRYPOINT ["tail", "-f", "/dev/null"]

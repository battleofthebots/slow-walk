FROM ghcr.io/battleofthebots/slow-walk-base-image:latest

COPY scripts/start.sh /scripts/start.sh
COPY scripts/initialize_runner.py /scripts/initialize_runner.py
RUN chmod +x /scripts/start.sh
CMD /scripts/start.sh

HEALTHCHECK --interval=60s --timeout=30s --retries=5 \
CMD /opt/gitlab/bin/gitlab-healthcheck --fail --max-time 10
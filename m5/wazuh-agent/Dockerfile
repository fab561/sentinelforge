# Wazuh Agent — SentinelForge M5
# Multi-arch: builds on amd64 (laptop) and arm64 (Raspberry Pi)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add Wazuh repository
RUN curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH \
    | gpg --no-default-keyring \
          --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg \
          --import \
    && chmod 644 /usr/share/keyrings/wazuh.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] \
    https://packages.wazuh.com/4.x/apt/ stable main" \
    | tee /etc/apt/sources.list.d/wazuh.list

# Install agent — WAZUH_MANAGER sets server address at install time
ARG WAZUH_MANAGER=wazuh-manager
RUN apt-get update && \
    WAZUH_MANAGER=${WAZUH_MANAGER} apt-get install -y wazuh-agent && \
    rm -rf /var/lib/apt/lists/*

# Copy config files
COPY ossec.conf /var/ossec/etc/ossec.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

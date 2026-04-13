#!/bin/bash
# Wazuh Agent entrypoint — SentinelForge M5
# Waits for wazuh-manager, then starts agent daemons.

set -e

MANAGER_HOST="${WAZUH_MANAGER:-wazuh-manager}"
MANAGER_PORT="${WAZUH_MANAGER_PORT:-1514}"
MAX_WAIT=120  # seconds to wait for manager
COWRIE_LOG_DIR="/var/log/cowrie"

echo "[M5] Wazuh agent starting..."
echo "[M5] Manager: ${MANAGER_HOST}:${MANAGER_PORT}"

# ── Ensure Cowrie log directory exists ──────────────────────────
mkdir -p "${COWRIE_LOG_DIR}"

# Create empty cowrie.json if not present (prevents log collector errors)
if [ ! -f "${COWRIE_LOG_DIR}/cowrie.json" ]; then
    touch "${COWRIE_LOG_DIR}/cowrie.json"
    echo "[M5] Created empty ${COWRIE_LOG_DIR}/cowrie.json"
fi

# ── Wait for Wazuh manager to be reachable ─────────────────────
echo "[M5] Waiting for wazuh-manager at ${MANAGER_HOST}:${MANAGER_PORT}..."
WAITED=0
until timeout 2 bash -c ">/dev/tcp/${MANAGER_HOST}/${MANAGER_PORT}" 2>/dev/null; do
    if [ "${WAITED}" -ge "${MAX_WAIT}" ]; then
        echo "[M5] ERROR: Manager not reachable after ${MAX_WAIT}s — starting anyway"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "[M5] Still waiting... (${WAITED}s)"
done
echo "[M5] Manager reachable (or timeout reached) — starting agent"

# ── Patch ossec.conf manager address (supports env override) ───
sed -i "s|<address>wazuh-manager</address>|<address>${MANAGER_HOST}</address>|g" \
    /var/ossec/etc/ossec.conf

# ── Start Wazuh agent ──────────────────────────────────────────
/var/ossec/bin/wazuh-control start

echo "[M5] Agent started. Tailing logs..."

# Keep container alive + stream agent logs
tail -F /var/ossec/logs/ossec.log 2>/dev/null || \
    while true; do sleep 30; done

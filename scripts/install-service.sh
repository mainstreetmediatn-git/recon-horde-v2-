#!/usr/bin/env bash
set -euo pipefail

install -d -m 0750 /opt/horde
install -d -m 0750 /var/lib/horde
install -m 0644 deploy/systemd/horde-worker@.service /etc/systemd/system/horde-worker@.service
systemctl daemon-reload
echo 'Service installed. Configure /etc/horde/%i.env, then enable horde-worker@atlas.'

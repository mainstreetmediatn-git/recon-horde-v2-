#!/usr/bin/env bash
set -euo pipefail

command -v apt-get >/dev/null || { echo 'apt-get is required for this installer'; exit 1; }
sudo apt-get update
for package in dnsutils nmap; do
  if ! dpkg -s "$package" >/dev/null 2>&1; then sudo apt-get install -y "$package"; fi
done
echo 'Optional tools installed where available. Native Python adapters remain the default.'

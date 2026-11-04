#!/usr/bin/env bash
# Copy one device's certificate and key into the firmware before building/flashing it.
#   ./provision.sh esp32-living [certdir]
set -euo pipefail
DEV=$1; CERTS=${2:-../security/certs}; cd "$(dirname "$0")"
mkdir -p main/certs
cp "$CERTS/ca.crt" main/certs/ca.crt; cp "$CERTS/$DEV.crt" main/certs/device.crt; cp "$CERTS/$DEV.key" main/certs/device.key
echo "provisioned $DEV (set CONFIG_DEVICE_ID=$DEV and CONFIG_ROOM in menuconfig; key: $(cat "$CERTS/$DEV.aeskey" | cut -c1-6)...)"

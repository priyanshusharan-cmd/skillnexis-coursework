#!/usr/bin/env bash
# Private CA + broker certificate + one client certificate per device (ECDSA P-256, as fast on an ESP32 as RSA-2048 is slow).
# Keys never leave this folder and are git-ignored: run this once per installation, then flash each device with its own cert.
#   ./security/gen_certs.sh [outdir]      default: security/certs
set -euo pipefail
OUT=${1:-$(dirname "$0")/certs}
mkdir -p "$OUT" && cd "$OUT"
DAYS=825
key() { openssl ecparam -name prime256v1 -genkey -noout -out "$1.key" 2>/dev/null; chmod 600 "$1.key"; }

key ca
openssl req -x509 -new -key ca.key -sha256 -days 3650 -subj "/O=SmartHome/CN=SmartHome Root CA" -out ca.crt \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:0" -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash"
LEAF="keyUsage=critical,digitalSignature\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\nbasicConstraints=critical,CA:FALSE"

key broker
openssl req -new -key broker.key -subj "/O=SmartHome/CN=localhost" -out broker.csr
printf "subjectAltName=DNS:localhost,DNS:smarthome.local,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n$LEAF\n" > broker.ext
openssl x509 -req -in broker.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days $DAYS -sha256 -extfile broker.ext -out broker.crt 2>/dev/null

# the certificate CN becomes the MQTT username (use_identity_as_username), which the ACL file keys on
for c in esp32-living esp32-bedroom hub phone voice; do
  key "$c"
  openssl req -new -key "$c.key" -subj "/O=SmartHome/CN=$c" -out "$c.csr"
  printf "extendedKeyUsage=clientAuth\n$LEAF\n" > client.ext
  openssl x509 -req -in "$c.csr" -CA ca.crt -CAkey ca.key -CAcreateserial -days $DAYS -sha256 -extfile client.ext -out "$c.crt" 2>/dev/null
done
# 256-bit end-to-end payload keys, one per device, shared only between that device and the hub
for c in esp32-living esp32-bedroom; do openssl rand -hex 32 > "$c.aeskey"; chmod 600 "$c.aeskey"; done
rm -f ./*.csr ./*.ext ./*.srl
echo "certificates in $OUT"

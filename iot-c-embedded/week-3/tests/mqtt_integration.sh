#!/bin/sh
# Starts a private Mosquitto, runs the station for 12 s, sends one command, and checks what the broker saw.
set -eu
PORT=${PORT:-18883}
TMP=$(mktemp -d)
printf 'listener %s 127.0.0.1\nallow_anonymous true\n' "$PORT" > "$TMP/mosq.conf"
mosquitto -c "$TMP/mosq.conf" > "$TMP/broker.log" 2>&1 &
BROKER=$!
trap 'kill $BROKER 2>/dev/null; rm -rf "$TMP"' EXIT
sleep 1
timeout 16 mosquitto_sub -h 127.0.0.1 -p "$PORT" -t 'weather/#' -v > "$TMP/seen.txt" &
sleep 0.5
( sleep 6; mosquitto_pub -h 127.0.0.1 -p "$PORT" -t weather/ws-test/cmd -m 'interval=1' ) &
./build/station_pc 127.0.0.1 "$PORT" 12 ws-test > "$TMP/station.txt"
sleep 4
fail=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
check "status online published"         'grep -q "^weather/ws-test/status online" "$TMP/seen.txt"'
check "at least 8 JSON readings"         '[ "$(grep -c "^weather/ws-test/state {" "$TMP/seen.txt")" -ge 8 ]'
check "readings carry t, h, p and seq"   'grep "^weather/ws-test/state" "$TMP/seen.txt" | tail -1 | grep -Eq "\"seq\":[0-9]+,\"t\":[0-9.]+,\"h\":[0-9.]+,\"p\":[0-9.]+"'
check "command received by station"      'grep -q "interval is now 1000 ms" "$TMP/station.txt"'
check "faster publishing after command"  '[ "$(grep -c "^\[pub\]" "$TMP/station.txt")" -ge 9 ]'
check "clean offline status at the end"  'tail -1 "$TMP/seen.txt" | grep -q "status offline"'
cp "$TMP/seen.txt" results/mqtt-capture.txt
cp "$TMP/station.txt" results/station-pc-run.txt
exit $fail

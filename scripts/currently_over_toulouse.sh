#!/usr/bin/env sh

TOULOUSE_LAT="43.6045"
TOULOUSE_LNG="1.444"
SEARCH_RAD=5
ALT=0
CAT=0

SATS_URL="https://revontulet.lol/api/satellites?lat=$TOULOUSE_LAT&lng=$TOULOUSE_LNG&cat=$CAT&alt=$ALT&search_radius=$SEARCH_RAD"

curl -s -X 'GET' \
  "$SATS_URL" \
  -H 'accept: application/json' | jq -r '.above | map(.satid) | .[:4] | join(",")'

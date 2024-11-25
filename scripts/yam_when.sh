#!/usr/bin/env bash

YAM_5=55076
TOULOUSE_LAT="43.6045"
TOULOUSE_LNG="1.444"
SEARCH_RAD=5
ALT=0
CAT=0

YAM_5_TOULOUSE=$(curl -s -X "GET" \
    "https://revontulet.lol/api/satellite?norad_id=$YAM_5&lat=$TOULOUSE_LAT&lng=$TOULOUSE_LNG&tz=America/Los_Angeles" \
    -H "Accept: application/json" | jq -r '.[0].culmination.client_time')

echo -e "YAM-5 will be over Toulouse at: $YAM_5_TOULOUSE"

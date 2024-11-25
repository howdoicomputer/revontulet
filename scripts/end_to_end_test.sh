#!/usr/bin/env bash

TOULOUSE_LAT="43.6045"
TOULOUSE_LNG="1.444"
SEARCH_RAD=5
ALT=0
CAT=0

echo -e "This script will query out satellites over a location, reprocess them into sat_color_pairs, and then feed that back into the API"
echo -e "in order to create a representation of functionality.\n"

echo -e "Toulouse latitutde: $TOULOUSE_LAT"
echo -e "Toulouse longitude: $TOULOUSE_LNG"
echo -e "Search Radius: $SEARCH_RAD"
echo -e "Altitude: $ALT"
echo -e "Category ID: $CAT"

SATS_URL="https://revontulet.lol/api/satellites?lat=$TOULOUSE_LAT&lng=$TOULOUSE_LNG&cat=$CAT&alt=$ALT&search_radius=$SEARCH_RAD"
echo -e "First curl URL: $SATS_URL\n"

# Get a list of four satellites currently over Toulouse
#
# We just want ANY set of satellites in order to do an
# end to end holistic test of the system.
#
SATS=$(curl -s -X 'GET' \
  "$SATS_URL" \
  -H 'accept: application/json' | jq -r '.above | map(.satid) | .[:4] | join(",")')

# Use some bash to create sat_color_pairs. I.E, id,blue,id,red
COLORS=("blue" "red" "yellow" "green" "purple" "orange")

IFS=',' read -r -a SAT_ARRAY <<< "$SATS"

RESULT=""
for i in "${!SAT_ARRAY[@]}"; do
  SAT_ID="${SAT_ARRAY[$i]}"
  COLOR="${COLORS[$((i % ${#COLORS[@]}))]}" # Cycle through colors
  RESULT+="$SAT_ID,$COLOR,"
done

SAT_COLOR_PAIRS=${RESULT%,}

echo -e "Resolved these sat_color_pairs: $SAT_COLOR_PAIRS\n"

echo -e "Satellites (with their colors) currently above Toulouse, France:\n"

# Then we want to pass in those satellites as sat_color_pairs
# in order to test the /api/satellites/above endpoint.
#
ABOVE_URL="https://revontulet.lol/api/satellites/above?lat=$TOULOUSE_LAT&lng=$TOULOUSE_LNG&cat=$CAT&alt=$ALT&search_radius=$SEARCH_RAD&sat_color_pairs=$SAT_COLOR_PAIRS"
echo -e "Fetch above URL: $ABOVE_URL\n"

curl -s -X "GET" \
    "$ABOVE_URL" \
    -H "accept: application/json"

echo -e "\nThe same satellites but in text format:\n"

ABOVE_TEXT_URL="$ABOVE_URL&format=text"

# Then we want to pass in those satellites as sat_color_pairs
# in order to test the /api/satellites/above endpoint.
#
curl -s -X "GET" \
    "$ABOVE_TEXT_URL" \
    -H "accept: application/json"

echo -e "\nOkay now let's verify streaming text:\n"

STREAM_URL="https://revontulet.lol/api/satellites/above/stream?lat=$TOULOUSE_LAT&lng=$TOULOUSE_LNG&cat=$CAT&alt=$ALT&search_radius=$SEARCH_RAD&sat_color_pairs=$SAT_COLOR_PAIRS&format=text"

echo -e "\nStream URL: $STREAM_URL\n"

curl -s -X "GET" \
  "$STREAM_URL" \
  -H "accept: application/json"

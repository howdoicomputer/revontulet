# About

This directory has a bunch of utility scripts that I use to validate functionality, demonstrate usage, and satisfy curiousity.

# end_to_end_test.sh

**Requirements:** bash, curl, jq

Will query out a list of satellites currently flying over Toulouse, France. It will then build out a sat_color_pair string "<norad_id>,color,<norad_id>,color" and send that to `/api/satellites/above/stream` with Toulouse's coordinates in order to emit color notifications for those satellites.

## Purpose

It helps provide immediate feedback on whether or not the system is working on a basic level. You can open up take the emitted satellite data and open up N2YO and check to see where the satellites are.

## Usage

`./end_to_end_test.sh`

# currently_over_toulouse.sh

**Requirements:** bash, curl, jq

Will query out a list of satellites curently over Toulouse.

## Purpose

Nice utility. Helps to quickly get some real data for other tests.

## Usage

`./currently_over_toulouse.sh`

# client_example.py

**Requirements:** Python3

An example of consuming the `/api/satellites/above/stream` endpoint using Python's stdlib.

Gets HTTP query parameters from `client_example_config.json`. You can use `currently_over_toulouse.sh` to get some satellite IDs.

## Purpose

A demonstration of writing a thin client that will receive a stream of satellite tracking data.

## Usage

`./client_example.py`

# client_example_go.go

**Requirements:** go

Same as `client_example.py`. Uses the same config file. Also using only stdlib.

## Purpose

Same as the Python example but showing consumption in another language.

## Usage

`go run client_example_go.go`

# yam_when.sh

Queries out when YAM-5 will be over Toulouse. Outputs data in `America/Los_Angeles`.

## Purpose

I think it's neat.

## Usage

`./yam_when`

# Revontulet | About

Revontulet is an API that - given a set of coordinates, NORAD_ID ids, and colors - will continuously check to see if the provided satellites are over the provided coordinates and then emit light commands if they are.

For example, this curl command hits the `/api/satellites/above/stream` endpoint with these parameters:

| Parameter          | Value                                          | Description                                  |
|--------------------|------------------------------------------------|----------------------------------------------|
| `lat`              | `43.6045`                                     | Latitude of the observer.                   |
| `lng`              | `1.444`                                       | Longitude of the observer.                  |
| `search_radius`    | `90`                                          | Search radius in degrees around the observer.|
| `sat_color_pairs`  | `10155,blue,11690,red,12818,yellow,14277,green`| Comma-separated list of NORAD_ID ID and colors. |
| `format`           | `text`                                        | Response format (`text` or `json`).         |


``` sh
curl -X 'GET' \
  'http://localhost:8000/api/satellites/above/stream?lat=43.6045&lng=1.444&search_radius=90&sat_color_pairs=10155,blue,11690,red,12818,yellow,14277,green&format=text' \
  -H 'accept: application/json'
```

And we get back this response as an HTTP stream on a 10 second timer (notice that yellow is missing; it wasn't flying over those coordinates at the time).

``` sh
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
NORAD_ID_10155: blue, NORAD_ID_11690: red, NORAD_ID_14277: green
```

# How it works

## Upstream APIs and caching

This API sends requests to two upstream APIs: https://sat.terrestre.ar/docs/#/ and https://www.n2yo.com/api/

There are home built API clients for both in `libs/` that use httpx to asynchronously fetch API results and then cache them on a 10 second TTL
if the responses are 200s.

## Typing and Pydantic

The routes themselves use those clients to fetch data and then filter and annotate the results. The codebase makes extensive use of Pydantic models to provide documented, typed, and validated interfaces for both the API routes and internal functions.

## Testing

The external routes are tested using pytest with mocks and stubbed out data. The mocks and stubs allows our tests to be ran without secret injection as well.

An end-to-end test exists in `scripts/end_to_end_test.sh` that is convenient for me to use. It will curl `/api/satellites` to resolve a set of satellites currently over a coordinate pair and then create a `sat_color_pair` string to feed into the `/api/satellites/above` endpoint to resolve satellites and their color data for a location.

For example,

``` sh
revontulet/scripts main*​
revontulet-py3.13 ❯ ./end_to_end_test.sh
This script will query out satellites over a location, reprocess them into a sat_color_pair, and then feed that back into the API
in order to create a representation of functionality.

Toulouse latitutde: 43.6045
Toulouse longitude: 1.444
Search Radius: 15
Altitude: 0
Category ID: 0
Resolved these sat_color_pairs: 5680,blue,6302,red,13603,yellow,14607,green

Satellites (with their colors) currently above Toulouse, France:

[{"norad_id":5680,"color":"blue"},{"norad_id":6302,"color":"red"},{"norad_id":13603,"color":"yellow"},{"norad_id":14607,"color":"green"}]
The same satellites but in text format:

"NORAD_ID_5680: blue, NORAD_ID_6302: red, NORAD_ID_13603: yellow, NORAD_ID_14607: green"⏎
```

# Routes

## /api/satellite

This route queries out a single satellite.

``` sh
curl -X 'GET' \
  'http://0.0.0.0:8000/api/satellite?norad_id=8018&lat=43.6045&lng=1.444&days=1&limit=1&tz=America%2FLos_Angeles' \
  -H 'accept: application/json'
```

``` sh
[
  {
    "rise": {
      "alt": "10.00",
      "az": "331.95",
      "az_octant": "NW",
      "utc_datetime": "2024-11-23 11:34:55.644424+00:00",
      "utc_timestamp": 1732361695,
      "is_sunlit": true,
      "visible": false,
      "client_time": "2024-11-23 03:34:55 PST"
    },
    "culmination": {
      "alt": "29.96",
      "az": "315.83",
      "az_octant": "NW",
      "utc_datetime": "2024-11-23 13:26:06.053063+00:00",
      "utc_timestamp": 1732368366,
      "is_sunlit": true,
      "visible": false,
      "client_time": "2024-11-23 05:26:06 PST"
    },
    "set": {
      "alt": "10.00",
      "az": "296.41",
      "az_octant": "NW",
      "utc_datetime": "2024-11-23 16:09:15.689282+00:00",
      "utc_timestamp": 1732378155,
      "is_sunlit": true,
      "visible": false,
      "client_time": "2024-11-23 08:09:15 PST"
    },
    "visible": false,
    "norad_id": 8018
  }
]
```

The response is similar to the response given by the Terrestare Pass API except that you can pass in a timezone to get a localized client_time field.

## /api/satellites

This endpoint is a proxy for the N2YO API. It exists only to provide base access and to help perform holistic system smoke tests.

For example, to get the list of satellites over Toulouse, France (with a 15 degree search radius):

``` sh
curl -s -X 'GET' \
  'http://0.0.0.0:8000/api/satellites?lat=43.6045&lng=1.444&cat=0&alt=0&search_radius=15' \
  -H 'accept: application/json'
```

## /api/satellites/above|stream

This endpoint is the meat and potatoes. It is delicious and hardy.

``` sh
curl -X 'GET' \
  'http://0.0.0.0:8000/api/satellites/above?lat=43.6045&lng=1.444&search_radius=90&sat_color_pairs=11690,blue&format=text' \
  -H 'accept: application/json'
```

``` sh
"NORAD_ID_11690: blue"⏎
```

`/api/satellites/above/stream` does the same using server sent events over an HTTP stream

## /api/satellites/above/profile|stream

This route is the same as above but uses profiles for predeclared locations. For example, in `config.py` you will see entries for Toulouse, France, Golden, CO, and San Francisco, CA. Each location has a set of sat_color_pairs. Instead of setting in HTTP query parameters that specifies lat/lng coordinates, sat_color_pairs, etc, a client can lean on a profile for a simpler request.

``` sh
curl -N "http://localhost:8000/api/satellites/above/profile/stream?name=golden&format=json&search_radius=90"
```

## /metrics

Revontulet exposes Prometheus metrics.

## Profiles

Profiles are a way for Revontulet to help clients be even more thin. They are preconfigured locations that already include lat/lng coordinates and sat_color_pairs.

For example, in `config.py` here are the default profiles:

``` sh
class Settings(BaseSettings):
    n2yo_api_key: str = Field(..., description="The API key for N2YO")
    office_profiles: List[Office] = Field(
        default=[
            Office(
                name="toulouse",
                lat="43.6045",
                lng="1.444",
                sat_color_pairs=[
                    SatColorPair(norad_id="55076", color="blue"),
                    SatColorPair(norad_id="48915", color="white"),
                    SatColorPair(norad_id="59126", color="red"),
                ],
            ),
            Office(
                name="sf",
                lat="37.7749",
                lng="-122.4194",
                sat_color_pairs=[
                    SatColorPair(norad_id="55076", color="red"),
                    SatColorPair(norad_id="48915", color="white"),
                    SatColorPair(norad_id="59126", color="blue"),
                ],
            ),
            Office(
                name="golden",
                lat="39.7555",
                lng="-105.2211",
                sat_color_pairs=[
                    SatColorPair(norad_id="55076", color="red"),
                    SatColorPair(norad_id="48915", color="white"),
                    SatColorPair(norad_id="59126", color="blue"),
                ],
            ),
        ],
        description="A list of all office profiles",
    )
```

If you want to change the defaults then create `config.json` and place a new set of profiles for Revontulet to load.

# Configuration

There is really only configuration value **required** and that's an `N2YO_API_KEY`. There is an `sample-envrc` in this repository that you can modify and then `cp sample-envrc ./.envrc` to use direnv to autoload that key for development.

However, you are able to override profiles in a `config.json` file. Revontulet is able to start without that configuration file. Additionally, you can specify a `n2yo_api_key` value in that configuration file but it will take backseat to the environment variable equivalent.

# Development Environment

There is a `Makefile` that helps ease development. Check out its
directives to see what it can do.

## Requirements

* Poetry
* Pyenv
* GNU Make

## Setup

This project uses Poetry to manage dependencies. Follow the install instructions for that project and then run `poetry install`

# Shipping a Version

The Makefile, by default, uses my Dockerhub username and account. You'll need to change it if you want to take ownership of this.

It's instructions look like this:

``` sh
build:
	poetry export --without-hashes --format=requirements.txt > requirements.txt
	docker build . -t revontulet-api:v$(VERSION)
```

Then Kubernetes manifests should then be updated to pull down that new version.

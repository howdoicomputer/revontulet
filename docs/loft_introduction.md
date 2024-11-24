# Loft Orbital Take Home

# My Solution

Nothing about the requirement specified that this had to be a CLI utility. Just that it had to be a Python application that took in some input and then spit out "NORAD_ID_1: blue, NORAD_ID_2: green".

Given those loose requirements, I went with what I felt like was the best solution: build an API that extends other satellite tracking APIs.

Revontulet is an API that extends and annotates, primarily, the N2YO API in order to provide the functionality requested.

## Why would you do this

I feel like this provided a lot of benefits:

* **Ease of validation**: I could host a URL that you could curl and see a result. There would be no setup requirements to test my application. All you would need was curl.
* **Clients can be flexible**: I didn't want to be constrained by the inflexiblity of a configuration file. I wanted to be able to quickly change coordinates, satellites, and color pairings.
* **Deployments for clients are simpler**: By keeping business logic in a central location, the implementation at the edge is thinner and so there is less to go wrong. The clients that control the lighting system just need to make one HTTP call and then feed the result into lights.
* **Easily extendable**: If I needed to support additional systems (say, a countdown clock that has an ETA for each satellite for a location) then I just add an API route that provides a countdown. Clients continue to stay thin.
* **A wee bit more secure**: I can deploy the API to an internal network and make sure that the network path that controls the lights only have access to that API. This makes the security model simpler as I would only have to worry about network access for the API.
* **Removes the burden from upstream APIs/scalable**: I don't know how many edge devices this solution can support *exactly* on a per node basis but this solution is extremely scalable (could put a light in every home). This is because every 200 request to upstream APIs is cached. That means that even if we have 1000 Raspberry Pis hitting the Revontulet API we wouldn't get throttled upstream because we would be serving cached data with a reasonable TTL.

## How do I validate this?

The OpenAPI/swagger docs are at: https://revontulet.lol/docs

The API is pretty flexible but, for ease of use, I provided "profiles" that track the YAM-* satellites over Toulouse, Golden, and San Francisco (I named the feature profiles).

Just run:

```
curl "https://revontulet.lol/api/satellites/above/profile/stream?name=toulouse&search_radius=90
```

This will open up an HTTP stream that *may* output something to your terminal. If none of the YAM-* sats are over Toulouse at a 90 degree search radius then you'll likely see nothing (womp, womp).

If you're not getting any output, that's okay. There is a script in
`scripts/end_to_end_test.sh` that will query out a list of satellites currently flying over Toulouse, assign some colors to them, and then make an API call to stream the output to your terminal (adjust the search radius as much as you'd like - I keep at 5 as I believe that is a good enough value to represent 'overhead'). There is a make directive so you can also `make e2e` to do a validation.

The output should look something like this:

```
...
Okay now let's verify streaming text:


Stream URL: https://revontulet.lol/api/satellites/above/stream?lat=43.6045&lng=1.444&cat=0&alt=0&search_radius=15&sat_color_pairs=7376,blue,12894,red,18357,yellow,24293,green&format=text

NORAD_ID_7376: blue, NORAD_ID_12894: red, NORAD_ID_18357: yellow, NORAD_ID_24293: green
NORAD_ID_7376: blue, NORAD_ID_12894: red, NORAD_ID_18357: yellow, NORAD_ID_24293: green
NORAD_ID_7376: blue, NORAD_ID_12894: red, NORAD_ID_18357: yellow, NORAD_ID_24293: green
NORAD_ID_7376: blue, NORAD_ID_12894: red, NORAD_ID_18357: yellow, NORAD_ID_24293: green
```

Something that I like to do for validation is take the outputted NORAD_IDs and open them up on the N2YO website to see where they are on a map:

https://www.n2yo.com/satellite/?s=28926#results

Nothing beats raw visual validation.

## Supporting both the requirements text and JSON

I felt like the requirements output data format ("NORAD_ID_1: green, NORAD_ID_2: blue") was weird. It's data that is meant to be read by machines yet it isn't easily serializable. Therefore I added a `format=json|text` to support both the requirements text and the a structured output (json).

# Requirements

## Must Haves

* Python `>=3.11` - I ended up using 3.13 as that was the latest stable release. Managed locally by pyenv.
* A `Dockerfile` - There is a Dockerfile and a Makefile that wraps the docker run to create it. I didn't feel like a docker-compose file was needed. You don't super need to do any setup due to my approach as there is a public endpoint.
* Additional libraries can be selected at will - I did.
* A README.md is expected to detail the chosen solution and how to run it.
* Relevant unit tests should be provided using pytest - I have written unit tests to test my API routes and a shell script to hit the public API
* Use Python type annotations - I didn't just use type annotations. I also used Pydantic to do data validation.

## Task Fulfillment

### Consume a configuration file...

My application can be configured either with environment variables or a configuration file. However, my approach has made a configuration file moot as you can just pass in some query parameters to a URL to capture the data that you would use in a config file. The configuration file is used to override the default "profiles."

### Uses a public API...

I wrote API clients for:

* https://www.n2yo.com/api/
* https://satellites.fly.dev/

I did find client libraries for the N2YO API but they tended to use the requests library. This was a problem as the requests library is synchronous and THAT would mean that every proxied API request would block the FastAPI event loop until the request was completed. I ended up using httpx to create asynchronous clients.

### If multiple satellites are passing over a location...

Let's use Toulouse as an example - and really we're restating here - there are two ways to emit what I call "sat_color_pairs" to represent a desired set of satellites flying over a location.

Toulouse has these coordinates: `43.6045, 1.444`

## First Example

This curl command hits the /api/satellites/above endpoint with those parameters, a search radius of 5, and a sat_color_pairs set of `{"38246", "blue", "51623": "red"}` (/api/satellites/above/stream does the same thing but opens an HTTP stream)

```
curl "https://revontulet.lol/api/satellites/above?lat=43.6045&lng=1.444&cat=0&alt=0&search_radius=5&sat_color_pairs=38246,blue,51623,red"

[{"norad_id":38246,"color":"blue"},{"norad_id":51623,"color":"red"}]
```

## Second Example

But let's say that we want our clients to be even lazier. In that case, we configure a "profile" - a preconfigured set of satellites, colors, and coordinates. Revontulet, by default, ships with three profiles: `sf`, `toulouse`, and `golden` (you can see these defaults set in `config.py`).

The default sets of satellites that I picked are three YAM satellites and I gave them the colors shared between the French and American flags.

Now our curl command looks like this:

```
curl "https://revontulet.lol/api/satellites/above/profile?name=toulouse&search_radius=5"
```

Really, a client running on a raspi can look like this:

```
curl <stream_endpoint> | write_to_lights.py
```

# Optional Tasks

## Provide a script or CI/CD pipeline...

I went with GitHub Actions. I thought about creating a [Dagger](https://dagger.io/) pipeline but had to reduce scope to ship. GitHub Actions took me, like, 5 minutes to setup as they had a preconfigured pylint action yml I could create. I just had to change it slightly to account for Poetry and then have it call my Makefile.

I do want to expand the pipeline to build and ship my container images. This is a bit more work as I would have to handle my Docker credentials and so, again, cut it to reduce scope.

## Isolate the dev and prod environment

Due to the way that the CI system is setup I didn't really need to do multi-stage builds. The image build sequence produces a container image that doesn't contain any dev environment dependencies and the CI system has its own build build process that produces a container that DOES have the dev dependencies.

This does leave the codebase in a situation where containers aren't used to run tests LOCALLY but when/if I get around to implementing Dagger based pipelines then the entire CI/CD process will be locally runnable and portable across any CI systems.

## My Optional Tasks

Here are some things I implemented:

* I added a Prometheus metric endpoint to the application
* The application is deployed on my Homelab (Nomad, Traefik, Lets Encrypt, Grafana, Prometheus, etc)
* I bought a domain (someone owes me two bucks)
* I created some Kubernetes manifests (they live in `deploy/k8s`) that use ArgoCD to deploy this to a GKE cluster
* I created multi-arch container image builds to support MacOS and AMD64 Linux
* I used Pydantic to be extra rigorous about typing for interfaces

## What would I change?

There is a long list:

* Version the API /api/v1/*
* Create a [Dagger](https://dagger.io/) pipeline for CI/CD
* Deploy a GCP environment with a k8s cluster with ArgoCD and deploy the application there (my homelab is free tho)
* Make profiles creatable via POST requests
* Use TLE to do local satellite predictions and drop the API requirements
* Structured logging, OpenTelemetry tracing, and further metric instrumentation
* Define SLIs and SLOs for the service and create alerts for them
* Create a GitHub Action that publishes my container image
* Better error reporting for API responses
* Move metrics to a dedicated port
* Create a healthcheck endpoint that validates upstream dependencies
* Expand and refine tests and maybe include behavioral tests
* Add an ETA for the /satellite call (so a client gets a countdown for when a specific satellite passes over an area)
* Write a React frontend to visualize the data
* Get a physical device working
* Multimodal state representation for lights I.E, a satellite can be approaching, directly overheaad, passing, or just not there. What if we had a light for each state?
* Use the aforementioned instrumentation to build Grafana dashboards

### Most important and immediate improvements

I would probably start with structured logging, opentelemetry tracing, and more metric instrumentation throughout the codebase.

Turns out that implmenting structured logging with FastAPI is kinda' difficult and finnicky. I wasted a couple of hours on it before cutting the feature to save scope.

I personally believe that most logs should structured so that you can pipe them into log ingestion pipelines. If a log stream isn't structured then you need to build log processing using something like Vector, FluentBit, FluentD, etc.

Distributed tracing that is compatible with OTel is also important. It's also kind of hard to get right so I didn't so I could deliver on time. However, distributed tracing is VERY cool and VERY useful.

Prometheus metrics are available but just for FastAPI. I also want to track metrics for upstream request failure rates.

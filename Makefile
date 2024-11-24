VERSION = 1

build:
	poetry export --without-hashes --format=requirements.txt > requirements.txt
	docker buildx build --platform linux/amd64,linux/arm64 . -t howdoicomputer/revontulet:v$(VERSION) --load

run:
	fastapi dev main.py

test:
	pytest .

lint:
	flake8
	mypy .

validate:
	pytest .
	flake8
	mypy .

push:
	docker buildx build --platform linux/amd64,linux/arm64 . -t howdoicomputer/revontulet:v$(VERSION) --push

shell:
	poetry shell

run-docker:
	docker run -d -p 8000:8000 -e N2YO_API_KEY=$N2YO_API_KEY --name revontulet-api howdoicomputer/revontulet

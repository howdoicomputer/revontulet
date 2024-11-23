VERSION = 1

build:
	poetry export --without-hashes --format=requirements.txt > requirements.txt
	docker build . -t revontulet-api:v$(VERSION)

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
	docker push howdoicomputer/revontulet:v$(VERSION)

shell:
	poetry shell

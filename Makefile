default: help

.PHONY: help test install coverage run dev build build-x86 docker-run docker-stop docker-rm redis

help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

test: # run unit tests for backend service
	poetry run isort .
	poetry run pre-commit run --all-files
	poetry run pycodestyle --ignore "E501, E402, W503, W504" app
	ENV=ci poetry run coverage run --source=app -m unittest -v
	poetry run coverage report
	poetry run coverage xml

install: # install dependencies
	poetry install
	poetry run pre-commit install
	@if [ ! -f .env ]; then\
		cp .env.example .env;\
	fi
	@echo ""
	@echo "##### install complete #####"
	@echo "Please fill in .env file"

coverage: # show coverage report
	poetry run coverage report

run: # run service without reload flag
	GOOGLE_APPLICATION_CREDENTIALS=config/gcp-service-account.json ENV=ci poetry run uvicorn app.main:app

dev: # run service with reload flag
	GOOGLE_APPLICATION_CREDENTIALS=config/gcp-service-account.json ENV=ci poetry run uvicorn app.main:app --reload

build: # build docker image
	docker build -t asia-east1-docker.pkg.dev/tw-rd-sa-zoe-lin/cloud-native-repository/cloud-native-backend .

build-x86: # build x86_64 docker image
	docker build --platform=linux/amd64 -t asia-east1-docker.pkg.dev/tw-rd-sa-zoe-lin/cloud-native-repository/cloud-native-backend .

docker-run: # run docker container with newest image of "cloud-native", backend port would be 8000
	docker run -d --name cloud-native-backend -p 8000:80 cloud-native-backend

docker-stop: # stop cloud-native container
	docker stop cloud-native-backend

docker-rm: # rm cloud-native container
	docker rm cloud-native-backend

redis: # run redis docker
	docker run -d --rm --name redis -p 6379:6379 redis

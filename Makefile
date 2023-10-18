default: help

.PHONY: help test coverage run dev docker-build docker-build-x86 docker-run docker-stop docker-rm

help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

test: # run unit test for backend service
	ruff .
	coverage run -m unittest

coverage: # show coverage report
	coverage report

run: # run service without reload flag
	uvicorn main:app

dev: # run service with reload flag
	uvicorn main:app --reload

docker-build: # build docker image
	docker build -t cloud-native .

docker-build-x86: # build x86_64 docker image
	docker build --platform=linux/amd64 -t cloud-native .

docker-run: # run docker container with newest image of "cloud-native", backend port would be 8000
	docker run --name cloud-native -p 8000:80 cloud-native

docker-stop: # stop cloud-native container
	docker stop cloud-native

docker-rm: # rm cloud-native container
	docker rm cloud-native
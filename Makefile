default: help

.PHONY: help test coverage run dev docker-build docker-build-x86 docker-run docker-stop docker-rm redis

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

build: # build docker image
	docker build -t cloud-native .

build-x86: # build x86_64 docker image
	docker build --platform=linux/amd64 -t cloud-native .

docker-run: # run docker container with newest image of "cloud-native", backend port would be 8000
	docker run -d --name cloud-native -p 8000:80 cloud-native

docker-stop: # stop cloud-native container
	docker stop cloud-native

docker-rm: # rm cloud-native container
	docker rm cloud-native

redis: # run redis docker
	docker run -d --rm --name redis -p 6379:6379 redis

helm: # helm upgrade
	helm upgrade cloud-native-backend deploy --install --namespace=cloud-native  --values deploy/values.yaml

NODE_PORT := $(shell kubectl get --namespace cloud-native -o jsonpath="{.spec.ports[0].nodePort}" services cloud-native)
NODE_IP := $(shell kubectl get nodes --namespace cloud-native -o jsonpath="{.items[0].status.addresses[0].address}")

show_url:
	echo http://$(NODE_IP):$(NODE_PORT)

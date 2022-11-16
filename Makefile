.PHONY: help
help:
	@echo "make build         # build docker image"
	@echo "make push          # push docker image"
	@echo "make login         # get aws ecr login"
	@echo "make help          # show this help"

.PHONY: build
build:
	docker build -t su-bill-report .
	docker tag su-bill-report:latest 948691256895.dkr.ecr.eu-west-2.amazonaws.com/su-bill-report:$(version)

.PHONY: login
login:
	aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 948691256895.dkr.ecr.eu-west-2.amazonaws.com

.PHONY: push
push:
	docker push 948691256895.dkr.ecr.eu-west-2.amazonaws.com/su-bill-report:$(version)
	
.PHONY: flake8
flake8:
	flake8 .
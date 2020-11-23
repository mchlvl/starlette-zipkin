.DEFAULT_GOAL := help
.PHONY: run requirements install requirements build publish tests help
.EXPORT_ALL_VARIABLES: 
PIPENV_VENV_IN_PROJECT=1

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

black:
	pipenv run black starlette_zipkin
sort:
	pipenv run isort starlette_zipkin
check-format:
	pipenv run black starlette_zipkin --check
check-lint:
	pipenv run flake8 starlette_zipkin 
check-sort:
	pipenv run isort starlette_zipkin --check-only --profile black
check-mypy:
	pipenv run mypy starlette_zipkin --ignore-missing-imports --follow-imports=skip --strict-optional

##@ Manage
install:  ## install venv from Pipfile
	pipenv install --dev --skip-lock
requirements:  ## creates requirements.txt from Pipfile
	pipenv run pip freeze > requirements.txt
check: check-sort check-format check-lint check-mypy ## perform checks
format: sort black check-lint  ## perform all formatings

##@ Run
run: ## run uvicorn app:app --reload
	pipenv run uvicorn app:app --reload
build: requirements  ## requirements & python setup.py sdist
	pipenv run python setup.py sdist
publish: build  ## build & twine upload dist/*
	pipenv run twine upload dist/*
tests: ## tests
	pipenv run python -m pytest

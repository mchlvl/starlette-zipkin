.PHONY: run requirements install requirements build publish
.EXPORT_ALL_VARIABLES: 
PIPENV_VENV_IN_PROJECT=1


run:
	pipenv run uvicorn app:app --reload

install:
	pipenv install --dev

requirements:
	pipenv run pip freeze > requirements.txt

build: requirements
	pipenv run python setup.py sdist

publish: build
	pipenv run twine upload dist/*

tests:
	pipenv run python -m pytest

.DEFAULT_GOAL := show-help

show-help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  run           run uvicorn app:app --reload"
	@echo "  install       install venv from Pipfile"
	@echo "  requirements  creates requirements.txt from venv"
	@echo "  build         requirements & python setup.py sdist"
	@echo "  publish       build & twine upload dist/*"

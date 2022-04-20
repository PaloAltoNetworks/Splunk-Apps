help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "bandit - run bandit security checks"
	@echo "format - format all python files"
	@echo "check-format - check the format of all python files"
	@echo "sync-deps - save dependencies to requirements.txt"
	@echo "deploy - deploy to Google Cloud Function"

clean: clean-pyc

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

bandit:
	bandit main.py

format:
	isort --atomic main.py
	black .

check-format:
	isort --atomic --check-only main.py
	black --check .

sync-deps:
	poetry export --without-hashes -f requirements.txt -o requirements.txt

deploy:
	gcloud functions deploy reset-demo \
	  --runtime python39 \
	  --memory 256MB \
	  --trigger-topic reset-demo \
	  --env-vars-file ./config.yml \
	  --entry-point reset_demo
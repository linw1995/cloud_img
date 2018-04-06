init:
	python -m pip install -U pip
	pip install pipenv
	pipenv install --dev --skip-lock
	pipenv run pip install -e .

isort:
	pipenv run isort -rc --atomic ./tests ./cloud_img

flake:
	pipenv run flake8 ./tests ./cloud_img

test: flake isort
	pipenv run py.test -q ./tests

vtest: flake isort
	pipenv run py.test -s -v ./tests

cov: flake isort
	@pipenv run py.test --cov=cloud_img -v --timeout 10
	@echo "building coverage html, view at './htmlcov/index.html'"
	@pipenv run coverage html

freeze:
	pipenv lock -r > ./requirements.txt
	pipenv lock -r -d > ./dev-requirements.txt

clean:
	@rm -rf htmlcov
	@rm -rf cloud_img.egg-info
	@rm -rf .pytest_cache
	@rm .coverage

start_test_env:
	docker-compose up -d mysql redis

stop_test_env:
	docker-compose stop

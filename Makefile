init:
	python -m pip install -U pip
	pip install pipenv
	pipenv install --dev
	pipenv run pip install -e .

isort:
	pipenv run isort -rc --atomic ./tests ./cloud_img

flake:
	pipenv run flake8 ./tests ./cloud_img

test:
	pipenv run py.test -q ./tests

vtest:
	pipenv run py.test -s -v ./tests

cov:
	@pipenv run py.test --cov=cloud_img
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

start_test_db:
	@echo "----------------------------------------------------"
	@echo "Starting mysql, see docker-compose.yml for user/pass"
	@echo "----------------------------------------------------"
	docker-compose -f docker-compose.yml up -d test_db

stop_test_db:
	docker-compose -f docker-compose.yml stop test_db

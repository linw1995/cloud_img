FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir pipenv
RUN pipenv install --skip-lock

RUN pipenv install -e . --skip-lock

RUN cp conf.docker-compose.yaml conf.yaml

ENTRYPOINT [ "pipenv", "run" ]

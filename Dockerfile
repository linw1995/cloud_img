FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir pipenv
RUN pipenv install --system --skip-lock

RUN pip install -e .

RUN cp conf.docker-compose.yaml conf.yaml
